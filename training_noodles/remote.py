import logging
import os
import pathlib
import tempfile

from training_noodles.cli import (
    decode_output, run_command, read_command_results)
from training_noodles.utils import split_by_scheme, wrap_with_list


def run_commands_over_ssh(server_spec, commands, envs={}):
    """ Run commands over SSH.

    The "commands" will be written into the temporary file. The final command
    would use bash to execute these "commands" from the temporary file and write
    STDOUT and STDERR into the newly created temporary files (Temp STDOUT and
    Temp STDERR).

    Arguments:
        server_spec (dict): The server spec.
        commands (str or list): A single command (str) or list of commands.
        envs (dict): Environment variables.

    Returns:
        (results, debug_infos) where "results" is a dict(stdouts, stderrs,
        returncodes, temp_stdouts, temp_stderrs) and "debug_infos" is a list of
        dict(inner_command, outer_command).
    """
    # Wrap the commands in list for consistency
    commands = wrap_with_list(commands)

    # Group commands by endpoints
    endpoint_results = _group_commands_by_endpoints(server_spec, commands)

    # Initialize the results
    stdouts, stderrs, returncodes, temp_stdouts, temp_stderrs = (
        [], [], [], [], [])

    # Initialize the debug infos
    inner_commands = []
    outer_commands = []

    # Iterate each endpoint group
    for ssh_command, command_group in endpoint_results:
        # Create temporary files
        temp_files = _create_temp_files()

        # Concatenate commands by newlines
        inner_command = '\n'.join(command_group)

        # Write command to temporary stdin file
        _write_command_to_stdin(inner_command, temp_files)

        # Build outer command
        outer_command = _build_outer_command(ssh_command, temp_files)

        # Execute the outer command
        p_obj = run_command(outer_command, extra_envs=envs)

        # Read the command results
        stdout, stderr, returncode = read_command_results(p_obj)

        # Read stdout and stderr from temporary files
        temp_stdout, temp_stderr = _read_stdout_and_stderr(temp_files)

        # Delete temporary files
        _delete_temp_files(temp_files)

        # Decode and append the results
        stdouts.append(decode_output(stdout))
        stderrs.append(decode_output(stderr))
        temp_stdouts.append(decode_output(temp_stdout))
        temp_stderrs.append(decode_output(temp_stderr))

        # Append the returncode
        returncodes.append(returncode)

        # Append the commands
        inner_commands.append(inner_command)
        outer_commands.append(outer_command)

    # Build the results
    results = {
        'stdouts': stdouts,
        'stderrs': stderrs,
        'returncodes': returncodes,
        'temp_stdouts': temp_stdouts,
        'temp_stderrs': temp_stderrs,
    }

    # Build debugging info
    debug_info = {
        'inner_commands': inner_commands,
        'outer_commands': outer_commands,
    }

    # Return the results
    return results, debug_info


def _group_commands_by_endpoints(server_spec, commands):
    # Initialize empty outputs
    ssh_commands = []
    endpoint_commands = []

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
            if scheme == prev_scheme or prev_scheme is None:
                # Append the command to the current group of commands
                cur_group.append(follow_command)
            else:
                # Add results to outputs
                _add_endpoint_results_to_outputs(
                    server_spec, prev_scheme, cur_group, ssh_commands,
                    endpoint_commands)

                # Reset current group of commands
                cur_group = [follow_command]
        else:
            message = 'Unknown scheme "{}" in command "{}"'.format(
                scheme, command)
            logging.error(message)
            raise ValueError(message)

    # Add final results to outputs
    _add_endpoint_results_to_outputs(
        server_spec, prev_scheme, cur_group, ssh_commands,
        endpoint_commands)

    # Return zipped results
    return zip(ssh_commands, endpoint_commands)


def _add_endpoint_results_to_outputs(server_spec, prev_scheme, cur_group,
                                     ssh_commands, endpoint_commands):
    # Check whether to build local or remote command
    if prev_scheme == 'local':
        ssh_command = _build_local_command()
    else:
        ssh_command = _build_ssh_command(server_spec)

    # Add SSH command to the outputs
    ssh_commands.append(ssh_command)

    # Add current group of commands to the outputs
    endpoint_commands.append(cur_group)


def _create_temp_files():
    # Create temporary files
    try:
        stdin_fp = tempfile.NamedTemporaryFile(
            delete=False, prefix='training_noodles.', suffix='.stdin')
        stdout_fp = tempfile.NamedTemporaryFile(
            delete=False, prefix='training_noodles.', suffix='.stdout')
        stderr_fp = tempfile.NamedTemporaryFile(
            delete=False, prefix='training_noodles.', suffix='.stderr')
    except:
        logging.exception('Failed to create temporary files')
        raise

    # Close stdout and stderr files
    stdout_fp.close()
    stderr_fp.close()

    # Convert the paths to POSIX-style paths
    stdin_path = pathlib.Path(stdin_fp.name).as_posix()
    stdout_path = pathlib.Path(stdout_fp.name).as_posix()
    stderr_path = pathlib.Path(stderr_fp.name).as_posix()

    # Log the temporary files
    logging.debug('Created temporary file for stdin: {}'.format(stdin_path))
    logging.debug('Created temporary file for stdout: {}'.format(stdout_path))
    logging.debug('Created temporary file for stderr: {}'.format(stderr_path))

    # Return the temporary files and paths
    return {
        'stdin_fp': stdin_fp,
        'stdout_fp': stdout_fp,
        'stderr_fp': stderr_fp,
        'stdin_path': stdin_path,
        'stdout_path': stdout_path,
        'stderr_path': stderr_path,
    }


def _write_command_to_stdin(command, temp_files):
    # Log the command and temporary file
    logging.debug('Write command to temporary stdin file "{}"->\n{}'.format(
        temp_files['stdin_path'], command))

    # Write the commands into the temporary stdin file
    temp_files['stdin_fp'].write(command.encode('utf-8'))

    # Close the temporary stdin file
    temp_files['stdin_fp'].close()


def _read_stdout_and_stderr(temp_files):
    try:
        with open(temp_files['stdout_path'], 'rb') as stdout_fp:
            stdout = stdout_fp.read()
    except:
        logging.exception('Failed to read file: {}'.format(
            temp_files['stdout_path']))
        raise

    try:
        with open(temp_files['stderr_path'], 'rb') as stderr_fp:
            stderr = stderr_fp.read()
    except:
        logging.exception('Failed to read file: {}'.format(
            temp_files['stderr_path']))
        raise

    return stdout, stderr


def _delete_temp_files(temp_files):
    try:
        os.unlink(temp_files['stdin_path'])
        os.unlink(temp_files['stdout_path'])
        os.unlink(temp_files['stderr_path'])
    except:
        logging.exception(('Failed to delete temporary files,' +
                           ' ignore now: {}').format(temp_files))


def _build_ssh_command(server_spec):
    """ Build SSH command.

    Arguments:
        server_spec (dict): Server spec.

    References:
        https://linux.die.net/man/1/ssh

    Returns:
        str: SSH command.
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


def _build_outer_command(ssh_command, temp_files):
    # Get temporary file paths
    stdin_path = temp_files['stdin_path']
    stdout_path = temp_files['stdout_path']
    stderr_path = temp_files['stderr_path']

    # Build the command
    outer_command = '{} \'bash -s\' < {} > {} 2> {}'.format(
        ssh_command, stdin_path, stdout_path, stderr_path)

    # Return the final command
    return outer_command
