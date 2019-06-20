import os
import unittest

# Testing targets
from training_noodles.temp_files_helper import TempFilesHelper


class TestCreateTempFiles(unittest.TestCase):
    def setUp(self):
        # Set whether to close the file pointers
        closes = dict(stdin=False, stdout=True, stderr=True)

        # Create a new temp files helper
        self.temp_files_helper = TempFilesHelper(closes)

    def test_no_user_files(self):
        self.user_files = {}
        self.expected_streams = ['stdin', 'stdout', 'stderr']

    def test_stdout_user_file(self):
        self.user_files = {
            'stdout': '/some/nonexistent/path',
        }
        self.expected_streams = ['stdin', 'stderr']

    def test_stdout_and_stderr_user_files(self):
        self.user_files = {
            'stdout': '/some/nonexistent/path/stdout.log',
            'stderr': '/some/nonexistent/path/stderr.log',
        }
        self.expected_streams = ['stdin']

    def tearDown(self):
        # Create temporary files
        temp_files = self.temp_files_helper.create_temp_files(self.user_files)

        # Check whether the keys are the same as the expected streams
        sorted_keys = sorted(temp_files.keys())
        sorted_expected_streams = sorted(self.expected_streams)
        self.assertEqual(sorted_keys, sorted_expected_streams)

        # Iterate each expected stream
        for stream in self.expected_streams:
            # Get the temporary file object
            temp_file = temp_files[stream]

            # Get the file pointer and path
            fp, path = temp_file['fp'], temp_file['path']

            # Write something to the file pointer if it's STDIN
            if stream == 'stdin':
                fp.write('foo bar'.encode('utf-8'))
                fp.close()

            # Check whether the path exists
            self.assertTrue(os.path.exists(path))

            # Delete the temporary file
            os.unlink(path)


class TestDeleteTempFiles(unittest.TestCase):
    def setUp(self):
        # Set whether to close the file pointers
        closes = dict(stdin=False, stdout=True, stderr=True)

        # Create a new temp files helper
        self.temp_files_helper = TempFilesHelper(closes)

    def test_no_user_files(self):
        self.user_files = {}
        self.expected_streams = ['stdin', 'stdout', 'stderr']

    def test_stdout_user_file(self):
        self.user_files = {
            'stdout': '/some/nonexistent/path',
        }
        self.expected_streams = ['stdin', 'stderr']

    def test_stdout_and_stderr_user_files(self):
        self.user_files = {
            'stdout': '/some/nonexistent/path/stdout.log',
            'stderr': '/some/nonexistent/path/stderr.log',
        }
        self.expected_streams = ['stdin']

    def tearDown(self):
        # Create temporary files
        temp_files = self.temp_files_helper.create_temp_files(self.user_files)

        # Delete the temporary files
        self.temp_files_helper.delete_temp_files(temp_files)

        # Iterate each expected stream
        for stream in self.expected_streams:
            # Get the temporary file object
            temp_file = temp_files[stream]

            # Get the path
            path = temp_file['path']

            # Check whether the path no longer exists
            self.assertFalse(os.path.exists(path))
