import json
import logging
import os
import subprocess

from training_noodles.utils import convert_values_to_strs


def run_command(command, stdin=None, extra_envs=None, wait=True):
    """ Run the command using bash.

    Arguments:
        command (str): Command to run.
        stdin (file object): Input stream. Set to "None" to use default stdin.
        extra_envs (dict): Extra environment variables.
        wait (bool): Whether to wait for the command to finish.

    Returns:
        p_obj: A "Popen" object.
    """
    # Wrap the command by bash
    command = 'bash -c "{}"'.format(command)

    # Convert environment variable values to strings
    extra_envs = convert_values_to_strs(extra_envs)

    # Print the command
    logging.debug('Run command: {}'.format(command))

    # Print the extra environment variables
    logging.debug(
        'Extra environment variables: {}'.format(json.dumps(extra_envs)))

    try:
        # Get default environment variables
        env = os.environ.copy()

        # Update with extra environment variables
        if extra_envs:
            env.update(extra_envs)

        # Run the program
        p_obj = subprocess.Popen(command, stdin=stdin, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, env=env)

        # Check whether to wait
        if wait:
            p_obj.wait()

        return p_obj
    except subprocess.CalledProcessError as e:
        logging.exception('Could not run the command: {}'.format(command))
        logging.error('RETURN_CODE: {}'.format(e.returncode))
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


def read_command_results(p_obj):
    """ Read command results.

    Read the raw stdout and stderr. Will raise error if "check_return_code" is
    on and return code is non-zero.

    Arguments:
        p_obj (Popen): The object given by "run_command" function.

    Returns:
        (Raw stdout, Raw stderr, Return code (int))
    """
    # Read stdout and stderr
    stdout, stderr = p_obj.communicate()

    # Read return code
    return_code = p_obj.returncode

    # Return the raw results and return code
    return stdout, stderr, return_code


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


def escape_command(command, quote='"'):
    # Replace all quotes by a backslash and a quote
    escaped_quote = '\\{}'.format(quote)

    return command.replace(quote, escaped_quote)
