# Changelog

## 1.2.2 (2020-07-26)

* Fix missing argument error when calling response commands

## 1.2.1 (2020-07-23)

* Avoid running response commands recursively due to response commands errors
* Log messages first before running response commands

## 1.2.0 (2019-07-14)

* Changed the default metric output from percentage to a range between 0.0-1.0

## 1.1.1 (2019-07-14)

* Added requirement `cuda_memory_usage` in the default spec
* Removed requirement `cuda_memory_utilization` in the default spec

## 1.1.0 (2019-06-20)

* Added spec option `commands_interval` to add a delay between command executions
* Added spec option `error_handlers[].commands` for executing response commands when errors occur
* Added spec options `shell_string` and `shell_stdin` for customizing the shell commands to read from string and STDIN
* Add command type and user spec path in the output file of `write_status_to`

## 1.0.16 (2019-06-20)

* Transferred the repo to elsa-lab

## 1.0.15 (2019-06-20)

* Fixed the runner might ignore "retry" action when the commands are separated into command groups for local and remote executions
* Changed the logging formats
* Added `cpu_load` requirement in the default spec

## 1.0.14 (2019-06-15)

* Fixed null metric problem when the server has been deployed with some experiment
* Fixed number of successful deployments not increased if there are no commands
* Log the skipped server when the server has been deployed

## 1.0.13 (2019-06-14)

* Fixed some operators in requirement expression are not recognized
* Fixed some environment variables are not evaluated correctly

## 1.0.12 (2019-06-14)

* Fixed environment variables order may not be preserved (`experiment.envs` first, then `experiment_default.envs`)

## 1.0.11 (2019-06-14)

* Fixed environment variables order may not be preserved (`experiment.envs` first, then `experiment_default.envs`)

## 1.0.10 (2019-06-14)

* Fixed splitting scheme so that scheme can only contain word characters (e.g., "local:ls" has a scheme but "scp user@host:~/file" doesn't)

## 1.0.9 (2019-06-11)

* Fixed command execution error on Linux

## 1.0.8 (2019-06-11)

* Fixed dependency checking
* Fixed deployed server not being removed from **S** if the error handling action is `continue`
* Make the experiment names ordered in Noodles status output

## 1.0.7 (2019-06-11)

* Fixed division by zero error when there are no experiments
* Fixed errors when the spec file is empty
* Added default name for `server_default`
* Changed Noodles status output format from Title Case to Sentence case
* Removed extra environment variable `NOODLES_SERVER_PRIVATE_KEY_PATH`

## 1.0.6 (2019-06-09)

* Updated README

## 1.0.5 (2019-06-08)

* Updated README

## 1.0.4 (2019-06-08)

* Fixed images in README not showing in PyPI webpage

## 1.0.3 (2019-06-08)

* Fixed default spec path not found error

## 1.0.2 (2019-06-08)

* Fixed Python module not found error

## 1.0.1 (2019-06-08)

* Fixed Python module not found error

## 1.0.0 (2019-06-08)

* Added the initial project
