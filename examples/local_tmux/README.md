# Example: Local Tmux

This example runs a short Tmux session and a long Tmux session on local.

The short Tmux session would delay for 10 seconds and write the current time into `examples/local_tmux/output.log`. The long Tmux session would wait for the short Tmux session to finish, wait for 30 seconds, and delete the previous output file.

## Prerequisites

Please make sure `tmux` is installed on the local machine.

## Run

To run this example, use project root directory as working directory and execute the following:

```bash
noodles run examples/local_tmux/spec.yml
```

You would notice that `examples/local_tmux/output.log` is created after 10 seconds delay and deleted after 30 seconds.

## Stop

There are actually two Tmux sessions responsible for creation and deletion of the file. To kill the long Tmux session, open another terminal and execute the following immediately when the output file is created:

```bash
noodles stop "examples/local_tmux/spec.yml:Long Tmux"
```

Then the output file would never be deleted because the long Tmux session is killed after running the above command. To see the list of running Tmux sessions, execute the following:

```bash
tmux ls
```

## Clean

To remove the script files produced by *run* commands, execute the following:

```bash
noodles clean examples/local_tmux/clean.yml
```

`script1.sh` and `script2.sh` would be deleted afterwards.
