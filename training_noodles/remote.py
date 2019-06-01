import logging
import os
import pathlib
import tempfile

from training_noodles.cli import (
    decode_output, run_command, read_command_results)


def run_commands_over_ssh(commands, server_spec):
    """ Run commands over SSH.

    Arguments:
        commands (str or list): A single command (str) or list of commands.
        server_spec (dict): The server spec.

    Returns:
        Raw stdout.
    """
    # Convert to list of commands for consistency
    if isinstance(commands, str):
        commands = [commands]
    elif isinstance(commands, list):
        commands = commands
    else:
        message = 'Unknown type of command arguments'
        logging.error(message)
        raise ValueError(message)

    # Create temporary files
    temp_files = _create_temp_files()

    # Build SSH command
    ssh_command = _build_ssh_command(server_spec)

    # Concatenate commands by newlines
    command = '\n'.join(commands)

    # Write command to temporary stdin file
    _write_command_to_stdin(command, temp_files)

    # Build remote command
    remote_command = _build_remote_command(ssh_command, temp_files)

    # Execute the remote command
    p_obj = run_command(remote_command)

    # Read the command results (just for checking errors)
    read_command_results(p_obj)

    # Read stdout and stderr from temporary files
    stdout, stderr = _read_stdout_and_stderr(temp_files)

    # Delete temporary files
    _delete_temp_files(temp_files)

    # Return the results
    return stdout, stderr


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
        return 'bash -c'
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


def _build_remote_command(ssh_command, temp_files):
    # Get temporary file paths
    stdin_path = temp_files['stdin_path']
    stdout_path = temp_files['stdout_path']
    stderr_path = temp_files['stderr_path']

    # Build the command
    remote_command = '{} \'bash -s\' < {} > {} 2> {}'.format(
        ssh_command, stdin_path, stdout_path, stderr_path)

    # Return the remote command
    return remote_command
