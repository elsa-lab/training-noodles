# Example: Two Locals

This is a simple example which writes three log files on local machine.

Please see the spec file `spec.yml`. *Experiment 1* would write a hello message into `examples/two_locals/exp1.log`, while *Experiment 2* and *Experiment 3* would write the time of execution into `exp2.log` and `exp3.log` under the directory `examples/two_locals/`.

Moreover, *Experiment 3* requires the CPU usage to be greater than or equal to 0 (which is always true). Noodles would measure CPU usage on the servers (which are local machines in this case) and deploy the experiment to one of the satisfied servers (i.e., local machines).

You can run this example without servers. Because we use `hostname: localhost` in the spec `spec.yml`, Noodles would run all the commands on local machines without SSH. However, you can easily switch the deployment targets to remote servers by changing the server info in the spec. See another example [examples/two_servers_same_user](../../examples/two_servers_same_user) for more information.

## Run

To run this example, use project root directory as working directory and execute the following:

```bash
noodles run examples/two_locals/spec.yml
```

You would see files `exp1.log`, `exp2.log` and `exp3.log` created under the directory `examples/two_locals/`, which are the results of the experiment commands written in the spec.

### 10 Seconds Delay

You would notice there is a 10 second delay between deployments of *Experiment 2* and *Experiment 3* due to the option `round_interval` in the spec. We generally want to keep a long delay between each deployment round because the system metrics would drastically change after the previous deployment round. In this example, if we deploy too quickly (e.g., set `round_interval` to 0), the CPU usage might still be low in the early stages of training, which would make Noodles deploy lots of experiments in a short time and result in higher CPU usage than expected.

### Choose Only Some Experiments

To run only *Experiment 2* and *Experiment 3*, specify them as the following:

```bash
noodles run "examples/two_locals/spec.yml:Experiment 2,Experiment 3"
```

### See Details of Executions

To understand how the commands are executed, specify extra arguments which turn on verbose logging and debugging info:

```bash
noodles run examples/two_locals/spec.yml --verbose --debug
```

## Clean

To remove all log files created by *run* commands, execute the following:

```bash
noodles clean examples/two_locals/clean.yml
```
