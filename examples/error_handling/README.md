# Example: Error Handling

This example specifies an nonexistent server in the spec purposely to test whether Noodles can handle errors properly.

The error handler *Ignore SSH resolve hostname error* in the spec would ignore any error which causes the `ssh` to return error code 255 and produces the STDERR error matching the regular expression.

You should prepare a server to run this example. Please feel free to modify entries `server_default` and `servers` in the spec to specify your own servers.

## Run

To run this example, use project root directory as working directory and execute the following:

```bash
noodles run examples/error_handling/spec.yml
```

Noodles would try to deploy each experiment to a different server, but one deployment would fail in each deployment round because one of the servers is nonexistent. Noodles would retry to deploy the failed experiment latter because we specify `retry` action in the error handler *Ignore SSH resolve hostname error*.

A status file `noodles_status.yml` would also be created in the directory `examples/error_handling` before the first deployment and updated after each deployment. If Noodles has to be shut down due to some unexpected errors, the status file can be very helpful. `Undeployed experiments (For command)` in the status file can be used as the filter string for another Noodles run.

## Clean

To remove the Noodles status file, execute the following:

```bash
noodles clean examples/error_handling/clean.yml
```
