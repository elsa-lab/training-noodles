import json
import logging
import re
import time

from training_noodles.cli import decode_output
from training_noodles.remote import run_commands_over_ssh


class Runner:
    def __init__(self, user_spec, verbose=False):
        # Save the user spec
        self.user_spec = user_spec

        # Save the logging variables
        self.verbose = verbose

    def run(self):
        """ Deploy all the experiments until finish.
        """
        # Initialize a set of indexes of undeployed experiments
        undeployed = set(range(self._count_experiments()))

        # Deploy all remaining experiments until there are none
        deployment_idx = 0

        while len(undeployed) > 0:
            # Log the deployment
            self._log_deployment(deployment_idx, undeployed)

            # Wait for next deployment
            if deployment_idx > 0:
                self._wait_for_next_deployment()

            # Filter the experiments to choose the undeployed experiments
            undeployed_exps = self._filter_undeployed_experiments(undeployed)

            # Try to deploy each experiment to one of the satisfied servers
            deployed = self._deploy_experiments(undeployed_exps)

            # Restore the original deployed indexes
            undeployed_list = list(undeployed)
            deployed = set([undeployed_list[i] for i in deployed])

            # Remove deployed indexes
            undeployed -= deployed

            # Increment deployment index
            deployment_idx += 1

        # Log the finish
        logging.info('Successfully deployed all experiments')

    def _deploy_experiments(self, exps_spec):
        # Initialize set of indexes of deployed servers
        deployed = set()

        # Initialize the empty metrics
        metrics = {}

        # Get servers spec
        servers_spec = self.user_spec.get('servers', [])

        # Iterate each experiment spec
        for exp_spec in exps_spec:
            # Get the experiment name
            exp_name = exp_spec.get('name', '')

            # Log the experiment
            if self.verbose:
                logging.info('Try to deploy experiment "{}"'.format(exp_name))

            # Update metrics lazily
            self._update_metrics(exp_spec, metrics)

            # Find satisfied servers
            satisfied_servers = self._find_satisfied_servers(
                exp_spec, metrics, deployed)

            # Log the satisfied servers
            if self.verbose:
                server_names = [servers_spec[i].get('name', '')
                                for i in satisfied_servers]
                logging.info('Satisfied servers: {}'.format(
                    json.dumps(server_names)))

            # Check whether there are any satisfied servers
            if len(satisfied_servers) > 0:
                # Choose the first satisfied server
                server_idx = next(iter(satisfied_servers))

                # Get experiment commands
                commands = exp_spec.get('commands', [])

                # Get server spec
                server_spec = servers_spec[server_idx]

                # Get the server name
                server_name = server_spec.get('name', '')

                # Log the deployment
                logging.info('Deploy experiment "{}" to server "{}"'.format(
                    exp_name, server_name))

                # Deploy the experiment to the server
                run_commands_over_ssh(commands, server_spec)

                # Add the index to the deployed servers
                deployed.add(server_idx)

            # Check whether there are no available servers in this deployment
            if len(deployed) >= len(servers_spec):
                # Log the break
                if self.verbose:
                    logging.info('No available servers, skip the deployment')

                break

        # Return the deployed experiments
        return deployed

    def _check_server_metrics(self, req_id):
        # Initialize the metric outputs
        metrics = []

        # Get requirements spec
        reqs_spec = self.user_spec.get('requirements', {})

        # Iterate each server spec
        for server_spec in self.user_spec.get('servers', []):
            # Get name of the server
            name = server_spec['name']

            # Log the server and requirement ID
            if self.verbose:
                logging.info('Check requirement "{}" on server: {}'.format(
                    req_id, name))

            # Get the requirement commands
            req_commands = reqs_spec.get(req_id, None)

            # Check whether the requirement command exists
            if req_commands is None:
                message = 'Requirement ID does not exist: {}'.format(req_id)
                logging.error(message)
                raise ValueError(message)

            # Run the remote command on server
            stdout = run_commands_over_ssh(req_commands, server_spec)

            # Decode the results
            results = decode_output(stdout)

            # Log the results
            logging.debug('Metric results:->\n{}'.format(results))

            # Calculate mean metric of results
            mean_metric = self._calc_mean(results)

            # Log the mean
            logging.debug('Mean metric: {}'.format(mean_metric))

            # Add the mean metric to the list
            metrics.append(mean_metric)

        # Return list of metrics for all servers
        return metrics

    def _count_experiments(self):
        # Get experiment specs as remaining experiments
        exps_spec = self.user_spec.get('experiments', [])

        # Return the count
        return len(exps_spec)

    def _filter_undeployed_experiments(self, undeployed):
        # Initialize the list of undeployed experiments
        undeployed_exps = []

        # Get experiment specs as remaining experiments
        exps_spec = self.user_spec.get('experiments', [])

        # Add each undeployed experiments to the list
        for exp_idx in undeployed:
            # Get the experiment spec
            exp_spec = exps_spec[exp_idx]

            # Add to the undeployed experiments
            undeployed_exps.append(exp_spec)

        # Return the undeployed experiments
        return undeployed_exps

    def _update_metrics(self, exp_spec, metrics):
        # Get experiment requirements
        requirements = exp_spec.get('requirements', {})

        # Iterate each requirement
        for req_id in requirements.keys():
            # Check whether the requirement ID has been existed in metrics
            if req_id not in metrics:
                # Log the check
                if self.verbose:
                    logging.info(('Requirement "{}" has not been checked, ' +
                                  'check now').format(req_id))

                # Check server metrics
                server_metrics = self._check_server_metrics(req_id)

                # Update the metrics
                metrics[req_id] = server_metrics

    def _find_satisfied_servers(self, exp_spec, metrics, deployed):
        # Get servers spec
        servers_spec = self.user_spec.get('servers', [])

        # Initialize all indexes of servers
        satisfied = set(range(len(servers_spec)))

        # Get experiment requirements
        requirements = exp_spec.get('requirements', {})

        # Iterate each requirement
        for req_id, req_expr in requirements.items():
            # Parse the requirement expression
            operator, value = self._parse_requirement_expression(req_expr)

            # Get the list of server metrics of the requirement
            servers_metrics = metrics.get(req_id, None)

            if servers_metrics is None:
                message = 'Requirement ID "{}" should be in metrics'.format(
                    req_id)
                logging.error(message)
                raise ValueError(message)

            # Update the indexes of satisfied servers by comparing the server
            # metric to the requirement value
            satisfied = filter(lambda i: self._is_metric_satisfied(
                servers_metrics[i], operator, value), satisfied)

        # Remove indexes of deployed servers
        satisfied = set(satisfied) - deployed

        # Return indexes of satisfied servers
        return satisfied

    def _wait_for_next_deployment(self):
        # Get deployment interval
        deployment_interval = self.user_spec.get('deployment_interval', 0)

        # Log the wait
        if self.verbose:
            logging.info('Wait for next deployment for {}s'.format(
                deployment_interval))

        # Wait for some time
        time.sleep(deployment_interval)

    def _log_deployment(self, deployment_idx, undeployed):
        if self.verbose:
            # Log the deployment number
            logging.info('Deployment #{}'.format(deployment_idx + 1))

            # Log the undeployed experiments
            exps_spec = self.user_spec.get('experiments', [])
            undeployed_names = [exps_spec[i].get('name', '#{}'.format(i))
                                for i in undeployed]
            logging.info('Undeployed experiments: {}'.format(
                json.dumps(undeployed_names)))

    def _log_requirement_ids(self, req_ids):
        logging.debug('Collected requirement IDs: {}'.format(
            json.dumps(req_ids)))

    def _log_metrics(self, metrics):
        logging.debug('Server metrics: {}'.format(json.dumps(metrics)))

    def _is_metric_satisfied(self, metric, operator, value):
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
            message = 'Unknown operator: {}'.format(operator)
            logging.error(message)
            raise ValueError(message)

    def _parse_requirement_expression(self, req_expr):
        # Remove whitespaces
        req_expr = req_expr.strip()

        # Parse the expression
        m = re.match(r'^(?P<operator>[<>=]+)(?P<value>[\d.]+)$', req_expr)

        # Check whether the expression is valid
        if m is None:
            message = 'Could not parse the requirement expression: {}'.format(
                req_expr)
            logging.error(message)
            raise ValueError(message)
        else:
            operator = m.group('operator')
            value = m.group('value')

            # Convert the value to float
            try:
                value = float(value)
            except:
                message = 'Could not convert value to float: {}'.format(value)
                logging.error(message)
                raise ValueError(message)

        # Return operator and value
        return operator, value

    def _calc_mean(self, results):
        # Split the results by newlines
        results = results.split('\n')

        # Remove empty contents in results
        results = filter(lambda s: len(s.strip()) > 0, results)

        try:
            # Convert the results to floats
            floats = list(map(float, results))

            # Calculate the mean
            mean = sum(floats) / len(floats)
        except:
            message = 'Could not calculate mean from the results: {}'.format(
                results)
            logging.error(message)
            raise ValueError(message)
        else:
            return mean
