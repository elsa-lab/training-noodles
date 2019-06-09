#!/bin/bash
#
# Handle errors and exit
#
# References:
# https://stackoverflow.com/a/185900
# https://superuser.com/a/257591

# Make ERR trap inherited in functions
set -o errtrace

# Error handler
error() {
  local parent_lineno="$1"
  local message="$2"
  local code="${3:-1}"
  if [[ -n "$message" ]] ; then
    echo "ERROR: Error on or near line ${parent_lineno}: ${message}; exiting with status ${code}" >&2
  else
    echo "ERROR: Error on or near line ${parent_lineno}; exiting with status ${code}" >&2
  fi
  exit "${code}"
}

# Trap the errors
trap 'error ${LINENO}' ERR
