#!/bin/bash
#
# Install the package in development mode

# Handle errors
source scripts/dev/includes/error_handling.sh

# Install the package in development mode
pip install -e .
