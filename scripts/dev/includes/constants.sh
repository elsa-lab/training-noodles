#!/bin/bash
#
# Set the constants

# Handle errors
source scripts/dev/includes/error_handling.sh

# Package name
PACKAGE_NAME=training_noodles

# Conda environment name to create for testing
TEST_CONDA_ENV_NAME=test_noodles

# The Python versions used by the Conda environment
TEST_PYTHON_VERSIONS=( 3.5 3.6 3.7 )

# The directory to run the tests
TEST_DIR=temp
