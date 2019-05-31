# Sample: Two Locals

You can run this sample without servers. Because we use `hostname: localhost` in the spec `two_locals.yml`, noodles would run all the commands on localhost without SSH.

In the spec, "Experiment 1" would write a hello message into `examples/two_locals/exp1.log`, while "Experiment 2" and "Experiment 3" would write the time of execution into `exp2.log` and `exp3.log` under the directory `examples/two_locals/`. Moreover, "Experiment 3" requires the CPU usage to be greater than or equal to 0 (always true), which would make noodles measure CPU usage on the servers (actually localhosts) and deploy the experiment to one of the satisfied servers.

## Run

To run this sample, use project root directory as working directory and execute the following:

```bash
noodles run examples/two_locals/two_locals.yml
```

You would see three `.log` files created under the directory `examples/two_locals/`, which are the results of the experiment commands in the spec.

To understand how the commands are executed, specify extra arguments which turn on verbose logging and debugging info:

```bash
noodles run examples/two_locals/two_locals.yml --verbose --debug
```
