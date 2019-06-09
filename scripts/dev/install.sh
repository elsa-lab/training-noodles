#!/bin/bash
#
# Install the package in development mode

# Handle errors
source scripts/dev/includes/error_handling.sh

# Print the goal of this script
echo "Install the package in development mode"

# Install the package in development mode
pip install -e .

# Print success message
echo "Successfully installed the package in development mode"
