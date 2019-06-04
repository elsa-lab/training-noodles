import ast
import json
import logging
import re
import time

from training_noodles.remote import (
    eval_expression_on_local, run_commands, get_error_message)
from training_noodles.utils import (
    match_full, split_by_scheme, update_dict_with_missing, wrap_with_list)


class Runner:
    def __init__(self, command_type, user_spec, verbose=False):
        # Save the command type
        self.command_type = command_type

        # Save the user spec
        self.user_spec = user_spec

        # Save the logging variable
        self.verbose = verbose

        # Create a logger
        self.logger = logging.getLogger(name='run')

    def run(self):
        """ Deploy all the experiments until finish.
        """
        # Save the first timestamp
        start_time = time.time()

        # Deploy "before all" experiments
        self._deploy_stage('before_all_experiments')

        # Deploy main experiments
        num_success, total = self._deploy_stage('experiments')

        # Deploy "after all" experiments
        self._deploy_stage('after_all_experiments')

        # Calculate total elapsed time
        elapsed = time.time() - start_time

        # Log the elapsed time
        self.logger.info('Total elapsed time: {:.3f}s'.format(elapsed))

        # Calculate ratio of successful deployments
        percentage = float(num_success) / float(total) * 100.0

        # Log the ratio of successful deployments
        self.logger.info(
            'Successfully deployed {:g}% ({}/{}) "{}" experiments'.format(
                percentage, num_success, total, self.command_type))

    def _deploy_stage(self, stage):
       # Initialize total number of successful deployments
        total_num_success = 0

        # Get number of experiments in the stage
        num_exps = self._count_experiments(stage)

        # Initialize a set of indexes of undeployed experiments
        undeployed = set(range(num_exps))

        # Log the start
        self.logger.info('Start stage "{}"'.format(stage))

        # Deploy all remaining experiments until there are none
        round_idx = 0
        prev_round_time = time.time()

        while len(undeployed) > 0:
            # Log the deployment round
            self._log_round(round_idx, stage, undeployed)

            # Wait for next round
            if round_idx > 0:
                self._wait_for_next_round()

            # Create undeployed experiments
            undeployed_exps = self._filter_undeployed_experiments(
                stage, undeployed)

            # Try to deploy each experiment to one of the satisfied servers
            deployed, num_success = self._deploy_experiment_specs(
                undeployed, undeployed_exps)

            # Remove deployed indexes
            undeployed -= deployed

            # Accumulate number of successful deployments
            total_num_success += num_success

            # Log the round time
            self._log_round_time(prev_round_time)

            # Update previous round time
            prev_round_time = time.time()

            # Increment round index
            round_idx += 1

        # Log the finish
        self.logger.info('Finished stage "{}"'.format(stage))

        # Return the ratio of successful deployments
        return total_num_success, num_exps

    def _deploy_experiment_specs(self, exp_idxs, exps_spec):
        # Initialize set of deployed experiment indexes
        deployed_exps = set()

        # Initialize set of deployed server indexes
        deployed_servers = set()

        # Initialize the number of successful deployments
        num_success = 0

        # Convert experiment indexes to list
        exp_idxs = list(exp_idxs)

        # Initialize the empty metrics
        metrics = {}

        # Get server specs
        servers_spec = self._get_server_specs()

        # Iterate each experiment spec
        for filtered_exp_idx, exp_spec in enumerate(exps_spec):
            # Get the experiment name
            exp_name = exp_spec.get('name', '')

            # Get the original experiment index
            exp_idx = exp_idxs[filtered_exp_idx]

            # Log the experiment
            self._log_verbose('Try to deploy experiment "{}"'.format(exp_name))

            # Check whether the experiment is empty
            if self._check_empty_experiment(exp_spec):
                # Log the skip
                self._log_verbose('Experiment "{}" is empty, skip'.format(
                    exp_name))

                # Add the experiment index to the deployed experiment indexes
                deployed_exps.add(exp_idx)

                # Continue to next experiment
                continue

            # Find satisfied servers and update metrics lazily
            satisfied_servers = self._update_metrics_and_find_servers(
                exp_spec, metrics, deployed_servers)

            # Check whether there are any satisfied servers
            if len(satisfied_servers) > 0:
                # Wait for next deployment
                if len(deployed_exps) > 0:
                    self._wait_for_next_deployment()

                # Choose the first satisfied server
                server_idx = next(iter(satisfied_servers))

                # Get server spec
                server_spec = servers_spec[server_idx]

                # Get the server name
                server_name = server_spec.get('name', '')

                # Log the deployment
                self.logger.info(
                    'Deploy experiment "{}" to server "{}"'.format(
                        exp_name, server_name))

                # Deploy the experiment to the server
                status = self._deploy_experiment_to_server(
                    exp_spec, server_spec)

                # Update deployed indexes by status
                self._update_deployed_indexes_by_status(
                    status, exp_idx, server_idx, deployed_exps,
                    deployed_servers)

                # Increment the number of successful deployments
                if status == 'success' or status == 'continue':
                    num_success += 1

            # Check whether there are no available servers in this
            # deployment
            if len(deployed_servers) >= len(servers_spec):
                # Log the break
                self._log_verbose('No available servers, skip the deployment')

                break

        # Return the deployed experiment indexes and number of successful
        # deployments
        return deployed_exps, num_success

    def _deploy_experiment_to_server(self, exp_spec, server_spec):
        # Build experiment commands
        commands = self._build_experiment_details(exp_spec, 'commands')

        # Build experiment environment variables
        envs = self._build_experiment_details(exp_spec, 'envs')

        # Add environment variables of the satisfied server
        server_envs = self._build_server_envs(server_spec, envs)

        # Merge environment variables
        envs = {**envs, **server_envs}

        # Deploy the experiment to the server
        status, results = self._run_commands(
            server_spec, commands, envs=envs)

        # Log the results
        self.logger.info('Commands results->\n{}'.format(results))

        # Return the status
        return status

    def _update_deployed_indexes_by_status(self, status, exp_idx, server_idx,
                                           deployed_exps, deployed_servers):
        # Take action according to the status
        if status == 'success':
            # Add the experiment index to the deployed experiment
            # indexes
            deployed_exps.add(exp_idx)

            # Add the deployed server index to the deployed server
            # indexes
            deployed_servers.add(server_idx)

        elif status == 'continue':
            # Log the continue
            self.logger.warning('Unsuccessful deployment, will continue')

            # Give up this experiment by treating it as if it has been
            # deployed
            deployed_exps.add(exp_idx)

        elif status == 'retry':
            # Log the retry
            self.logger.warning('Unsuccessful deployment, will retry')

        else:
            # Should not reach here
            raise ValueError('Unknown status: {}'.format(status))

    def _check_server_metrics(self, req_id, envs):
        # Initialize the metric outputs
        metrics = []

        # Get requirement specs
        reqs_spec = self._get_requirement_specs()

        # Get server specs
        servers_spec = self._get_server_specs()

        # Iterate each server spec
        for server_spec in servers_spec:
            # Run the command until success
            status = None

            while status != 'success':
                # Get name of the server
                name = server_spec['name']

                # Log the server and requirement ID
                self._log_verbose(('Check requirement "{}"' +
                                   ' on server "{}"').format(req_id, name))

                # Get the requirement commands
                req_commands = reqs_spec.get(req_id, None)

                # Check whether the requirement command exists
                if req_commands is None:
                    self._raise_error(
                        'Requirement ID does not exist: {}'.format(req_id))

                # Run the remote command on server
                status, results = self._run_commands(
                    server_spec, req_commands, envs=envs)

                # Take action according to the status
                if status == 'success':
                    # Log the results
                    self.logger.debug('Metric results:->\n{}'.format(results))

                    # Try to calculate mean metric of results
                    metric = self._try_calc_mean(results)

                    # Log the processed metric
                    self.logger.debug('Processed metric: {}'.format(metric))

                    # Add the metric to the list
                    metrics.append(metric)

                elif status == 'continue':
                    # Log the continue
                    self.logger.warning(
                        'Unsuccessful commands execution, will continue')

                    # Continue to next server spec
                    break

                elif status == 'retry':
                    # Log the retry
                    self.logger.warning(
                        'Unsuccessful commands execution, will retry')

                else:
                    # Should not reach here
                    raise ValueError('Unknown status: {}'.format(status))

        # Return list of metrics for all servers
        return metrics

    def _run_commands(self, server_spec, commands, envs={}):
        # Run the commands
        all_results, debug_infos = run_commands(
            server_spec, commands, envs=envs)

        # Check errors
        status = None
        for results, debug_info in zip(all_results, debug_infos):
            status = self._handle_errors(results, debug_info)

            # Break when it has error status
            if status != 'success':
                break

        # Get STDOUTs produced by inner commands
        inner_stdouts = map(lambda x: x['inner_stdout'], all_results)

        # Concatenate the STDOUTs
        inner_stdout = ''.join(inner_stdouts)

        # Return the error status and STDOUT
        return status, inner_stdout

    def _handle_errors(self, results, debug_info):
        # Get error handling spec
        check_any_errors = self.user_spec.get('check_any_errors', True)

        # Determine whether to check any errors
        if check_any_errors:
            # Get error message
            message = get_error_message(results, debug_info)
        else:
            # Set empty error message
            message = ''

        # Check whether there is any error message
        if len(message) > 0:
            # Get error handling action
            action = self._check_error_handler_action(results)

            # Take action
            if action == 'continue':
                self._log_verbose(message)
            elif action == 'retry':
                self._log_verbose(message)
            elif action == 'abort':
                self._raise_error(message)
            else:
                self._raise_error('Unknown error action "{}"'.format(action))

            # Return error handling action
            return action
        else:
            # Indicate no action should be taken
            return 'success'

    def _check_error_handler_action(self, results):
        # Get error handler specs
        error_handlers = self.user_spec.get('error_handlers', [])

        # Iterate each error handler
        for error_handler in error_handlers:
            # Get return code to ignore
            return_code = error_handler.get('return_code', None)

            # Get STDERR pattern to ignore
            stderr_pattern = error_handler.get('stderr_pattern', None)

            # Check the return code
            if isinstance(return_code, str):
                match_return_code = match_full(
                    return_code, results['return_code'])
            else:
                match_return_code = (results['return_code'] == return_code)

            # Check whether it's a full match
            match_stderr = match_full(stderr_pattern, results['inner_stderr'])

            # Return code and STDERR must all be matched
            if match_return_code and match_stderr:
                # Get the name of the filter
                name = error_handler.get('name', '')

                # Get the action
                action = error_handler.get('action', 'abort')

                # Log the match
                self._log_verbose(('Found error handler match with name "{}"' +
                                   ' and action "{}"').format(name, action))

                # Return the action
                return action

        # All filters do not apply, abort the runner
        return 'abort'

    def _count_experiments(self, stage):
        # Get experiment specs
        exps_spec = self._get_experiment_specs(stage)

        # Return the count
        return len(exps_spec)

    def _filter_undeployed_experiments(self, stage, undeployed):
        # Initialize the list of undeployed experiments
        undeployed_exps = []

        # Get experiments
        exps_spec = self._get_experiment_specs(stage)

        # Add each undeployed experiment to the list
        for exp_idx in undeployed:
            # Get the experiment spec
            exp_spec = exps_spec[exp_idx]

            # Add to the undeployed list
            undeployed_exps.append(exp_spec)

        # Return the undeployed experiments
        return undeployed_exps

    def _update_metrics_and_find_servers(self, exp_spec, metrics, deployed):
        # Get server specs
        servers_spec = self._get_server_specs()

        # Initialize all indexes of servers
        satisfied = set(range(len(servers_spec)))

        # Build experiment requirements
        reqs_spec = self._build_experiment_details(exp_spec, 'requirements')

        # Build experiment environment variables
        envs = self._build_experiment_details(exp_spec, 'envs')

        # Log the search
        self._log_verbose('Find satisfied servers')

        # Iterate each requirement group
        for group_idx, req_group in enumerate(reqs_spec):
            # Stop the search when there are no any satisfied servers left
            if len(satisfied) <= 0:
                break

            # Log the group index
            self._log_verbose('Check requirement group #{}'.format(
                group_idx + 1))

            # Update metrics lazily
            self._update_metrics(metrics, req_group, envs)

            # Filter indexes of satisfied servers based on cached metrics
            satisfied = self._filter_satisfied_servers(
                satisfied, req_group, metrics)

        # Remove indexes of deployed servers
        satisfied = set(satisfied) - deployed

        # Log the satisfied servers
        if self.verbose:
            server_names = [servers_spec[i].get('name', '')
                            for i in satisfied]
            self.logger.info('Satisfied servers: {}'.format(
                json.dumps(server_names)))

        # Return indexes of satisfied servers
        return satisfied

    def _update_metrics(self, metrics, req_group, envs):
        # Iterate each requirement ID
        for req_id in req_group.keys():
            # Check whether we should update the metric
            if self._should_update_metric(req_id, metrics):
                # Log the check
                self._log_verbose(('Check requirement ID: {}').format(req_id))

                # Check server metrics
                server_metrics = self._check_server_metrics(req_id, envs)

                # Update the metrics
                metrics[req_id] = server_metrics

    def _filter_satisfied_servers(self, satisfied, req_group, metrics):
        # Iterate each requirement
        for req_id, req_expr in req_group.items():
            # Stop the search when there are no any satisfied servers left
            if len(satisfied) <= 0:
                break

            # Parse the requirement expression
            operator, value = self._parse_requirement_expression(req_expr)

            # Log the requirement
            self.logger.debug(('Requirement ID: "{}", Operator: "{}",' +
                               ' Value: "{}"').format(
                req_id, operator, value))

            # Get the list of server metrics of the requirement
            servers_metrics = metrics.get(req_id, None)

            if servers_metrics is None:
                self._raise_error(('Requirement ID "{}" should' +
                                   ' be in metrics').format(req_id))

            # Update the indexes of satisfied servers by comparing the
            # server metric to the requirement value
            satisfied = filter(lambda i: self._is_metric_satisfied(
                servers_metrics[i], operator, value), satisfied)

        # Return the filtered indexes
        return set(satisfied)

    def _build_server_envs(self, server_spec, envs):
        # Build environment variables
        server_envs = {
            'NOODLES_SERVER_NAME': server_spec.get('name', ''),
            'NOODLES_SERVER_PRIVATE_KEY_PATH':
                server_spec.get('private_key_path', ''),
            'NOODLES_SERVER_PORT': server_spec.get('port', ''),
            'NOODLES_SERVER_USERNAME': server_spec.get('username', ''),
            'NOODLES_SERVER_HOSTNAME': server_spec.get('hostname', ''),
            'NOODLES_SERVER_AUTHORITY':
                self._build_server_authority(server_spec),
        }

        # Evaluate values in environment variables
        for key, expr in server_envs.items():
            # Convert to string
            expr = str(expr)

            # Skip the evaluation when the expression is empty
            if expr == '':
                continue

            # Check whether any environment variables exist
            m = re.match(r'(\$.+)|(\${.+})', expr)

            if m is None:
                continue

            # Evaluate express until success
            status = None

            while status != 'success':
                # Evaluate expression on local
                results, debug_info = eval_expression_on_local(
                    expr, envs=envs)

                # Handle errors
                status = self._handle_errors(results, debug_info)

                # Take action according to the status
                if status == 'success':
                    # Set evaluated values
                    server_envs[key] = results['inner_stdout']

                elif status == 'continue':
                    # Give up this evaluation
                    break

                elif status == 'retry':
                    pass

                else:
                    # Should not reach here
                    raise ValueError('Unknown status: {}'.format(status))

        # Return evaluated environment variables
        return server_envs

    def _build_server_authority(self, server_spec):
        # Get username
        username = server_spec.get('username', None)

        # Get hostname
        hostname = server_spec.get('hostname', '')

        # Check whether to include username
        if username is None:
            return '{}'.format(hostname)
        else:
            return '{}@{}'.format(username, hostname)

    def _wait_for_next_round(self):
        # Get round interval
        round_interval = self.user_spec.get('round_interval', 0)

        # Log the wait
        self._log_verbose('Wait for next round for {}s'.format(
            round_interval))

        # Wait for some time
        time.sleep(round_interval)

    def _wait_for_next_deployment(self):
        # Get deployment interval
        deployment_interval = self.user_spec.get('deployment_interval', 0)

        # Log the wait
        self._log_verbose('Wait for next deployment for {}s'.format(
            deployment_interval))

        # Wait for some time
        time.sleep(deployment_interval)

    def _should_update_metric(self, req_id, metrics):
        # Check whether the requirement ID contains any scheme (e.g.,
        # "static:cpu_usage", "dynamic:cpu_usage")
        schemes = ['static', 'dynamic']
        success, scheme, req_id = split_by_scheme(req_id, schemes)

        # Check whether there is unknown scheme
        if success:
            # Set default scheme to "dynamic"
            scheme = scheme or 'dynamic'

            # Log the scheme
            self._log_verbose('Requirement ID "{}" has scheme: {}'.format(
                req_id, scheme))

            # Check whether to update metric
            if scheme == 'dynamic':
                # Log the result
                self._log_verbose(
                    'Requirement ID "{}" should be checked'.format(req_id))

                return True
            elif scheme == 'static':
                # Check whether the requirement ID has existed in metrics
                if req_id in metrics:
                    # Log the result
                    self._log_verbose(
                        'Requirement ID "{}" is not in metrics'.format(req_id))

                    return False
                else:
                    # Log the result
                    self._log_verbose(
                        'Requirement ID "{}" is already in metrics'.format(
                            req_id))

                    return True
            else:
                # Should not reach here
                raise ValueError('Unknown scheme "{}"'.format(scheme))
        else:
            self._raise_error(
                'Unknown scheme "{}" in requirement ID "{}"'.format(
                    scheme, req_id))

    def _is_metric_satisfied(self, metric, operator, value):
        try:
            if operator == '==':
                return metric == value
            elif operator == '!=':
                return metric != value
            elif operator == '<':
                return metric < value
            elif operator == '>':
                return metric > value
            elif operator == '<=':
                return metric <= value
            elif operator == '>=':
                return metric >= value
            else:
                self._raise_error('Unknown operator: {}'.format(operator))
        except:
            self._raise_error(
                'Could not compare the values: "{}" "{}" "{}"'.format(
                    metric, operator, value))

    def _parse_requirement_expression(self, req_expr):
        # Remove whitespaces
        req_expr = req_expr.strip()

        # Parse the expression
        m = re.match(r'^(?P<operator>[<>=]+)(?P<value>.+)$', req_expr)

        # Check whether the expression is valid
        if m is None:
            self._raise_error(
                'Could not parse the requirement expression: {}'.format(
                    req_expr))
        else:
            operator = m.group('operator')
            value = m.group('value')

            # Try to parse the value
            try:
                value = ast.literal_eval(value)
            except:
                pass

        # Return operator and value
        return operator, value

    def _try_calc_mean(self, results):
        # Split the results by newlines
        lines = results.split('\n')

        # Remove empty contents in results
        lines = filter(lambda s: len(s.strip()) > 0, lines)

        try:
            # Parse the results
            parsed_lines = list(map(ast.literal_eval, lines))

            # Calculate the mean
            result = sum(parsed_lines) / len(parsed_lines)
        except:
            # Use original results
            result = results

        return result

    def _build_experiment_details(self, exp_spec, detail_name):
        # Get details in the experiment
        exp_details = self._get_experiment_details(exp_spec, detail_name)

        # Get "each" experiment details
        each_exp_details = self._get_stage_experiment_details(
            'experiment_default', detail_name)

        # Check whether to use default details from "each" experiment
        # details
        if len(exp_details) <= 0 and len(each_exp_details) > 0:
            # Log the use
            self._log_verbose(('Use default "{}" from' +
                               ' "experiment_default"->\n{}').format(
                detail_name, json.dumps(each_exp_details)))

            # Use commands from "each" commands
            exp_details = each_exp_details

        # Return the the experiment details
        return exp_details

    def _get_experiment_details(self, exp_spec, detail_name):
        # Get the details
        details = exp_spec.get(detail_name, {})

        # Get the corresponding details
        details = self._get_corresponding_details(detail_name, details)

        # Wrap the details and return
        return self._wrap_details(detail_name, details)

    def _get_stage_experiment_details(self, stage, detail_name):
        # Get the spec
        stage_spec = self._get_experiment_specs(stage)

        # Get the details
        details = stage_spec.get(detail_name, {})

        # Get the corresponding details
        details = self._get_corresponding_details(detail_name, details)

        # Wrap the details and return
        return self._wrap_details(detail_name, details)

    def _get_corresponding_details(self, detail_name, details):
        if detail_name == 'envs':
            # Return the original details
            return details
        elif detail_name == 'commands':
            # Return the corresponding type
            return details.get(self.command_type, [])
        elif detail_name == 'requirements':
            # Return the corresponding type
            return details.get(self.command_type, [])
        else:
            self._raise_error('Unknown detail name: {}'.format(detail_name))

    def _wrap_details(self, detail_name, details):
        if detail_name == 'envs':
            # Return the dict
            return details
        elif detail_name == 'commands':
            # Wrap the details in list and return
            return wrap_with_list(details)
        elif detail_name == 'requirements':
            # Return the dict
            return wrap_with_list(details)
        else:
            self._raise_error('Unknown detail name: {}'.format(detail_name))

    def _check_empty_experiment(self, exp_spec):
        # Build the commands
        commands = self._build_experiment_details(exp_spec, 'commands')

        # Check whether the commands are empty
        return len(commands) <= 0

    def _get_experiment_specs(self, stage):
        # Check whether the stage is in allowed list
        allowed_stages = ['before_all_experiments', 'experiment_default',
                          'experiments', 'after_all_experiments']

        if stage not in allowed_stages:
            self._raise_error('Unexpected stage: {}'.format(stage))

        return self.user_spec.get(stage, {})

    def _get_server_specs(self):
        return self.user_spec.get('servers', [])

    def _get_requirement_specs(self):
        return self.user_spec.get('requirements', {})

    def _log_round(self, round_idx, stage, undeployed):
        if self.verbose:
            # Log the round number
            self.logger.info('Round #{}'.format(round_idx + 1))

            # Log the undeployed experiments
            exps_spec = self._get_experiment_specs(stage)
            undeployed_names = [exps_spec[i].get('name', '#{}'.format(i))
                                for i in undeployed]
            self.logger.info('Undeployed experiments: {}'.format(
                json.dumps(undeployed_names)))

    def _log_round_time(self, prev_round_time):
        if self.verbose:
            # Calculate round time
            elapsed_time = time.time() - prev_round_time

            # Log the elapsed time
            self.logger.info(
                'Elapsed round time: {:.3f}s'.format(elapsed_time))

    def _log_requirement_ids(self, req_ids):
        self.logger.debug('Collected requirement IDs: {}'.format(
            json.dumps(req_ids)))

    def _log_metrics(self, metrics):
        self.logger.debug('Server metrics: {}'.format(json.dumps(metrics)))

    def _log_verbose(self, message):
        if self.verbose:
            self.logger.info(message)

    def _raise_error(self, message):
        self.logger.error(message)
        raise ValueError(message)
