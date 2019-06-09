#!/bin/bash
#
# Test the package in a new Anaconda environment

# Handle errors
source scripts/dev/includes/error_handling.sh

# Include constants
source scripts/dev/includes/constants.sh

# Include test functions
source scripts/dev/includes/tests.sh

# Print the goal of this script
echo "Test the editable package \"$PACKAGE_NAME\""

# Test each Python version
for TEST_PYTHON_VERSION in "${TEST_PYTHON_VERSIONS[@]}"
do
    # Print the Python version
    echo "Test with Python $TEST_PYTHON_VERSION"

    # Clean old stuff
    clean_old_stuff

    # Set up test test environment
    set_up_test_env

    # Install the package in development mode
    source scripts/dev/install.sh

    # Run the tests
    run_tests

    # Tear down the test environment
    tear_down_test_env
done

# Print success message
echo "Successfully tested the editable package \"$PACKAGE_NAME\""
