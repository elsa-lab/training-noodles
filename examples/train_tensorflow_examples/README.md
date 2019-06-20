# Example: Train TensorFlow Examples

This example runs three different TensorFlow examples on two different remote servers.

[TensorFlow examples](https://github.com/aymericdamien/TensorFlow-Examples) will be downloaded on remote servers and run.

The general procedure of the 1st phase *Initialize Experiments* goes like this:

1. Find one available server which has no lock file
2. Create a lock file to avoid race condition
3. Create a marker file for Noodles to find the same server in latter experiments
4. Clone [TensorFlow-Examples](https://github.com/aymericdamien/TensorFlow-Examples) from GitHub
5. Create a new conda environment

and the 2nd phase *Run Experiments*:

1. Activate the created conda environment
2. Install TensorFlow in the activated conda environment
3. Create a detached Tmux session to run the experiment

and finally the 3rd phase *Download Experimental Results*:

1. Run `scp` on local machine to download log files produced by the experiment
2. Remote the lock file

You should prepare two servers to run this example. Please feel free to modify entries `server_default` and `servers` in the spec to specify your own servers. If you only have one server, please remove *server2* in the spec.

## Prerequisites

Please make sure each server meets the following requirements:

1. Have installed [Anaconda](https://www.anaconda.com/distribution/) at `$HOME/anaconda3`
2. The conda environment `noodles_test` doesn't exist (Use `conda env list` to check)
3. Can run TensorFlow with Python 3.6 properly in an Anaconda environment
4. Can use `git` to clone repositories properly
5. Have installed `tmux`

## Run

To run this example, use project root directory as working directory and execute the following:

```bash
noodles run examples/train_tensorflow_examples/spec.yml
```

It may take a while for each phase to complete. After a successful execution, you should find 6 log files (`tensorflow_results.*.log`) downloaded in the directory `examples/train_tensorflow_examples`. STDOUT and STDERR outputs of all experiments (`commands_results.*.log`) are written into another 18 log files in the directory `examples/train_tensorflow_examples`.

## Automatically Clean

To undo everything done by *run* commands, execute the following:

```bash
noodles clean examples/train_tensorflow_examples/clean.yml
```

Note that you should only execute the above command after a successful *run*. Otherwise see subsection [Manually Clean](#manually-clean) for cleaning manually.

## Manually Clean

If something went wrong in the middle and you would like to redo everything done by an unsuccessful *run*, execute the following on each server:

```bash
CONDA_DIR=$HOME/anaconda3; CONDA_ENV_NAME=noodles_test; TMUX_SESSION_PREFIX=test; tmux kill-ses -t $TMUX_SESSION_PREFIX/exp1; tmux kill-ses -t $TMUX_SESSION_PREFIX/exp2; tmux kill-ses -t $TMUX_SESSION_PREFIX/exp3; $CONDA_DIR/bin/conda remove -y -n $CONDA_ENV_NAME --all; rm -rf ~/TensorFlow-Examples; rm -f ~/tensorflow_results.*.log; rm -f ~/marker_exp*.txt; rm -f ~/noodles.lock; rm -f ~/error.log
```

and execute the following on local machine:

```bash
LOCAL_DIR=examples/train_tensorflow_examples; rm -f $LOCAL_DIR/*.log; rm -f $LOCAL_DIR/noodles_status.yml; rm -f $LOCAL_DIR/error.log
```
