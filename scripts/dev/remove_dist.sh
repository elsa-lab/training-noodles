#!/bin/bash
#
# Remove the distribution files

# Handle errors
source scripts/dev/includes/error_handling.sh

# Print the goal of this script
echo "Remove the distribution files"

# Remove directories created by PyPI
rm -rf build/
rm -rf dist/

# Print success message
echo "Successfully removed the distribution files"
