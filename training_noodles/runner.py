import copy
import json
import logging
import re
import time

from training_noodles.cli import decode_output
from training_noodles.remote import run_commands_over_ssh


class Runner:
    def __init__(self, packet_type, user_spec, verbose=False):
        # Save the packet type
        self.packet_type = packet_type

        # Save the user spec
        self.user_spec = user_spec

        # Save the logging variables
        self.verbose = verbose

    def run(self):
        """ Deploy all the command packets until finish.
        """
        # Save the first timestamp
        start_time = time.time()

        # Initialize a set of indexes of undeployed packets
        undeployed = set(range(self._count_packets()))

        # Deploy all remaining packets until there are none
        round_idx = 0
        prev_round_time = time.time()

        while len(undeployed) > 0:
            # Log the deployment round
            self._log_round(round_idx, undeployed)

            # Wait for next round
            if round_idx > 0:
                self._wait_for_next_round()

            # Create undeployed packets
            undeployed_packets = self._filter_undeployed_packets(undeployed)

            # Try to deploy each packet to one of the satisfied servers
            deployed = self._deploy_packets(undeployed_packets)

            # Restore the original deployed indexes
            undeployed_list = list(undeployed)
            deployed = set([undeployed_list[i] for i in deployed])

            # Remove deployed indexes
            undeployed -= deployed

            # Log the round time
            self._log_round_time(prev_round_time)

            # Update previous round time
            prev_round_time = time.time()

            # Increment round index
            round_idx += 1

        # Calculate total elapsed time
        elapsed = time.time() - start_time

        # Log the finish
        logging.info('Total elapsed time: {:.3f}s'.format(elapsed))
        logging.info('Successfully deployed all commands')

    def _deploy_packets(self, packets_spec):
        # Initialize set of indexes of deployed servers
        deployed = set()

        # Initialize the empty metrics
        metrics = {}

        # Get servers spec
        servers_spec = self.user_spec.get('servers', [])

        # Iterate each packet spec
        for packet_idx, packet_spec in enumerate(packets_spec):
            # Get the packet name
            packet_name = packet_spec.get('name', '')

            # Log the packet
            if self.verbose:
                logging.info('Try to deploy packet "{}"'.format(packet_name))

            # Update metrics lazily
            self._update_metrics(packet_spec, metrics)

            # Find satisfied servers
            satisfied_servers = self._find_satisfied_servers(
                packet_spec, metrics, deployed)

            # Check whether there are any satisfied servers
            if len(satisfied_servers) > 0:
                # Wait for next deployment
                if len(deployed) > 0:
                    self._wait_for_next_deployment()

                # Choose the first satisfied server
                server_idx = next(iter(satisfied_servers))

                # Get server spec
                server_spec = servers_spec[server_idx]

                # Get the server name
                server_name = server_spec.get('name', '')

                # Log the deployment
                logging.info('Deploy packet "{}" to server "{}"'.format(
                    packet_name, server_name))

                # Get packet commands
                commands = packet_spec.get('commands', [])

                # Deploy the packet to the server
                results = self._run_commands(commands, server_spec)

                # Log the results
                logging.info('Commands results->\n{}'.format(results))

                # Add the index to the deployed servers
                deployed.add(server_idx)

            # Check whether there are no available servers in this deployment
            if len(deployed) >= len(servers_spec):
                # Log the break
                if self.verbose:
                    logging.info('No available servers, skip the deployment')

                break

        # Return the deployed packet indexes
        return deployed

    def _check_server_metrics(self, req_id):
        # Initialize the metric outputs
        metrics = []

        # Get requirements spec
        reqs_spec = self.user_spec.get('requirements', {})

        # Get server specs
        servers_spec = self.user_spec.get('servers', [])

        # Iterate each server spec
        for server_spec in servers_spec:
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
            results = self._run_commands(req_commands, server_spec)

            # Log the results
            logging.debug('Metric results:->\n{}'.format(results))

            # Try to calculate mean metric of results
            metric = self._try_calc_mean(results)

            # Log the metric
            logging.debug('Metric: {}'.format(metric))

            # Add the metric to the list
            metrics.append(metric)

        # Return list of metrics for all servers
        return metrics

    def _run_commands(self, commands, server_spec):
        # Get global server spec
        global_server_spec = self.user_spec.get('each_server', {})

        # Copy the server spec to avoid changing the original server spec
        server_spec = copy.deepcopy(server_spec)

        # Update missing properties in server spec by global server spec
        server_spec.update({k: v for k, v in global_server_spec.items()
                            if k not in server_spec})

        # Run the commands on remote
        stdout, stderr = run_commands_over_ssh(commands, server_spec)

        # Decode the output
        stdout_results = decode_output(stdout)
        stderr_results = decode_output(stderr)

        # Log the errors if there are any
        if self.verbose and len(stderr_results) > 0:
            logging.error('STDERR->\n{}'.format(stderr_results))

        # Return the results
        return stdout_results

    def _count_packets(self):
        # Get command packets
        packets_spec = self._get_command_packets()

        # Return the count
        return len(packets_spec)

    def _filter_undeployed_packets(self, undeployed):
        # Initialize the list of undeployed packets
        undeployed_packets = []

        # Get command packets
        packets_spec = self._get_command_packets()

        # Add each undeployed packet to the list
        for packet_idx in undeployed:
            # Get the packet spec
            packet_spec = packets_spec[packet_idx]

            # Add to the undeployed packets
            undeployed_packets.append(packet_spec)

        # Return the undeployed packets
        return undeployed_packets

    def _update_metrics(self, packet_spec, metrics):
        # Get packet requirements
        requirements = packet_spec.get('requirements', {})

        # Log the update
        if self.verbose:
            logging.info('Update metrics')

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

    def _find_satisfied_servers(self, packet_spec, metrics, deployed):
        # Get servers spec
        servers_spec = self.user_spec.get('servers', [])

        # Initialize all indexes of servers
        satisfied = set(range(len(servers_spec)))

        # Get packet requirements
        requirements = packet_spec.get('requirements', {})

        # Log the find
        if self.verbose:
            logging.info('Find satisfied servers')

        # Iterate each requirement
        for req_id, req_expr in requirements.items():
            # Parse the requirement expression
            operator, value = self._parse_requirement_expression(req_expr)

            # Log the requirement
            logging.debug('Requirement ID: {}, Operator: {}, Value: {}'.format(
                req_id, operator, value))

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

        # Log the satisfied servers
        if self.verbose:
            server_names = [servers_spec[i].get('name', '')
                            for i in satisfied]
            logging.info('Satisfied servers: {}'.format(
                json.dumps(server_names)))

        # Return indexes of satisfied servers
        return satisfied

    def _wait_for_next_round(self):
        # Get round interval
        round_interval = self.user_spec.get('round_interval', 0)

        # Log the wait
        if self.verbose:
            logging.info('Wait for next round for {}s'.format(
                round_interval))

        # Wait for some time
        time.sleep(round_interval)

    def _wait_for_next_deployment(self):
        # Get deployment interval
        deployment_interval = self.user_spec.get('deployment_interval', 0)

        # Log the wait
        if self.verbose:
            logging.info('Wait for next deployment for {}s'.format(
                deployment_interval))

        # Wait for some time
        time.sleep(deployment_interval)

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

            # Try to convert the value to float
            try:
                value = float(value)
            except:
                # Log the conversion fail
                if self.verbose:
                    logging.info(('Failed to convert value to float,' +
                                  ' ignore now: {}').format(value))

        # Return operator and value
        return operator, value

    def _try_calc_mean(self, results):
        # Split the results by newlines
        results = results.split('\n')

        # Remove empty contents in results
        results = filter(lambda s: len(s.strip()) > 0, results)

        try:
            # Convert the results to floats
            floats = list(map(float, results))

            # Calculate the mean
            result = sum(floats) / len(floats)
        except:
            # Log the conversion fail
            if self.verbose:
                logging.info(('Failed to convert results to floats,' +
                              ' ignore now: {}').format(results))

            # Use original results
            result = results

        return result

    def _get_command_packets(self):
        # Get packet box
        packet_box = self.user_spec.get(self.packet_type, {})

        # Get packet bundle
        packets = packet_box.get('all', {})

        # Return the packet bundle
        return packets

    def _log_round(self, round_idx, undeployed):
        if self.verbose:
            # Log the round number
            logging.info('Round #{}'.format(round_idx + 1))

            # Log the undeployed packets
            packets_spec = self._get_command_packets()
            undeployed_names = [packets_spec[i].get('name', '#{}'.format(i))
                                for i in undeployed]
            logging.info('Undeployed packets: {}'.format(
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
