#!/bin/bash
#
# Uninstall the package

# Handle errors
source scripts/dev/includes/error_handling.sh

# Include constants
source scripts/dev/includes/constants.sh

# Uninstall the package
pip uninstall -y "$PACKAGE_NAME"
