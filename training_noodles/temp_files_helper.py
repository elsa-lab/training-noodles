import os
import pathlib
import tempfile

from training_noodles.logger import Logger


class TempFilesHelper:
    """ Temporary files helper.
    """

    def __init__(self, closes):
        """ Initialize the instance.

        Arguments:
            closes (dict): Closing file pointers. The key is the stream name
            and the value is a boolean indicating whether to close the file
            pointer after creating the corresponding temporary file.
        """
        # Save indicators of closing file pointers
        self.closes = closes

        # Set the streams
        self.streams = ['stdin', 'stdout', 'stderr']

        # Create a logger
        self.logger = Logger('temp')

    def create_temp_files(self, user_files):
        """ Create temporary files.

        Arguments:
            user_files (dict): User file paths. If a stream name exists in the
            dict as the key, the corresponding temporary file won't be created.

        Returns:
            dict: Temporary files. The key is stream name and the value is a
                dict(fp, path).
        """

        # Initialize the results
        temp_files = {}

        # Iterate each stream
        for stream in self.streams:
            # Check whether the user file exists
            user_path = user_files.get(stream, None)

            # Only create the temporary file when the user file doesn't exist
            if user_path is None:
                # Get whether to close the file pointer
                close = self.closes[stream]

                # Create the temporary file
                fp, path = self._create_temp_file(stream, close)

                # Save the file pointer, path and temporary marker
                temp_files[stream] = dict(fp=fp, path=path)

        # Return the results
        return temp_files

    def delete_temp_files(self, temp_files):
        # Iterate each stream
        for stream, temp_file in temp_files.items():
            # Get the file pointer and path
            fp, path = temp_file['fp'], temp_file['path']

            # Close the file pointer
            fp.close()

            # Try to delete the temporary file
            try:
                os.unlink(path)
            except:  # pragma: no cover
                # Only log the exception, don't raise it
                self.logger.exception(('Failed to delete {} temporary file,' +
                                       ' ignore now: {}').format(stream, path))

    def _create_temp_file(self, output_type, close):
        # Create a temporary file
        try:
            # Set the suffix
            suffix = '.{}'.format(output_type)

            # Create a named temporary file
            fp = tempfile.NamedTemporaryFile(
                delete=False, prefix='training_noodles.', suffix=suffix)
        except:  # pragma: no cover
            self.logger.exception('Failed to create temporary file')
            raise

        # Check whether to close the file
        if close:
            fp.close()

        # Convert the paths to POSIX-style paths
        path = pathlib.Path(fp.name).as_posix()

        # Log the temporary files
        self.logger.debug('Created temporary file for {}: {}'.format(
            output_type, path))

        # Return the temporary file pointer and path
        return fp, path
