#!/bin/bash
#
# Restore everything back to a clean slate so that
# 1. The package is not installed
# 2. PyPI build files don't exist

# Handle errors
source scripts/dev/includes/error_handling.sh

# Print the goal of this script
echo "Clean unnecessary files"

# Uninstall the package
source scripts/dev/uninstall.sh

# Remove distribution files
source scripts/dev/remove_dist.sh
