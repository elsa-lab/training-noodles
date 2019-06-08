#!/bin/bash
#
# Handle errors and exit
#
# Reference: https://stackoverflow.com/a/185900

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

trap 'error ${LINENO}' ERR
