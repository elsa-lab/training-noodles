import json
import logging
import os
import pathlib
import tempfile

from training_noodles.cli import (
    run_command, read_command_results, decode_output, escape_command)
from training_noodles.utils import split_by_scheme, wrap_with_list


def evaluate_expression_on_local(expr, envs={}):
    # Build endpoint command
    endpoint_command = _build_local_command()

    # Build inner command
    inner_command = _build_eval_command(expr)

    # Run commands on endpoint
    return _run_commands_on_endpoint(
        endpoint_command, inner_command, envs=envs)


def run_commands(server_spec, commands, user_files={}, envs={}):
    """ Run commands on either local or remote machine.

    The "commands" will be written into the temporary file. The final command
    would use bash to execute these "commands" from the temporary file and write
    STDOUT and STDERR into the newly created temporary files (Temp STDOUT and
    Temp STDERR).

    Arguments:
        server_spec (dict): The server spec.
        commands (str or list): A single command (str) or list of commands.
        user_files (dict): Optional file paths for appending STDOUT and STDERR
            for all command groups. It's a dict(stdout, stderr) where each value
            is the corresponding path.
        envs (dict): Environment variables.

    Returns:
        (all_results, debug_infos) where "all_results" is a list of "results"
        and "debug_infos" is a list of "debug_info". See
        function "_run_commands_on_endpoint".
    """
    # Wrap the commands in list for consistency
    commands = wrap_with_list(commands)

    # Group commands by endpoints
    group_results = _group_commands_by_endpoints(server_spec, commands)

    # Clear user files at the first iteration
    clear_user_files = True

    # Initialize the outputs
    all_results = []
    debug_infos = []

    # Iterate each endpoint group
    for endpoint_command, inner_commands in group_results:
        # Build remote commands
        inner_commands = _build_remote_command(inner_commands, envs=envs)

        # Run commands on endpoint
        results, debug_info = _run_commands_on_endpoint(
            endpoint_command, inner_commands, user_files=user_files,
            clear_user_files=clear_user_files, envs=envs)

        # Disable clearing user files in the latter command groups
        clear_user_files = False

        # Add the results and debug info to the outputs
        all_results.append(results)
        debug_infos.append(debug_info)

    # Return the results
    return all_results, debug_infos


def get_error_messages(results, debug_info):
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
        messages.append('Outer STDOUT->\n{}'.format(results['outer_stdout']))
        messages.append('Outer STDERR->\n{}'.format(results['outer_stderr']))
        messages.append('Inner STDOUT->\n{}'.format(results['stdout']))
        messages.append('Inner STDERR->\n{}'.format(results['stderr']))

    return messages


def _run_commands_on_endpoint(endpoint_command, inner_commands,
                              user_files={}, clear_user_files=True, envs={}):
    # Read the original user file sizes
    user_file_sizes = _read_file_sizes(user_files, clear_user_files, envs)

    # Create temporary files for each command group
    temp_files = _create_temp_files(user_files)

    # Write command to the stdin file
    _write_command_to_stdin(inner_commands, temp_files)

    # Build outer command
    outer_command = _build_outer_command(
        endpoint_command, temp_files, user_files, clear_user_files)

    # Execute the outer command
    p_obj = run_command(outer_command, extra_envs=envs)

    # Read return code from the outer command
    outer_stdout, outer_stderr, return_code = read_command_results(p_obj)

    # Read stdout and stderr from the inner commands
    inner_stdout, inner_stderr = _read_stdout_and_stderr(
        temp_files, user_files, user_file_sizes)

    # Delete temporary files
    _delete_temp_files(temp_files)

    # Build the decoded results
    results = {
        'outer_stdout': decode_output(outer_stdout),
        'outer_stderr': decode_output(outer_stderr),
        'stdout': decode_output(inner_stdout),
        'stderr': decode_output(inner_stderr),
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


def _group_commands_by_endpoints(server_spec, commands):
    # Initialize empty outputs
    endpoint_commands = []
    inner_commands = []

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
                _add_endpoint_results_to_outputs(
                    server_spec, prev_scheme, cur_group, endpoint_commands,
                    inner_commands)

                # Reset current group of commands
                cur_group = [follow_command]

            # Save the scheme
            prev_scheme = scheme
        else:
            message = 'Unknown scheme "{}" in command "{}"'.format(
                scheme, command)
            logging.error(message)
            raise ValueError(message)

    # Add final results to outputs
    _add_endpoint_results_to_outputs(
        server_spec, prev_scheme, cur_group, endpoint_commands,
        inner_commands)

    # Return zipped results
    return zip(endpoint_commands, inner_commands)


def _add_endpoint_results_to_outputs(server_spec, prev_scheme, cur_group,
                                     endpoint_commands, inner_commands):
    # Check whether to build local or remote command
    if prev_scheme == 'local':
        endpoint_command = _build_local_command()
    else:
        endpoint_command = _build_endpoint_command(server_spec)

    # Add endpoint command to the outputs
    endpoint_commands.append(endpoint_command)

    # Add current group of commands to the outputs
    inner_commands.append(cur_group)


def _read_file_sizes(files, clear_user_files, envs):
    # Initialize the file sizes
    file_sizes = {}

    # Iterate each file
    for stream, path in files.items():
        # Check whether to read the file size
        if clear_user_files:
            # The user file is about to be cleared, so the file size will be 0
            file_size = 0
        else:
            # Read the file size
            try:
                file_size = os.path.getsize(path)
            except:
                logging.exception(
                    'Could not read the file size from file "{}"'.format(path))
                raise

        # Save the file size to the results
        file_sizes[stream] = file_size

    # Return the file sizes
    return file_sizes


def _create_temp_files(user_files):
    # Initialize the results
    temp_files = {}

    # Set all streams
    streams = ['stdin', 'stdout', 'stderr']

    # Set whether to close the file pointer
    closes = [False, True, True]

    # Iterate each stream
    for stream, close in zip(streams, closes):
        # Check whether the user file exists
        user_path = user_files.get(stream, None)

        # Only create the temporary file when the user file doesn't exist
        if user_path is None:
            # Create the temporary file
            fp, path = _create_temp_file(stream, close=close)

            # Save the file pointer, path and temporary marker
            temp_files[stream] = dict(fp=fp, path=path)

    # Return the results
    return temp_files


def _create_temp_file(output_type, close=True):
    # Create a temporary file
    try:
        # Set the suffix
        suffix = '.{}'.format(output_type)

        # Create a named temporary file
        fp = tempfile.NamedTemporaryFile(
            delete=False, prefix='training_noodles.', suffix=suffix)
    except:
        logging.exception('Failed to create temporary file')
        raise

    # Check whether to close the file
    if close:
        fp.close()

    # Convert the paths to POSIX-style paths
    path = pathlib.Path(fp.name).as_posix()

    # Log the temporary files
    logging.debug('Created temporary file for {}: {}'.format(
        output_type, path))

    # Return the temporary file pointer and path
    return fp, path


def _write_command_to_stdin(command, files):
    # Get the file pointer and path
    stdin = files['stdin']
    fp, path = stdin['fp'], stdin['path']

    # Log the command and temporary file
    logging.debug('Write command to temporary stdin file "{}"->\n{}'.format(
        path, command))

    # Write the commands into the stdin file
    fp.write(command.encode('utf-8'))

    # Close the stdin file
    fp.close()


def _read_stdout_and_stderr(temp_files, user_files, user_file_sizes):
    # Initialize all contents
    all_contents = []

    # Set all streams
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
            offset = user_file_sizes.get(stream, None)

        # Read the file contents
        contents = _read_file_contents(stream, read_path, offset=offset)

        # Add the contents to the list
        all_contents.append(contents)

    return all_contents[0], all_contents[1]


def _read_file_contents(stream, path, offset=0):
    try:
        # Open the file in binary mode
        with open(path, 'rb') as fp:
            # Offset the stream position
            fp.seek(offset)

            # Read the contents
            contents = fp.read()

        # Return the contents
        return contents
    except:
        logging.exception('Failed to read {} file: {}'.format(stream, path))
        raise


def _delete_temp_files(temp_files):
    # Iterate each stream
    for stream, temp_file in temp_files.items():
        # Get the path
        path = temp_file['path']

        # Try to delete the temporary file
        try:
            os.unlink(path)
        except:
            # Only log the exception, don't raise it
            logging.exception(('Failed to delete {} temporary file,' +
                               ' ignore now: {}').format(stream, path))


def _build_endpoint_command(server_spec):
    """ Build endpoint command.

    The endpoint command is either a local or remote command depending on the
    server spec.

    Arguments:
        server_spec (dict): Server spec.

    References:
        https://linux.die.net/man/1/ssh

    Returns:
        str: Endpoint command.
    """
    # Check whether the hostname is localhost
    if server_spec.get('hostname', None) == 'localhost':
        return _build_local_command()
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


def _build_local_command():
    return 'bash -c'


def _build_remote_command(commands, envs={}):
    # Initialize the outputs
    remote_commands = []

    # Build list of commands to set environment variables
    for k, v in envs.items():
        # Convert the value to string
        v = str(v)

        # Escape the value
        escaped_v = escape_command(v)

        # Build the command
        export_command = 'export {}="{}"'.format(k, escaped_v)

        # Add the command to the list
        remote_commands.append(export_command)

    # Append the other commands
    remote_commands.extend(commands)

    # Concatenate all commands by newlines and return
    return '\n'.join(remote_commands)


def _build_eval_command(expr):
    return 'echo -n {}'.format(expr)


def _build_outer_command(endpoint_command, temp_files, user_files,
                         clear_user_files):
    # Get temporary file path for STDIN
    stdin_path = temp_files['stdin']['path']

    # Build the command part for STDIN
    stdin_command = '< \'{}\''.format(stdin_path)

    # Build the command part for STDOUT and STDERR
    stdout_command = _build_output_command_part(
        'stdout', temp_files, user_files, clear_user_files)
    stderr_command = _build_output_command_part(
        'stderr', temp_files, user_files, clear_user_files)

    # Build the command
    outer_command = '{} \'bash -s\' {} {} {}'.format(
        endpoint_command, stdin_command, stdout_command, stderr_command)

    # Return the final command
    return outer_command


def _build_output_command_part(stream, temp_files, user_files,
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
