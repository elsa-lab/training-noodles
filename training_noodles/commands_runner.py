import json

from training_noodles.cli import CLI
from training_noodles.data_structure_utils import wrap_with_list
from training_noodles.file_helper import FileHelper
from training_noodles.logger import Logger
from training_noodles.string_utils import split_by_scheme
from training_noodles.temp_files_helper import TempFilesHelper


class CommandsRunner:
    """ Commands runner.

    This class runs the commands on either local or remote machines.

    The process is as follows:
    1. List of commands are organized into groups of endpoint commands and
    unmixed commands by whether they will be run on local or remote endpoint
    2. A group of unmixed commands is mixed with environment variables and
    concatenated with newlines to become inner commands
    3. Write the inner commands into a temporary STDIN file
    4. Build the outer command by concatenating endpoint command and the
    temporary STDIN file
    5. Run the outer command
    6. Read the STDOUT and STDERR files

    Examples:
    1. ['local:cd ~', 'local:echo $TEST1', 'remote:ls'] are organized into 2
    groups, groups of endpoint commands are ['bash -c', 'ssh user1@server1']
    and groups of unmixed commands are [['cd ~'], ['echo $TEST1', 'ls']].
    2. If the given environment variable is {'TEST1': 'test1'}, the inner
    commands will be ['export TEST1="test1"\ncd ~',
    'export TEST1="test1'\necho $TEST1\nls'].
    3. The inner commands are written into the temporary files
    '/tmp/temp1.stdin' and '/tmp/temp2.stdin' (The real paths are determined by
    Python tempfile module).
    4. The outer commands will be ['bash -c \'bash -s\' < /tmp/temp1.stdin
    > /tmp/temp1.stdout' 2> /tmp/temp1.stderr', 'ssh user1@server1 \'bash -s\'
    < /tmp/temp2.stdin > /tmp/temp2.stdout 2> /tmp/temp2.stderr'].
    5. Run the outer commands
    6. Read the files [['/tmp/temp1.stdout', '/tmp/temp1.stderr'],
    ['/tmp/temp2.stdout', '/tmp/temp2.stderr']].

    Glossary:
    * Endpoint: Either a local machine or a remote machine.
    * Endpoint command: A command to be run on an endpoint.
    * Inner command: Exporting environment variables commands and unmixed
    commands, which will be written into the file.
    * Outer command: Command to be run by the subprocess module.
    * Unmixed command: Command specified by the user.
    """

    def __init__(self, shell_string='bash -c', shell_stdin='bash -s'):
        """ Initialize the instance.

        Arguments:
            shell_string (str): Shell command to read from string (e.g.,
                "bash -c").
            shell_stdin (str): Shell command to read from STDIN (e.g.,
                "bash -s").
        """

        # Save the shell command to read from string
        self.shell_string = shell_string

        # Save the shell command to read from STDIN
        self.shell_stdin = shell_stdin

        # Create a CLI
        self.cli = CLI(shell_string=self.shell_string)

        # Create a file helper
        self.file_helper = FileHelper()

        # Create a temporary files helper
        closes = dict(stdin=False, stdout=True, stderr=True)
        self.temp_helper = TempFilesHelper(closes)

        # Create a logger
        self.logger = Logger('command')

    def run_commands(self, commands, server_spec=None, user_files={}, envs={}):
        """ Run commands on either local or remote machine.

        The "commands" will be written into the temporary file. The final
        command would use bash to execute these "commands" from the temporary
        file and write STDOUT and STDERR into the newly created temporary files
        (Temp STDOUT and Temp STDERR).

        Arguments:
            commands (str or list): A single command (str) or list of commands.
            server_spec (dict): Optional server spec. If the server spec is
                omitted, the endpoint will be local.
            user_files (dict): Optional file paths for appending STDOUT and
                STDERR for all command groups. It's a dict(stdout, stderr)
                where each value is the corresponding path.
            envs (dict): Optional environment variables.

        Returns:
            (all_results, debug_infos) where "all_results" is a list of
            "results" and "debug_infos" is a list of "debug_info". See
            function "_run_commands_on_endpoint".
        """
        # Wrap the commands in list for consistency
        commands = wrap_with_list(commands)

        # Group commands by endpoints
        group_results = self._group_commands_by_endpoints(
            server_spec, commands)

        # Clear user files at the first iteration
        clear_user_files = True

        # Initialize the outputs
        all_results = []
        debug_infos = []

        # Iterate each endpoint group
        for endpoint_command, unmixed_commands in group_results:
            # Build inner commands
            inner_commands = self._build_inner_commands(
                unmixed_commands, envs=envs)

            # Run commands on endpoint
            results, debug_info = self._run_commands_on_endpoint(
                endpoint_command, inner_commands, user_files=user_files,
                clear_user_files=clear_user_files, envs=envs)

            # Disable clearing user files in the latter command groups
            clear_user_files = False

            # Add the results and debug info to the outputs
            all_results.append(results)
            debug_infos.append(debug_info)

        # Return the results
        return all_results, debug_infos

    def evaluate_expression_on_local(self, expr, envs={}):
        # Build endpoint command
        endpoint_command = self._build_local_endpoint_command()

        # Build inner command
        inner_command = self._build_eval_command(expr)

        # Run commands on endpoint
        return self._run_commands_on_endpoint(
            endpoint_command, inner_command, envs=envs)

    def get_error_messages(self, results, debug_info):
        # Initialize empty messages
        messages = []

        # Check errors caused by either outer command or inner commands
        return_code_error = (results['return_code'] != 0)
        outer_error = (len(results['outer_stderr']) > 0)
        inner_error = (len(results['stderr']) > 0)

        if return_code_error or outer_error or inner_error:
            messages.append('Error occurred when running the commands')
            messages.append('Outer command->\n{}'.format(
                debug_info['outer_command']))
            messages.append('Inner commands->\n{}'.format(
                debug_info['inner_commands']))
            messages.append('Environment variables->\n{}'.format(
                json.dumps(debug_info['envs'])))
            messages.append('Return code: {}'.format(results['return_code']))
            messages.append(
                'Outer STDOUT->\n{}'.format(results['outer_stdout']))
            messages.append(
                'Outer STDERR->\n{}'.format(results['outer_stderr']))
            messages.append('Inner STDOUT->\n{}'.format(results['stdout']))
            messages.append('Inner STDERR->\n{}'.format(results['stderr']))

        return messages

    def _run_commands_on_endpoint(
            self, endpoint_command, inner_commands, user_files={},
            clear_user_files=True, envs={}):
        # Build the user file offsets
        user_file_offsets = self._build_user_file_offsets(
            user_files, clear_user_files, envs)

        # Create temporary files for each command group
        temp_files = self.temp_helper.create_temp_files(user_files)

        # Write command to the stdin file
        self._write_command_to_stdin(inner_commands, temp_files)

        # Build outer command
        outer_command = self._build_outer_command(
            endpoint_command, temp_files, user_files, clear_user_files)

        # Execute the outer command
        p_obj = self.cli.run_command(outer_command, extra_envs=envs)

        # Read return code from the outer command
        outer_stdout, outer_stderr, return_code = self.cli.read_results(p_obj)

        # Read stdout and stderr from the inner commands
        inner_stdout, inner_stderr = self._read_stdout_and_stderr(
            temp_files, user_files, user_file_offsets)

        # Delete temporary files
        self.temp_helper.delete_temp_files(temp_files)

        # Build the decoded results
        results = {
            'outer_stdout': CLI.decode_output(outer_stdout),
            'outer_stderr': CLI.decode_output(outer_stderr),
            'stdout': CLI.decode_output(inner_stdout),
            'stderr': CLI.decode_output(inner_stderr),
            'return_code': return_code,
        }

        # Build debugging info
        debug_info = {
            'inner_commands': inner_commands,
            'outer_command': outer_command,
            'envs': envs,
        }

        # Return the results
        return results, debug_info

    def _group_commands_by_endpoints(self, server_spec, commands):
        # Initialize empty outputs
        endpoint_commands = []
        unmixed_commands = []

        # Set identifiable endpoint schemes
        schemes = ['local', 'remote']

        # Initialize previous scheme of the group
        prev_scheme = None

        # Initialize current group of commands
        cur_group = []

        # Iterate each command
        for command in commands:
            # Try to split the command by scheme
            success, scheme, follow_command = split_by_scheme(command, schemes)

            # Check whether there is unknown scheme
            if success:
                # Set default scheme to "remote"
                scheme = scheme or 'remote'

                if scheme == prev_scheme or prev_scheme is None:
                    # Append the command to the current group of commands
                    cur_group.append(follow_command)
                else:
                    # Add results to outputs
                    self._add_endpoint_results_to_outputs(
                        server_spec, prev_scheme, cur_group, endpoint_commands,
                        unmixed_commands)

                    # Reset current group of commands
                    cur_group = [follow_command]

                # Save the scheme
                prev_scheme = scheme
            else:
                self.logger.raise_error(
                    'Unknown scheme "{}" in command "{}"'.format(
                        scheme, command))

        # Add final results to outputs
        if prev_scheme is not None:
            self._add_endpoint_results_to_outputs(
                server_spec, prev_scheme, cur_group, endpoint_commands,
                unmixed_commands)

        # Return zipped results
        return zip(endpoint_commands, unmixed_commands)

    def _add_endpoint_results_to_outputs(
            self, server_spec, prev_scheme, cur_group, endpoint_commands,
            unmixed_commands):
        # Check whether to build local or remote endpoint command
        if prev_scheme == 'local':
            endpoint_command = self._build_local_endpoint_command()
        else:
            endpoint_command = self._build_endpoint_command(server_spec)

        # Add endpoint command to the outputs
        endpoint_commands.append(endpoint_command)

        # Add current group of commands to the outputs
        unmixed_commands.append(cur_group)

    def _build_endpoint_command(self, server_spec):
        """ Build endpoint command.

        The endpoint command is either a local or remote command depending on
        the server spec.

        Arguments:
            server_spec (dict): Server spec. If the spec is None or
                server_spec['hostname'] is "localhost", the endpoint will be
                local, otherwise remote.

        References:
            https://linux.die.net/man/1/ssh

        Returns:
            str: Remote endpoint command.
        """
        # Check whether the server spec is intended to run on local machine
        if (server_spec is None
                or server_spec.get('hostname', None) == 'localhost'):
            is_local = True
        else:
            is_local = False

        # Check whether the endpoint is local
        if is_local:
            return self._build_local_endpoint_command()
        else:
            # Initialize the ssh options
            options = []

            # Check whether to add identity option
            private_key_path = server_spec.get('private_key_path', None)
            if private_key_path is not None:
                options.extend(['-i', private_key_path])

            # Check whether to add port option
            port = server_spec.get('port', None)
            if port is not None:
                options.extend(['-p', str(port)])

            # Build the authority
            username = server_spec.get('username', None)
            hostname = server_spec.get('hostname', None)

            if username is None:
                authority = '{}'.format(hostname)
            else:
                authority = '{}@{}'.format(username, hostname)

            # Build the options command
            option_command = ' '.join(options)

            # Build the SSH command
            ssh_command = 'ssh {} {}'.format(option_command, authority)

            # Return the SSH command
            return ssh_command

    def _build_local_endpoint_command(self):
        return self.shell_string

    def _build_inner_commands(self, unmixed_commands, envs={}):
        # Initialize the outputs
        remote_commands = []

        # Build list of commands to set environment variables
        for k, v in envs.items():
            # Convert the value to string
            v = str(v)

            # Escape the value
            escaped_v = CLI.escape_command(v)

            # Build the command
            export_command = 'export {}="{}"'.format(k, escaped_v)

            # Add the command to the list
            remote_commands.append(export_command)

        # Append the unmixed commands
        remote_commands.extend(unmixed_commands)

        # Concatenate all commands by newlines and return
        return '\n'.join(remote_commands)

    def _build_outer_command(self, endpoint_command, temp_files, user_files,
                             clear_user_files):
        # Get temporary file path for STDIN
        stdin_path = temp_files['stdin']['path']

        # Build the command part for STDIN
        stdin_command = '< \'{}\''.format(stdin_path)

        # Build the command part for STDOUT and STDERR
        stdout_command = self._build_output_command_part(
            'stdout', temp_files, user_files, clear_user_files)
        stderr_command = self._build_output_command_part(
            'stderr', temp_files, user_files, clear_user_files)

        # Build the command
        outer_command = '{} \'{}\' {} {} {}'.format(
            endpoint_command, self.shell_stdin, stdin_command, stdout_command,
            stderr_command)

        # Return the final command
        return outer_command

    def _build_output_command_part(self, stream, temp_files, user_files,
                                   clear_user_files):
        # Get user file path
        user_path = user_files.get(stream, None)

        # Set the redirection operator
        if stream == 'stdout':
            redirection = '>'
        elif stream == 'stderr':
            redirection = '2>'
        else:
            raise ValueError('Unsupported stream "{}"'.format(stream))

        # Check whether to output to the user file
        if user_path is None:
            # Get the temporary file path
            temp_path = temp_files[stream]['path']

            # Output to the temporary path
            output_path = temp_path
        else:
            # Check whether to append to the file
            if not clear_user_files:
                redirection = '{}>'.format(redirection)

            # Output to the user file
            output_path = user_path

        # Build the command part and return
        return '{} \'{}\''.format(redirection, output_path)

    def _build_eval_command(self, expr):
        return 'echo -n {}'.format(expr)

    def _build_user_file_offsets(self, files, clear, envs):
        # Initialize the offsets
        user_file_offsets = {}

        # Iterate each file
        for stream, path in files.items():
            # Check whether to clear the old user file
            if clear:
                # The user file is about to be cleared, so the offset will be 0
                offset = 0
            else:
                # Read the file size as the offset
                offset = self.file_helper.read_file_size(path)

            # Save the offset in the results
            user_file_offsets[stream] = offset

        # Return the offsets
        return user_file_offsets

    def _write_command_to_stdin(self, command, files):
        # Get the file pointer and path
        stdin = files['stdin']
        fp, path = stdin['fp'], stdin['path']

        # Log the command and temporary file
        self.logger.debug(
            'Write command to temporary stdin file "{}"->\n{}'.format(
                path, command))

        # Write the commands into the stdin file
        fp.write(command.encode('utf-8'))

        # Close the stdin file
        fp.close()

    def _read_stdout_and_stderr(self, temp_files, user_files,
                                user_file_offsets):
        # Initialize all contents
        all_contents = []

        # Set all streams to read
        streams = ['stdout', 'stderr']

        # Iterate each stream
        for stream in streams:
            # Get the user file path
            user_path = user_files.get(stream)

            # Check whether to read from user file
            if user_path is None:
                # Get the temporary file path
                temp_path = temp_files[stream]['path']

                # Set the file to read
                read_path = temp_path

                # There is no old file, set offset to the beginning
                offset = 0
            else:
                # Set the file to read
                read_path = user_path

                # Get the old user file size as offset
                offset = user_file_offsets.get(stream, None)

            # Read the file contents
            contents = self.file_helper.read_file_contents(
                read_path, offset=offset)

            # Add the contents to the list
            all_contents.append(contents)

        # Return the contents
        return all_contents[0], all_contents[1]
