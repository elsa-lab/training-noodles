import logging
import os
import subprocess
import sys


def decode_output(output):
    """ Decode the output.

    Try to return the decoded output, if it fails, return the original output.

    Arguments:
        output: Raw output which can be stdout or stderr.

    Returns:
        The decoded output.
    """
    try:
        return output.decode('utf-8')
    except UnicodeDecodeError:
        return output


def run_command(command_or_parts, extra_env=None, wait=True):
    """ Run the command using bash.

    Arguments:
        command_or_parts (str or list): Single command as str or command parts
            in list.
        extra_env (dict): Extra environment variables.
        wait (bool): Whether to wait for the command to finish.

    Returns:
        p_obj: A "Popen" object.
    """
    # Convert the command arguments to string
    if isinstance(command_or_parts, str):
        command = command_or_parts
    elif isinstance(command_or_parts, list):
        command = ' '.join(command_or_parts)
    else:
        message = 'Unknown type of command arguments'
        logging.error(message)
        raise ValueError(message)

    # Print the command
    logging.debug('Run command: {}'.format(command))

    # Determine executable for the current platform
    if sys.platform == 'win32':
        executable = 'bash.exe'
    else:
        executable = 'bash'

    try:
        # Get default environment variables
        env = os.environ.copy()

        # Update with extra environment variables
        if extra_env:
            env.update(extra_env)

        # Run the program
        p_obj = subprocess.Popen([executable, '-c', command],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 env=env)

        # Check whether to wait
        if wait:
            p_obj.wait()

        return p_obj
    except subprocess.CalledProcessError as e:
        logging.exception('Could not run the command: {}'.format(command))
        logging.error('RETURNCODE: {}'.format(e.returncode))
        logging.error('STDOUT=>\n{}'.format(decode_output(e.stdout)))
        logging.error('STDERR=>\n{}'.format(decode_output(e.stderr)))
        raise
    except:
        logging.exception('Unknown error occurred')
        raise


def wait_command(p_obj):
    """ Wait for the command to finish.

    Arguments:
        p_obj (Popen): The object given by "run_command" function.
    """
    p_obj.wait()


def read_command_results(p_obj, check_return_code=True):
    """ Read command results.

    Read the raw stdout and stderr. Will raise error if "check_return_code" is
    on and return code is non-zero.

    Arguments:
        p_obj (Popen): The object given by "run_command" function.
        check_return_code (bool): Whether to check return code.

    Returns:
        (Raw stdout, Raw stderr, Return code (int))
    """
    # Read stdout and stderr
    stdout, stderr = p_obj.communicate()

    # Read return code
    return_code = p_obj.returncode

    # Check return code
    if check_return_code and return_code != 0:
        # Log stdout and stderr
        logging.error('STDOUT=>\n{}'.format(decode_output(stdout)))
        logging.error('STDERR=>\n{}'.format(decode_output(stderr)))

        # Raise error
        message = 'Returned non-zero return code {}'.format(return_code)
        logging.error(message)
        raise ValueError(message)

    return stdout, stderr, return_code
