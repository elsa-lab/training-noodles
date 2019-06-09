#!/bin/bash
#
# Test functions to be used

# Handle errors
source scripts/dev/includes/error_handling.sh

# Include constants
source scripts/dev/includes/constants.sh

clean_old_stuff() {
    echo "Clean old stuff"

    # Remove the old Conda environment
    conda remove -y -n "$TEST_CONDA_ENV_NAME" --all

    # Remove the test directory
    rm -rf "$TEST_DIR"
}

set_up_test_env() {
    echo "Set up test environment"

    # Create a Conda environment
    conda create -y -n "$TEST_CONDA_ENV_NAME" python=$TEST_PYTHON_VERSION

    # Activate the Conda environment
    source activate "$TEST_CONDA_ENV_NAME"

    # Create a new temporary directory
    mkdir -p "$TEST_DIR"

    # Copy the examples to the test directory
    cp -r "examples/" "$TEST_DIR/examples/"
}

run_tests() {
    echo "Run tests"

    # Change the working directory to the test directory
    cd "$TEST_DIR"

    # Run the examples

    echo "Run examples/error_handling"
    noodles run examples/error_handling/spec.yml
    noodles clean examples/error_handling/clean.yml

    echo "Run examples/two_locals"
    noodles run examples/two_locals/spec.yml
    noodles clean examples/two_locals/clean.yml

    # Change the working directory back to the root directory
    cd -
}

tear_down_test_env() {
    echo "Tear down test environment"

    # Remove the test directory
    rm -rf "$TEST_DIR"

    # Deactivate the Conda environment
    source deactivate

    # Remove the Conda environment
    conda remove -y -n "$TEST_CONDA_ENV_NAME" --all
}
