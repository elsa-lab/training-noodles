import json
import os
import subprocess

from training_noodles.data_structure_utils import convert_values_to_strs
from training_noodles.logger import Logger


class CLI:
    """ Command line interface helper.

    This class runs command on the local machine and reads the results.
    """

    def __init__(self, shell_string='bash -c'):
        """ Initialize the instance.

        Arguments:
            shell_string (str): Shell command to read from string (e.g.,
                "bash -c").
        """

        # Save the shell command to read from string
        self.shell_string = shell_string

        # Create a logger
        self.logger = Logger('cli')

    def run_command(self, command, stdin=None, extra_envs=None, wait=True):
        """ Run the command using the shell command.

        Arguments:
            command (str): Command to run.
            stdin (file object): Input stream. Set to "None" to use default
                stdin.
            extra_envs (dict): Extra environment variables.
            wait (bool): Whether to wait for the command to finish.

        Returns:
            Popen: A "Popen" object.
        """
        # Wrap the command by the shell command to ensure the command is
        # executed by the shell
        command = '{} "{}"'.format(self.shell_string, command)

        # Convert environment variable values to strings
        extra_envs = convert_values_to_strs(extra_envs)

        # Log the command
        self.logger.debug('Run command: {}'.format(command))

        # Log the extra environment variables
        self.logger.debug(
            'Extra environment variables: {}'.format(json.dumps(extra_envs)))

        try:
            # Get default environment variables
            env = os.environ.copy()

            # Update with extra environment variables
            if extra_envs:
                env.update(extra_envs)

            # Run the program
            p_obj = subprocess.Popen(command, stdin=stdin,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, shell=True,
                                     env=env)

            # Check whether to wait
            if wait:
                p_obj.wait()

            return p_obj
        except subprocess.CalledProcessError as e:
            self.logger.raise_error([
                'Could not run the command: {}'.format(command),
                'RETURN_CODE: {}'.format(e.returncode),
                'STDOUT=>\n{}'.format(self.decode_output(e.stdout)),
                'STDERR=>\n{}'.format(self.decode_output(e.stderr)),
            ])
        except:
            self.logger.raise_error('Unknown error occurred')

    def wait_command(self, p_obj):
        """ Wait for the command to finish.

        Arguments:
            p_obj (Popen): The object given by "run_command" function.
        """
        p_obj.wait()

    def read_results(self, p_obj):
        """ Read command results.

        Read the raw stdout and stderr. Will raise error if "check_return_code"
        is on and return code is non-zero.

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

    @staticmethod
    def decode_output(output):
        """ Decode the output.

        Try to return the decoded output, if it fails, return the original
        output.

        Arguments:
            output: Raw output which can be stdout or stderr.

        Returns:
            The decoded output.
        """
        try:
            return output.decode('utf-8')
        except UnicodeDecodeError:
            return output

    @staticmethod
    def escape_command(command, quote='"'):
        """ Escape the command.

        The quotes X in the command will be replaced by "\\X".

        Arguments:
            quote (str): The quote to escape.

        Returns:
            str: Escaped command.
        """
        # Replace all quotes by a backslash and a quote
        escaped_quote = '\\{}'.format(quote)

        return command.replace(quote, escaped_quote)
