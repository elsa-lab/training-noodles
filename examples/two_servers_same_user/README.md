# Example: Two Servers and Same User

This spec is very similar to the spec in *two_locals* example. If successfully run, `~/exp1.log` and `~/exp3.log` should be created on *server1*, and `~/exp2.log` should be created on *server2*.

You should prepare two servers to run this example. Please feel free to modify entries `server_default` and `servers` in the spec to specify your own servers. If you only have one server, please remove *server2* in the spec. Then all log files should be created on *server1*.

## Run

To run this example, use project root directory as working directory and execute the following:

```bash
noodles run examples/two_servers_same_user/spec.yml
```

## Clean

To remove all log files created by *run* commands, execute the following:

```bash
noodles clean examples/two_servers_same_user/clean.yml
```
