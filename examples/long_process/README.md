# Example: Long Process

This example shows the ability to see the intermediate results of any long process on the remote servers.

We simply print the numbers in a range per second on the remote server. The log files will be updated often with new printed numbers.

An alternative to this method is to use Tmux to run long processes. It has many [benefits](https://www.bugsnag.com/blog/benefits-of-using-tmux) over this method. See [examples/train_tensorflow_examples](../../examples/train_tensorflow_examples/README.md).

## Run

To run this example, use project root directory as working directory and execute the following:

```bash
noodles run examples/long_process/spec.yml
```

After running the above command, open the log files `exp1.stdout.log` and `exp2.stdout.log` to see the intermediate results. Make sure to refresh the files often to see the updated results.

## Clean

To remove the log files produced by *run* commands, execute the following:

```bash
noodles clean examples/long_process/clean.yml
```

`exp1.stdout.sh` and `exp2.stdout.sh` would be deleted afterwards.
