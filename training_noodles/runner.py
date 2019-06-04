import ast
import json
import logging
import re
import time

from training_noodles.remote import (
    eval_expression_on_local, run_commands_over_ssh, get_error_message)
from training_noodles.utils import (
    match_full, split_by_scheme, update_dict_with_missing, wrap_with_list)


class Runner:
    def __init__(self, command_type, user_spec, verbose=False):
        # Save the command type
        self.command_type = command_type

        # Save the user spec
        self.user_spec = user_spec

        # Save the logging variables
        self.verbose = verbose

    def run(self):
        """ Deploy all the experiments until finish.
        """
        # Save the first timestamp
        start_time = time.time()

        # Deploy "before all" experiments
        self._deploy_side_experiments('before_all_experiments')

        # Deploy main experiments
        num_success, total = self._deploy_main_experiments()

        # Deploy "after all" experiments
        self._deploy_side_experiments('after_all_experiments')

        # Calculate total elapsed time
        elapsed = time.time() - start_time

        # Log the elapsed time
        logging.info('Total elapsed time: {:.3f}s'.format(elapsed))

        # Calculate ratio of successful deployments
        percentage = float(num_success) / float(total) * 100.0

        # Log the ratio of successful deployments
        logging.info(
            'Successfully deployed {:g}% ({}/{}) "{}" experiments'.format(
                percentage, num_success, total, self.command_type))

    def _deploy_main_experiments(self):
        # Initialize total number of successful deployments
        total_num_success = 0

        # Get number of experiments
        num_exps = self._count_experiments()

        # Initialize a set of indexes of undeployed experiments
        undeployed = set(range(num_exps))

        # Deploy all remaining experiments until there are none
        round_idx = 0
        prev_round_time = time.time()

        while len(undeployed) > 0:
            # Log the deployment round
            self._log_round(round_idx, undeployed)

            # Wait for next round
            if round_idx > 0:
                self._wait_for_next_round()

            # Create undeployed experiments
            undeployed_exps = self._filter_undeployed_experiments(undeployed)

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
        logging.info('Finished main stage "experiments"')

        # Return the ratio of successful deployments
        return total_num_success, num_exps

    def _deploy_side_experiments(self, stage):
        # Get the side experiment spec
        side_exp_spec = self._get_side_experiments_spec(stage)

        # Wrap the side experiment spec in list
        wrapped_spec = [side_exp_spec]

        # Initialize a set of indexes of undeployed experiments
        undeployed = set([0])

        # Initialize the deployed set
        deployed = set()

        # Deploy all remaining experiments until there are none
        round_idx = 0
        prev_round_time = time.time()

        while len(deployed) <= 0:
            # Log the deployment round
            self._log_side_round(stage, round_idx)

            # Wait for next round
            if round_idx > 0:
                self._wait_for_next_round()

            # Try to deploy each experiment to one of the satisfied servers
            deployed, num_success = self._deploy_experiment_specs(
                undeployed, wrapped_spec, main=False)

            # Log the round time
            self._log_round_time(prev_round_time)

            # Update previous round time
            prev_round_time = time.time()

            # Increment round index
            round_idx += 1

        # Log the finish
        logging.info('Finished side stage "{}"'.format(stage))

        # Return the ratio of successful deployments
        return num_success, 1

    def _deploy_experiment_specs(self, exp_idxs, exps_spec, main=True):
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

        # Get servers spec
        servers_spec = self.user_spec.get('servers', [])

        # Iterate each experiment spec
        for filtered_exp_idx, exp_spec in enumerate(exps_spec):
            # Get the experiment name
            exp_name = exp_spec.get('name', '')

            # Get the original experiment index
            exp_idx = exp_idxs[filtered_exp_idx]

            # Log the experiment
            self._log_verbose('Try to deploy experiment "{}"'.format(exp_name))

            # Check whether the experiment is empty
            if self._check_empty_experiment(exp_spec, main=main):
                # Log the skip
                self._log_verbose('Experiment "{}" is empty, skip'.format(
                    exp_name))

                # Add the experiment index to the deployed experiment indexes
                deployed_exps.add(exp_idx)

            else:
                # Update metrics lazily
                self._update_metrics(exp_spec, metrics, main=main)

                # Find satisfied servers
                satisfied_servers = self._find_satisfied_servers(
                    exp_spec, metrics, deployed_servers, main=main)

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
                    logging.info(
                        'Deploy experiment "{}" to server "{}"'.format(
                            exp_name, server_name))

                    # Deploy the experiment to the server
                    status = self._deploy_experiment_to_server(
                        exp_spec, server_spec, main=main)

                    # Update deployed indexes by status
                    self._update_deployed_indexes_by_status(
                        status, exp_idx, server_idx, deployed_exps,
                        deployed_servers)

                    # Increment the number of successful deployments
                    if status == 'success':
                        num_success += 1

                # Check whether there are no available servers in this
                # deployment
                if len(deployed_servers) >= len(servers_spec):
                    # Log the break
                    self._log_verbose(
                        'No available servers, skip the deployment')

                    break

        # Return the deployed experiment indexes and number of successful
        # deployments
        return deployed_exps, num_success

    def _deploy_experiment_to_server(self, exp_spec, server_spec, main=True):
        # Build experiment commands
        commands = self._build_experiment_details(
            exp_spec, 'commands', main=main)

        # Build experiment environment variables
        envs = self._build_experiment_details(
            exp_spec, 'envs', main=main)

        # Add environment variables of the satisfied server
        server_envs = self._build_server_envs(server_spec, envs)

        # Merge environment variables
        envs = {**envs, **server_envs}

        # Deploy the experiment to the server
        status, results = self._run_commands(
            server_spec, commands, envs=envs)

        # Log the results
        logging.info('Commands results->\n{}'.format(results))

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
            logging.warning('Unsuccessful commands run, will continue')

            # Give up this experiment by treating it as if it has been
            # deployed
            deployed_exps.add(exp_idx)

        elif status == 'retry':
            # Log the retry
            logging.warning('Unsuccessful commands run, will retry')

        else:
            # Should not reach here
            raise ValueError('Unknown status: {}'.format(status))

    def _check_server_metrics(self, req_id, envs):
        # Initialize the metric outputs
        metrics = []

        # Get requirements spec
        reqs_spec = self.user_spec.get('requirements', {})

        # Get server specs
        servers_spec = self.user_spec.get('servers', [])

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
                    self._log_and_raise_error(
                        'Requirement ID does not exist: {}'.format(req_id))

                # Run the remote command on server
                status, results = self._run_commands(
                    server_spec, req_commands, envs=envs)

                # Take action according to the status
                if status == 'success':
                    # Log the results
                    logging.debug('Metric results:->\n{}'.format(results))

                    # Try to calculate mean metric of results
                    metric = self._try_calc_mean(results)

                    # Log the processed metric
                    logging.debug('Processed metric: {}'.format(metric))

                    # Add the metric to the list
                    metrics.append(metric)

                elif status == 'continue':
                    # Log the continue
                    logging.warning('Unsuccessful commands run, will continue')

                    # Continue to next server spec
                    break

                elif status == 'retry':
                    # Log the retry
                    logging.warning('Unsuccessful commands run, will retry')

                else:
                    # Should not reach here
                    raise ValueError('Unknown status: {}'.format(status))

        # Return list of metrics for all servers
        return metrics

    def _run_commands(self, server_spec, commands, envs={}):
        # Run the commands on remote
        all_results, debug_infos = run_commands_over_ssh(
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
                self._log_and_raise_error(message)
            else:
                self._log_and_raise_error(
                    'Unknown error action "{}"'.format(action))

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

    def _count_experiments(self):
        # Get experiment specs
        exps_spec = self._get_experiments_spec()

        # Return the count
        return len(exps_spec)

    def _filter_undeployed_experiments(self, undeployed):
        # Initialize the list of undeployed experiments
        undeployed_exps = []

        # Get experiments
        exps_spec = self._get_experiments_spec()

        # Add each undeployed experiment to the list
        for exp_idx in undeployed:
            # Get the experiment spec
            exp_spec = exps_spec[exp_idx]

            # Add to the undeployed list
            undeployed_exps.append(exp_spec)

        # Return the undeployed experiments
        return undeployed_exps

    def _update_metrics(self, exp_spec, metrics, main=True):
        # Build experiment environment variables
        envs = self._build_experiment_details(exp_spec, 'envs', main=main)

        # Build experiment requirements
        reqs_spec = self._build_experiment_details(
            exp_spec, 'requirements', main=main)

        # Log the update
        self._log_verbose('Update metrics')

        # Iterate each requirement
        for req_id in reqs_spec.keys():
            # Check whether we should update the metric
            if self._should_update_metric(req_id, metrics):
                # Log the check
                self._log_verbose(('Check requirement ID: {}').format(req_id))

                # Check server metrics
                server_metrics = self._check_server_metrics(req_id, envs)

                # Update the metrics
                metrics[req_id] = server_metrics

    def _find_satisfied_servers(self, exp_spec, metrics, deployed, main=True):
        # Get servers spec
        servers_spec = self.user_spec.get('servers', [])

        # Initialize all indexes of servers
        satisfied = set(range(len(servers_spec)))

        # Build experiment requirements
        reqs_spec = self._build_experiment_details(
            exp_spec, 'requirements', main=main)

        # Log the find
        self._log_verbose('Find satisfied servers')

        # Iterate each requirement
        for req_id, req_expr in reqs_spec.items():
            # Parse the requirement expression
            operator, value = self._parse_requirement_expression(req_expr)

            # Log the requirement
            logging.debug(('Requirement ID: "{}", Operator: "{}",' +
                           ' Value: "{}"').format(req_id, operator, value))

            # Get the list of server metrics of the requirement
            servers_metrics = metrics.get(req_id, None)

            if servers_metrics is None:
                self._log_and_raise_error(
                    'Requirement ID "{}" should be in metrics'.format(req_id))

            # Update the indexes of satisfied servers by comparing the server
            # metric to the requirement value
            satisfied = filter(lambda i: self._is_metric_satisfied(
                servers_metrics[i], operator, value), satisfied)

        # Remove indexes of deployed servers
        satisfied = set(satisfied) - deployed

        # Log the satisfied servers
        if self.verbose:
            server_names = [servers_spec[i].get('name', '')
                            for i in satisfied]
            logging.info('Satisfied servers: {}'.format(
                json.dumps(server_names)))

        # Return indexes of satisfied servers
        return satisfied

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
            self._log_and_raise_error(
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
                self._log_and_raise_error(
                    'Unknown operator: {}'.format(operator))
        except:
            self._log_and_raise_error(
                'Could not compare the values: "{}" "{}" "{}"'.format(
                    metric, operator, value))

    def _parse_requirement_expression(self, req_expr):
        # Remove whitespaces
        req_expr = req_expr.strip()

        # Parse the expression
        m = re.match(r'^(?P<operator>[<>=]+)(?P<value>[\d.]+)$', req_expr)

        # Check whether the expression is valid
        if m is None:
            self._log_and_raise_error(
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
        results = results.split('\n')

        # Remove empty contents in results
        results = filter(lambda s: len(s.strip()) > 0, results)

        try:
            # Parse the results
            results = list(map(ast.literal_eval, results))

            # Calculate the mean
            result = sum(results) / len(results)
        except:
            pass

            # Use original results
            result = results

        return result

    def _build_experiment_details(self, exp_spec, detail_name, main=True):
        # Get details in the experiment
        exp_details = self._get_experiment_details(exp_spec, detail_name)

        # Check whether to merge specs from "before each", "each" and
        # "after each"
        if main:
            # Get "before each" experiment details
            before_each_exp_details = self._get_side_experiment_details(
                'before_each_experiment', detail_name)

            # Get "each" experiment details
            each_exp_details = self._get_side_experiment_details(
                'each_experiment', detail_name)

            # Get "after each" experiment details
            after_each_exp_details = self._get_side_experiment_details(
                'after_each_experiment', detail_name)

            # Check whether to use default details from "each" experiment
            # details
            if len(exp_details) <= 0 and len(each_exp_details) > 0:
                # Log the use
                self._log_verbose(('Use default "{}" from' +
                                   ' "each_experiment"->\n{}').format(
                    detail_name, json.dumps(each_exp_details)))

                # Use commands from "each" commands
                exp_details = each_exp_details

            # Log the merge
            if len(before_each_exp_details) > 0:
                self._log_verbose(('Merge "{}" from' +
                                   ' "before_each_experiment"->\n{}').format(
                    detail_name, json.dumps(before_each_exp_details)))

            if len(after_each_exp_details) > 0:
                self._log_verbose(('Merge "{}" from' +
                                   ' "after_each_experiment"->\n{}').format(
                    detail_name, json.dumps(after_each_exp_details)))

            # Merge with "before each" and "after each" commands then return
            return self._merge_experiment_details(
                before_each_exp_details, exp_details, after_each_exp_details)

        else:
            return exp_details

    def _merge_experiment_details(self, before_each_exp_details, exp_details,
                                  after_each_exp_details):
        if isinstance(exp_details, list):
            return (before_each_exp_details + exp_details +
                    after_each_exp_details)
        elif isinstance(exp_details, dict):
            return update_dict_with_missing(before_each_exp_details,
                                            exp_details, after_each_exp_details)
        else:
            self._log_and_raise_error(
                'Unknown type of experiment details: {}'.format(
                    type(exp_details)))

    def _get_side_experiments_spec(self, stage):
        # Return the side experiment
        return self.user_spec.get(stage, {})

    def _get_experiments_spec(self):
        # Return all experiments
        return self.user_spec.get('experiments', {})

    def _get_experiment_details(self, exp_spec, detail_name):
        # Get the details
        details = exp_spec.get(detail_name, {})

        # Get the corresponding details
        details = self._get_corresponding_details(detail_name, details)

        # Wrap the details and return
        return self._wrap_details(detail_name, details)

    def _get_side_experiment_details(self, stage, detail_name):
        # Get the spec
        stage_spec = self.user_spec.get(stage, {})

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
            return details.get(self.command_type, {})
        else:
            self._log_and_raise_error(
                'Unknown detail name: {}'.format(detail_name))

    def _wrap_details(self, detail_name, details):
        if detail_name == 'envs':
            # Return the dict
            return details
        elif detail_name == 'commands':
            # Wrap the details in list and return
            return wrap_with_list(details)
        elif detail_name == 'requirements':
            # Return the dict
            return details
        else:
            self._log_and_raise_error(
                'Unknown detail name: {}'.format(detail_name))

    def _check_empty_experiment(self, exp_spec, main=True):
        # Build the commands
        commands = self._build_experiment_details(
            exp_spec, 'commands', main=main)

        # Check whether the commands are empty
        return len(commands) <= 0

    def _log_side_round(self, stage, round_idx):
        self._log_verbose('Side round #{} ({})'.format(round_idx + 1, stage))

    def _log_round(self, round_idx, undeployed):
        if self.verbose:
            # Log the round number
            logging.info('Main round #{}'.format(round_idx + 1))

            # Log the undeployed experiments
            exps_spec = self._get_experiments_spec()
            undeployed_names = [exps_spec[i].get('name', '#{}'.format(i))
                                for i in undeployed]
            logging.info('Undeployed experiments: {}'.format(
                json.dumps(undeployed_names)))

    def _log_round_time(self, prev_round_time):
        if self.verbose:
            # Calculate round time
            elapsed_time = time.time() - prev_round_time

            # Log the elapsed time
            logging.info('Elapsed round time: {:.3f}s'.format(elapsed_time))

    def _log_requirement_ids(self, req_ids):
        logging.debug('Collected requirement IDs: {}'.format(
            json.dumps(req_ids)))

    def _log_metrics(self, metrics):
        logging.debug('Server metrics: {}'.format(json.dumps(metrics)))

    def _log_verbose(self, message):
        if self.verbose:
            logging.info(message)

    def _log_and_raise_error(self, message):
        logging.error(message)
        raise ValueError(message)
