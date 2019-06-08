#!/bin/bash
#
# Uninstall the package

# Handle errors
source scripts/dev/includes/error_handling.sh

# Include constants
source scripts/dev/includes/constants.sh

# Print the goal of this script
echo "Uninstall the package $PACKAGE_NAME"

# Uninstall the package
pip uninstall -y "$PACKAGE_NAME"
