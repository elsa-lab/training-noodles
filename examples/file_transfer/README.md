# Example: File Transfer

This example executes two experiments on servers. Each server runs one experiment. The general procedure goes like the following:

1. Upload scripts to servers
2. Run the scripts on servers
3. Download the results from servers

The requirement `get_random_number` makes Noodles deploy experiment *Upload experiment 1* to a randomly chosen server. To let `scp` know where to upload the script, Noodles provides the environment variable `NOODLES_SERVER_AUTHORITY` which has the form `<username>@<hostname>`. It then uses the uploaded script on servers as a way to identify which server to run and download.

You should prepare two servers to run this example. Please feel free to modify entries `each_server` and `servers` in the spec to specify your own servers. If you only have one server, please remove *server2* in the spec.

## Prerequisites

Please make sure `scp` is installed on the localhost.

## Run

To run this example, use project root directory as working directory and execute the following:

```bash
noodles run examples/file_transfer/spec.yml
```

Two log files `exp1_result.log` and `exp2_result.log` would be downloaded from servers and put into the directory `examples/file_transfer/`.

`exp1_result.log` would be the CPU information of *server1* (or *server2*) and `exp2_result.log` would be the memory information of *server2* (or *server1*) at the time of execution of experiments *Run experiment 1* and *Run experiment 2* respectively.

Note that you should *clean* the experimental results (See subsection [Clean](#clean)) before you *run* this example again.

## Clean

To remove the scripts and log files on servers as well as the log files on local, execute the following:

```bash
noodles clean examples/file_transfer/clean.yml
```

Note that it would hang if there are no uploaded scripts on servers (e.g., If you haven't *run* the `spec.yml`) because it would keep finding the scripts on servers due to `find_experiment` requirement in `spec.yml`.
