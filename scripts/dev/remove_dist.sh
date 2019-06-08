#!/bin/bash
#
# Remove distribution files

# Handle errors
source scripts/dev/includes/error_handling.sh

# Remove directories created by PyPI
rm -rf build/
rm -rf dist/
