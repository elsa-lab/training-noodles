import ast
import json
import logging
import re
import time
import yaml

from training_noodles.remote import (
    evaluate_expression_on_local, run_commands, get_error_messages)
from training_noodles.utils import (
    convert_unix_time_to_iso, match_full, split_by_scheme,
    update_dict_with_missing, wrap_with_list)


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

        # Initialize other attributes
        self.start_time = None
        self.stage = None
        self.undeployed = None
        self.round_idx = None
        self.prev_round_time = None

    ############################################################################
    # Deployment
    ############################################################################

    def run(self):
        """ Deploy all the experiments until finish.
        """
        # Save the first timestamp
        self.start_time = time.time()

        # Deploy "before all" experiments
        self._deploy_stage('before_all_experiments')

        # Deploy main experiments
        num_success, total = self._deploy_stage('experiments')

        # Deploy "after all" experiments
        self._deploy_stage('after_all_experiments')

        # Calculate total elapsed time
        elapsed = time.time() - self.start_time

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

        # Save the current stage
        self.stage = stage

        # Get number of experiments in the stage
        num_exps = self._count_experiments(self.stage)

        # Initialize a set of indexes of undeployed experiments
        self.undeployed = set(range(num_exps))

        # Log the start
        self.logger.info('Start stage "{}"'.format(self.stage))

        # Deploy all remaining experiments until there are none
        self.round_idx = 0
        self.prev_round_time = time.time()

        # Write the initial deployment status
        self._write_deployment_status()

        while len(self.undeployed) > 0:
            # Log the deployment round
            self._log_round()

            # Wait for next round
            if self.round_idx > 0:
                self._wait_for_next_round()

            # Create undeployed experiments
            filtered_exps = self._filter_undeployed_experiments(
                stage, self.undeployed)

            # Try to deploy each experiment to one of the satisfied servers
            filtered_deployed, num_success = self._deploy_experiment_specs(
                filtered_exps)

            # Restore unfiltered indexes
            deployed = self._restore_unfiltered_indexes(
                self.undeployed, filtered_deployed)

            # Remove deployed indexes
            self.undeployed -= deployed

            # Accumulate number of successful deployments
            total_num_success += num_success

            # Log the round time
            self._log_round_time()

            # Update previous round time
            self.prev_round_time = time.time()

            # Increment round index
            self.round_idx += 1

        # Log the finish
        self.logger.info('Finished stage "{}"'.format(stage))

        # Return the ratio of successful deployments
        return total_num_success, num_exps

    def _write_deployment_status(self, filtered_deployed=set()):
        # Check whether it's the main stage
        if self.stage != 'experiments':
            return

        # Get the output path
        write_path = self._get_write_status_to_spec()

        # Check whether to write
        if write_path is None:
            return

        # Calculate elapsed time
        elapsed_time = time.time() - self.start_time

        # Get default experiment spec
        default_exp_spec = self._get_default_experiment_spec()

        # Get default experiment environment variables
        envs = self._get_experiment_details(default_exp_spec, 'envs')

        # Evaluate the path
        write_path = self._evaluate_expression(write_path, envs=envs)

        # Get the experiments in the stage
        exps_spec = self._get_experiment_specs('experiments')

        # Get all experiment names
        exp_names = self._get_experiment_names(exps_spec)

        # Restore current deployed experiment indexes
        cur_deployed = self._restore_unfiltered_indexes(
            self.undeployed, filtered_deployed)

        # Build current undeployed experiment indexes
        cur_undeployed = self.undeployed - cur_deployed

        # Build undeployed experiment names
        undeployed_names = list(map(lambda i: exp_names[i], cur_undeployed))

        # Build deployed experiment names
        deployed_names = set(exp_names) - set(undeployed_names)

        # Convert the sets to lists
        deployed_names = list(deployed_names)

        # Build the status
        status = {
            'Start Time': convert_unix_time_to_iso(self.start_time),
            'Previous Round Time':
                convert_unix_time_to_iso(self.prev_round_time),
            'Elapsed time (s)': elapsed_time,
            'Stage': self.stage,
            'Round #': self.round_idx + 1,
            'Deployed Experiments': deployed_names,
            'Undeployed Experiments': undeployed_names,
            'Undeployed Experiments (For command)': ','.join(undeployed_names),
        }

        # Serialize the status into YAML string
        status = yaml.dump(status)

        # Write the status
        self._write_to_file(status, write_path)

    def _deploy_experiment_specs(self, exps_spec):
        # Initialize set of deployed experiment indexes
        deployed_exps = set()

        # Initialize set of deployed server indexes
        deployed_servers = set()

        # Initialize the number of successful deployments
        num_success = 0

        # Get experiment names
        exp_names = self._get_experiment_names(exps_spec)

        # Get server specs
        servers_spec = self._get_server_specs()

        # Initialize the empty metrics
        metrics = {}

        # Iterate each experiment spec
        for exp_idx, exp_spec in enumerate(exps_spec):
            # Get the experiment name
            exp_name = exp_spec.get('name', '')

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

            # Get the undeployed experiment dependencies
            undeployed_deps = self._get_undeployed_experiment_dependencies(
                exp_names, exp_spec, deployed_exps)

            # Check whether there are still some undeployed dependencies
            if len(undeployed_deps) > 0:
                # Log the skip
                self._log_verbose(('Experiment "{}" depends on experiments' +
                                   ' which are still undeployed: {}').format(
                                       exp_name, json.dumps(undeployed_deps)))

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

                # Log the deployment
                self._log_deployment_to_server(exp_name, server_spec)

                # Build the environment variables
                envs = self._build_experiment_envs(exp_spec, server_spec)

                # Deploy the experiment to the server
                status, stdout, stderr = self._deploy_experiment_to_server(
                    exp_spec, server_spec, envs)

                # Log outputs to terminal
                self._log_experiment_outputs(
                    exp_spec, status, stdout, stderr, envs)

                # Update deployed indexes by status
                self._update_deployed_indexes_by_status(
                    status, deployed_exps, deployed_servers, exp_idx,
                    server_idx, exp_name)

                # Check whether the deployment is successful
                if status == 'success' or status == 'continue':
                    # Write the deployment status
                    self._write_deployment_status(
                        filtered_deployed=deployed_exps)

                    # Increment the number of successful deployments
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

    def _deploy_experiment_to_server(self, exp_spec, server_spec, envs):
        # Get experiment commands
        commands = self._get_experiment_details(exp_spec, 'commands')

        # Build the user files
        user_files = self._build_user_files(exp_spec, envs)

        # Deploy the experiment to the server
        status, stdout, stderr = self._run_commands(
            server_spec, commands, user_files=user_files, envs=envs)

        # Return the status and outputs
        return status, stdout, stderr

    def _build_user_files(self, exp_spec, envs):
        # Initialize the user files
        user_files = {}

        # Set the output streams
        streams = ['stdout', 'stderr']

        # Get experiment outputs
        write_outputs = self._get_experiment_details(exp_spec, 'write_outputs')

        # Iterate each stream
        for stream in streams:
            # Set the spec key
            spec_key = '{}_to'.format(stream)

            # Get the path from the spec
            path = write_outputs.get(spec_key, None)

            # Check whether to add the path to the outputs
            if path is not None:
                # Evaluate the path
                evaluated_path = self._evaluate_expression(path, envs=envs)

                # Save the evaluated path
                user_files[stream] = evaluated_path

        # Return the user files
        return user_files

    def _log_experiment_outputs(
            self, exp_spec, status, stdout, stderr, envs):
        # Get experiment outputs
        write_outputs = self._get_experiment_details(exp_spec, 'write_outputs')

        # Get STDOUT and STDERR output paths
        stdout_path = write_outputs.get('stdout_to', None)
        stderr_path = write_outputs.get('stderr_to', None)

        # Check whether to write the STDOUT to the file
        if stdout_path is None:
            self.logger.info(
                'Commands output from STDOUT->\n{}'.format(stdout))
        else:
            # Log the write
            self.logger.info(
                'STDOUT output is written to "{}"'.format(stdout_path))

        # Check whether to write STDERR to the file
        if stderr_path is None:
            if len(stderr) > 0:
                self.logger.warning(
                    'Commands output from STDERR->\n{}'.format(stderr))
        else:
            # Log the write
            self.logger.info(
                'STDERR output is written to "{}"'.format(stderr_path))

    def _update_deployed_indexes_by_status(
            self, status, deployed_exps, deployed_servers, exp_idx, server_idx,
            exp_name):
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
            self.logger.warning(('Unsuccessful deployment of experiment' +
                                 ' "{}", will continue').format(exp_name))

            # Give up this experiment by treating it as if it has been
            # deployed
            deployed_exps.add(exp_idx)

        elif status == 'retry':
            # Log the retry
            self.logger.warning(('Unsuccessful deployment of experiment' +
                                 ' "{}", will retry').format(exp_name))

        else:
            # Should not reach here
            raise ValueError('Unknown status: {}'.format(status))

    ############################################################################
    # Stage Deployment Management
    ############################################################################

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

    def _restore_unfiltered_indexes(self, undeployed, filtered_deployed):
        # Convert the set of undeployed indexes to list
        undeployed = list(undeployed)

        # Map the filtered deployed indexes to original undeployed indexes
        return set(map(lambda i: undeployed[i], filtered_deployed))

    ############################################################################
    # Experiment Deployment Management
    ############################################################################

    def _get_undeployed_experiment_dependencies(self, exp_names, exp_spec,
                                                deployed):
        # Get experiment dependencies
        depends_on = self._get_experiment_details(exp_spec, 'depends_on')

        # Convert the dependencies to set
        depends_on = set(depends_on)

        # Build a set of deployed experiment names
        deployed_names = set(map(lambda i: exp_names[i], deployed))

        # Calculate undeployed experiment names
        undeployed_names = set(exp_names) - deployed_names

        # Calculate the intersection of dependencies and undeployed names
        undeployed_deps = depends_on.intersection(undeployed_names)

        # Return the undeployed dependency names
        return list(undeployed_deps)

    def _update_metrics_and_find_servers(self, exp_spec, metrics, deployed):
        # Get server specs
        servers_spec = self._get_server_specs()

        # Initialize all indexes of servers
        satisfied = set(range(len(servers_spec)))

        # Get experiment environment variables
        envs = self._get_experiment_details(exp_spec, 'envs')

        # Get experiment requirements
        reqs_spec = self._get_experiment_details(exp_spec, 'requirements')

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
            self._update_metrics(metrics, req_group, deployed, envs)

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

    def _update_metrics(self, metrics, req_group, deployed, envs):
        # Iterate each requirement ID
        for req_id in req_group.keys():
            # Check whether we should update the metric
            if self._should_update_metric(req_id, metrics):
                # Log the check
                self._log_verbose(('Check requirement ID: {}').format(req_id))

                # Check server metrics
                server_metrics = self._check_server_metrics(
                    req_id, deployed, envs)

                # Update the metrics
                metrics[req_id] = server_metrics

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

    def _check_server_metrics(self, req_id, deployed, envs):
        # Initialize the metric outputs
        metrics = []

        # Get requirement specs
        reqs_spec = self._get_requirement_specs()

        # Get server specs
        servers_spec = self._get_server_specs()

        # Iterate each server spec
        for server_idx, server_spec in enumerate(servers_spec):
            # Check whether the server has been deployed
            if server_idx in deployed:
                # Append null metric to the list
                metrics.append(None)

                # Continue to next server
                continue

            # Run the command until success
            status = None

            while status != 'success':
                # Get name of the server
                server_name = server_spec['name']

                # Log the server and requirement ID
                self._log_verbose(
                    'Check requirement "{}" on server "{}"'.format(
                        req_id, server_name))

                # Get the requirement commands
                req_commands = reqs_spec.get(req_id, None)

                # Check whether the requirement command exists
                if req_commands is None:
                    self._raise_error(
                        'Requirement ID does not exist: {}'.format(req_id))

                # Run the remote command on server
                status, stdout, _ = self._run_commands(
                    server_spec, req_commands, envs=envs)

                # Take action according to the status
                if status == 'success':
                    # Log the results
                    self.logger.debug('Metric results:->\n{}'.format(stdout))

                    # Try to calculate mean metric of results
                    metric = self._try_calc_mean(stdout)

                    # Log the processed metric
                    self.logger.debug('Processed metric->\n{}'.format(metric))

                    # Add the metric to the list
                    metrics.append(metric)

                elif status == 'continue':
                    # Log the continue
                    self.logger.warning(
                        ('Unsuccessful commands execution on server "{}",' +
                         ' will continue->\n{}').format(
                            server_name, req_commands))

                    # Continue to next server spec
                    break

                elif status == 'retry':
                    # Log the retry
                    self.logger.warning(
                        ('Unsuccessful commands execution on server "{}",' +
                         ' will retry->\n{}').format(
                            server_name, req_commands))

                else:
                    # Should not reach here
                    raise ValueError('Unknown status: {}'.format(status))

        # Return list of metrics for all servers
        return metrics

    ############################################################################
    # Metric Checking
    ############################################################################

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
            self.logger.exception(
                'Could not compare the values: "{}" "{}" "{}"'.format(
                    metric, operator, value))
            raise

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
                # Ignore the exception
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

    ############################################################################
    # Extra Environment Variables Provided by Noodles
    ############################################################################

    def _build_experiment_envs(self, exp_spec, server_spec):
        # Get experiment environment variables
        envs = self._get_experiment_details(exp_spec, 'envs')

        # Add environment variables of the satisfied server
        server_envs = self._build_extra_envs(exp_spec, server_spec, envs)

        # Merge environment variables and return
        return {**envs, **server_envs}

    def _build_extra_envs(self, exp_spec, server_spec, envs):
        # Build extra environment variables
        extra_envs = {
            # Experiment
            'NOODLES_EXPERIMENT_NAME': exp_spec.get('name', ''),
            # Server
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
        for key, expr in extra_envs.items():
            # Set evaluated values
            extra_envs[key] = self._evaluate_expression(expr, envs=envs)

        # Return evaluated environment variables
        return extra_envs

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

    ############################################################################
    # Command Execution
    ############################################################################

    def _run_commands(self, server_spec, commands, user_files={}, envs={}):
        # Run the commands
        all_results, debug_infos = run_commands(
            server_spec, commands, user_files=user_files, envs=envs)

        # Check errors from all results
        status = None
        for results, debug_info in zip(all_results, debug_infos):
            status = self._handle_errors(results, debug_info)

        # Combine STDOUTs produced by inner commands
        combined_stdout = self._combine_outputs(all_results, 'stdout')

        # Combine STDERRs produced by inner commands
        combined_stderr = self._combine_outputs(all_results, 'stderr')

        # Return the error status, combined STDOUT and combined STDERR
        return status, combined_stdout, combined_stderr

    def _handle_errors(self, results, debug_info):
        # Get error handling spec
        check_any_errors = self._get_check_any_errors_spec()

        # Determine whether to check any errors
        if check_any_errors:
            # Get error messages
            messages = get_error_messages(results, debug_info)
        else:
            # Set empty error messages
            messages = []

        # Check whether there are any error messages
        if len(messages) > 0:
            # Get error handling action
            action = self._check_error_handler_action(results)

            # Take action
            if action == 'continue':
                self._log_verbose(messages)
            elif action == 'retry':
                self._log_verbose(messages)
            elif action == 'abort':
                self._raise_error(messages)
            else:
                self._raise_error('Unknown error action "{}"'.format(action))

            # Return error handling action
            return action
        else:
            # Indicate no action should be taken
            return 'success'

    def _check_error_handler_action(self, results):
        # Get error handler specs
        error_handlers = self._get_error_handler_specs()

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
            match_stderr = match_full(stderr_pattern, results['stderr'])

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

    def _combine_outputs(self, all_results, output_type):
        # Get outputs
        outputs = map(lambda x: x[output_type], all_results)

        # Concatenate the outputs and return
        return ''.join(outputs)

    def _evaluate_expression(self, expr, envs={}):
        # Convert to string
        expr = str(expr)

        # Check whether any environment variables exist
        m = re.match(r'(\$.+)|(\${.+})', expr)

        # Return the original expression
        if m is None:
            return expr

        # Evaluate expression until success
        status = None

        while status != 'success':
            # Evaluate expression on local
            results, debug_info = evaluate_expression_on_local(expr, envs=envs)

            # Handle errors
            status = self._handle_errors(results, debug_info)

            # Take action according to the status
            if status == 'success':
                # Return evaluated values
                return results['stdout']

            elif status == 'continue':
                # Log the continue
                self.logger.warning(
                    ('Unsuccessful expression evaluation, will' +
                        ' continue->\n{}').format(expr))

                # Give up this evaluation
                break

            elif status == 'retry':
                # Log the retry
                self.logger.warning(
                    ('Unsuccessful expression evaluation, will' +
                        ' retry->\n{}').format(expr))

            else:
                # Should not reach here
                raise ValueError('Unknown status: {}'.format(status))

        # Return the original expression
        return expr

    ############################################################################
    # Experiment Spec Processing
    ############################################################################

    def _get_experiment_details(self, exp_spec, detail_name):
        # Get the details
        details = exp_spec.get(detail_name, {})

        # Get the corresponding details
        details = self._get_corresponding_details(detail_name, details)

        # Wrap the details and return
        return self._wrap_details(detail_name, details)

    def _get_default_details(self, detail_name):
        if detail_name == 'envs':
            return {}
        elif detail_name == 'depends_on':
            return {}
        elif detail_name == 'requirements':
            return {}
        elif detail_name == 'commands':
            return {}
        elif detail_name == 'write_outputs':
            return {}
        else:
            self._raise_error('Unknown detail name: {}'.format(detail_name))

    def _get_corresponding_details(self, detail_name, details):
        if detail_name == 'envs':
            # Return the original details
            return details
        elif detail_name == 'depends_on':
            # Return the original details
            return details.get(self.command_type, [])
        elif detail_name == 'requirements':
            # Return the corresponding type
            return details.get(self.command_type, [])
        elif detail_name == 'commands':
            # Return the corresponding type
            return details.get(self.command_type, [])
        elif detail_name == 'write_outputs':
            # Return the corresponding type
            return details.get(self.command_type, {})
        else:
            self._raise_error('Unknown detail name: {}'.format(detail_name))

    def _wrap_details(self, detail_name, details):
        if detail_name == 'envs':
            # Return the dict
            return details
        elif detail_name == 'depends_on':
            # Wrap the details in list and return
            return wrap_with_list(details)
        elif detail_name == 'requirements':
            # Wrap the details in list and return
            return wrap_with_list(details)
        elif detail_name == 'commands':
            # Wrap the details in list and return
            return wrap_with_list(details)
        elif detail_name == 'write_outputs':
            # Return the dict
            return details
        else:
            self._raise_error('Unknown detail name: {}'.format(detail_name))

    def _count_experiments(self, stage):
        # Get experiment specs
        exps_spec = self._get_experiment_specs(stage)

        # Return the count
        return len(exps_spec)

    def _get_experiment_specs(self, stage):
        # Check whether the stage is in allowed list
        allowed_stages = ['before_all_experiments', 'experiment_default',
                          'experiments', 'after_all_experiments']

        if stage not in allowed_stages:
            self._raise_error('Unexpected stage: {}'.format(stage))

        return self._get_stage_specs(stage)

    def _get_experiment_names(self, exps_spec):
        return [exp_spec.get('name', '') for exp_spec in exps_spec]

    def _check_empty_experiment(self, exp_spec):
        # Get the commands
        commands = self._get_experiment_details(exp_spec, 'commands')

        # Check whether the commands are empty
        return len(commands) <= 0

    ############################################################################
    # Time Delays
    ############################################################################

    def _wait_for_next_round(self):
        # Get round interval
        round_interval = self._get_round_interval_spec()

        # Log the wait
        self._log_verbose('Wait for next round for {}s'.format(round_interval))

        # Wait for some time
        time.sleep(round_interval)

    def _wait_for_next_deployment(self):
        # Get deployment interval
        deployment_interval = self._get_deployment_interval_spec()

        # Log the wait
        self._log_verbose('Wait for next deployment for {}s'.format(
            deployment_interval))

        # Wait for some time
        time.sleep(deployment_interval)

    ############################################################################
    # Getting Specs
    ############################################################################

    def _get_default_experiment_spec(self):
        return self.user_spec.get('experiment_default', {})

    def _get_stage_specs(self, stage):
        return self.user_spec.get(stage, {})

    def _get_server_specs(self):
        return self.user_spec.get('servers', [])

    def _get_requirement_specs(self):
        return self.user_spec.get('requirements', {})

    def _get_write_status_to_spec(self):
        # Get the paths
        write_status_to = self.user_spec.get('write_status_to', {})

        # Return the path for the current command type
        return write_status_to.get(self.command_type, None)

    def _get_round_interval_spec(self):
        return self.user_spec.get('round_interval', 0)

    def _get_deployment_interval_spec(self):
        return self.user_spec.get('deployment_interval', 0)

    def _get_check_any_errors_spec(self):
        return self.user_spec.get('check_any_errors', True)

    def _get_error_handler_specs(self):
        return self.user_spec.get('error_handlers', [])

    ############################################################################
    # Writing to Files
    ############################################################################

    def _write_to_file(self, contents, path):
        try:
            with open(path, 'w') as fp:
                fp.write(contents)
        except:
            self.logger.exception(
                'Could not write contents to file "{}"'.format(path))
            raise

    ############################################################################
    # Logging
    ############################################################################

    def _log_round(self):
        if self.verbose:
            # Log the round number
            self.logger.info('Round #{}'.format(self.round_idx + 1))

            # Log the undeployed experiments
            exps_spec = self._get_experiment_specs(self.stage)
            undeployed_names = [exps_spec[i].get('name', '#{}'.format(i))
                                for i in self.undeployed]
            self.logger.info('Undeployed experiments: {}'.format(
                json.dumps(undeployed_names)))

    def _log_round_time(self):
        if self.verbose:
            # Calculate round time
            elapsed_time = time.time() - self.prev_round_time

            # Log the elapsed time
            self.logger.info(
                'Elapsed round time: {:.3f}s'.format(elapsed_time))

    def _log_requirement_ids(self, req_ids):
        self.logger.debug('Collected requirement IDs: {}'.format(
            json.dumps(req_ids)))

    def _log_metrics(self, metrics):
        self.logger.debug('Server metrics: {}'.format(json.dumps(metrics)))

    def _log_deployment_to_server(self, exp_name, server_spec):
        # Get the server name
        server_name = server_spec.get('name', '')

        # Log the deployment
        self.logger.info('Deploy experiment "{}" to server "{}"'.format(
            exp_name, server_name))

    def _log_verbose(self, messages):
        # Check whether to log verbose messages
        if not self.verbose:
            return

        # Check the messages type
        if isinstance(messages, list):
            # Log all messages
            for message in messages:
                self.logger.info(message)
        elif isinstance(messages, str):
            # Log the message
            self.logger.info(messages)
        else:
            raise ValueError('Unknown messages type: {}'.format(
                type(messages)))

    ############################################################################
    # Error Handling
    ############################################################################

    def _raise_error(self, messages):
        # Check the messages type
        if isinstance(messages, list):
            # Log all messages
            for message in messages:
                self.logger.error(message)

            # Concatenate all messages
            combined_messages = '\n'.join(messages)

            # Raise the error
            raise ValueError(combined_messages)
        elif isinstance(message, str):
            # Log the message
            self.logger.error(messages)

            # Raise the error
            raise ValueError(messages)
        else:
            raise ValueError('Unknown messages type: {}'.format(
                type(messages)))
