import os
import tempfile
import unittest

# Testing targets
from training_noodles.file_helper import FileHelper


class TestReadFileContents(unittest.TestCase):
    def setUp(self):
        # Create a new file helper
        self.file_helper = FileHelper()

        # Initialize the contents
        self.contents = ''

        # Initialize the offset
        self.offset = 0

    def test_empty(self):
        self.contents = ''
        self.expected_contents = self.contents

    def test_simple(self):
        self.contents = 'abc 123'
        self.expected_contents = self.contents

    def test_multiline(self):
        for i in range(100):
            self.contents += 'line {}\n'.format(i)

        self.expected_contents = self.contents

    def test_multiline_with_offset(self):
        lines = []

        for i in range(100):
            line = 'line {}\n'.format(i)
            lines.append(line)
            self.contents += line

        # Set the offset at the line 50
        self.offset = sum(map(len, lines[:50]))

        # Set the expected contents to be lines 50-99
        self.expected_contents = ''.join(lines[50:])

    def tearDown(self):
        # Create a temporary file
        fp = tempfile.NamedTemporaryFile(delete=False)

        # Encode the contents
        encoded_contents = self.contents.encode('utf-8')

        # Encode the expected contents
        encoded_expected_contents = self.expected_contents.encode('utf-8')

        # Write the contents
        fp.write(encoded_contents)

        # Close the file
        fp.close()

        # Read the file contents
        read_contents = self.file_helper.read_file_contents(
            fp.name, offset=self.offset)

        # Check whether the contents are the same
        self.assertEqual(read_contents, encoded_expected_contents)

        # Delete the file
        os.unlink(fp.name)


class TestReadFileSize(unittest.TestCase):
    def setUp(self):
        # Create a new file helper
        self.file_helper = FileHelper()

        # Initialize the contents
        self.contents = ''

        # Initialize the expected file size
        self.expected_file_size = 0

    def test_empty(self):
        self.contents = ''
        self.expected_file_size = 0

    def test_simple(self):
        self.contents = 'abc 123'
        self.expected_file_size = 7

    def test_multiline(self):
        for i in range(10):
            line = 'line #{}\n'.format(i + 1)
            self.contents += line
            self.expected_file_size += len(line)

    def tearDown(self):
        # Create a temporary file
        fp = tempfile.NamedTemporaryFile(delete=False)

        # Encode the contents
        encoded_contents = self.contents.encode('utf-8')

        # Write the contents
        fp.write(encoded_contents)

        # Close the file
        fp.close()

        # Read the file size
        file_size = self.file_helper.read_file_size(fp.name)

        # Check whether the contents are the same
        self.assertEqual(file_size, self.expected_file_size)

        # Delete the file
        os.unlink(fp.name)


class TestGetResourcePath(unittest.TestCase):
    def test_defaults(self):
        self.package = 'training-noodles'
        self.resource_name = 'training_noodles/specs/defaults.yml'

    def tearDown(self):
        # Get the resource path
        path = FileHelper.get_resource_path(self.package, self.resource_name)

        # Open the file
        with open(path, 'r'):
            pass
