from training_noodles.logging_utils import get_logger


class Logger:
    def __init__(self, name):
        # Save the name
        self.name = name

        # Initialize the logger
        self._init_logger()

    def debug(self, messages):
        # Flatten the messages
        flattened_message = self._flatten_messages(messages)

        # Log the debugging message
        self.logger.debug(flattened_message)

        # Return the flattened message
        return flattened_message

    def info(self, messages):
        # Flatten the messages
        flattened_message = self._flatten_messages(messages)

        # Log the info
        self.logger.info(flattened_message)

        # Return the flattened message
        return flattened_message

    def warning(self, messages):
        # Flatten the messages
        flattened_message = self._flatten_messages(messages)

        # Log the warning
        self.logger.warning(flattened_message)

        # Return the flattened message
        return flattened_message

    def error(self, messages):
        # Flatten the messages
        flattened_message = self._flatten_messages(messages)

        # Log the error
        self.logger.error(flattened_message)

        # Return the flattened message
        return flattened_message

    def exception(self, messages):
        # Flatten the messages
        flattened_message = self._flatten_messages(messages)

        # Log the exception
        self.logger.exception(flattened_message)

        # Return the flattened message
        return flattened_message

    def raise_error(self, messages):
        # Log the error and get the flattened messages
        flattened_message = self.error(messages)

        # Raise the error
        raise ValueError(flattened_message)

    def _init_logger(self):
        # Get the logger and save
        self.logger = get_logger(self.name)

    def _flatten_messages(self, messages):
        # Check the messages type
        if isinstance(messages, list):
            # Concatenate all messages and return
            return '\n'.join(messages)
        elif isinstance(messages, str):
            # Return the message
            return messages
        else:
            raise ValueError(
                'Unknown messages type "{}"'.format(type(messages)))
