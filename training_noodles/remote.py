import logging

from training_noodles.cli import (
    decode_output, run_command, read_command_results)


def run_commands_over_ssh(commands, server_spec):
    """ Run commands over SSH.

    Arguments:
        commands (str or list): A single command (str) or list of commands.
        server_spec (dict): The server spec.

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

    # Build SSH command
    ssh_command = _build_ssh_command(server_spec)

    # Build remote command
    remote_command = _build_remote_command(ssh_command, commands)

    # Execute the remote command
    p_obj = run_command(remote_command)

    # Read the command results
    stdout, _, _ = read_command_results(p_obj)

    # Return the results
    return stdout


def _build_ssh_command(server_spec):
    """ Build SSH command.

    Args: server_spec (dict): Server spec.

    References:
        https://linux.die.net/man/1/ssh

    Returns:
        str: SSH command.
    """
    # Check whether the hostname is localhost
    if server_spec.get('hostname', None) == 'localhost':
        return None
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
            options.extend(['-p', port])

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
        ssh_command = 'ssh {}'.format(option_command)

        # Return the SSH command
        return ssh_command


def _build_remote_command(ssh_command, remote_commands):
    # Concatenate the remote commands by newlines
    remote_command = '\n'.join(remote_commands)

    # Check whether the target is localhost
    if ssh_command is None:
        return remote_command
    else:
        return '{} {}'.format(ssh_command, remote_command)
