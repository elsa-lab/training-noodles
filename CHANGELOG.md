# Changelog

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
