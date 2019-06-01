# Example: Two Servers and Same User

You should prepare two servers to run this example. Please feel free to modify entries `each_server` and `servers` in the spec to specify your own servers.

This spec is very similar to the spec in *two_locals* example. If successfully run, `~/exp1.log` and `~/exp3.log` should be created on *server1*, and `~/exp2.log` should be created on *server2*.

## Run

To run this example, use project root directory as working directory and execute the following:

```bash
noodles run examples/two_servers_same_user/spec.yml
```

To understand how the commands are executed, specify extra arguments which turn on verbose logging and debugging info:

```bash
noodles run examples/two_servers_same_user/spec.yml --verbose --debug
```
