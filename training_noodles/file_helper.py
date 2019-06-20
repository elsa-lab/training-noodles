import os

import pkg_resources

from training_noodles.logger import Logger


class FileHelper:
    def __init__(self):
        # Create a logger
        self.logger = Logger('file')

    def read_file_contents(self, path, mode='rb', offset=0):
        try:
            # Open the file in binary mode
            with open(path, mode) as fp:
                # Offset the stream position
                fp.seek(offset)

                # Read the contents and return
                return fp.read()
        except:
            self.logger.exception('Could not read the file "{}"'.format(path))
            raise

    def read_file_size(self, path):
        try:
            # Read the file size and return
            return os.path.getsize(path)
        except:
            self.logger.exception(
                'Could not read the file size from the file "{}"'.format(path))
            raise

    @staticmethod
    def get_resource_path(package, resource_name):
        # Build the requirement
        requirement = pkg_resources.Requirement.parse(package)

        # Get the resource filename and return
        return pkg_resources.resource_filename(requirement, resource_name)
