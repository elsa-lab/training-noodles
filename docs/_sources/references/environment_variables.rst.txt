Environment Variables
=====================

Environment Variables in Spec
-----------------------------

Environment variables can be used in the following
:ref:`spec options <spec_options>`:

* Environment variables in ``experiment_default.envs``
* Commands in ``experiment_default.commands``
* Paths in ``experiment_default.write_outputs``
* Environment variables in ``experiments[].envs``
* Commands in ``experiments[].commands``
* Paths in ``experiments[].write_outputs``
* Path in ``server_default.private_key_path``
* Value in ``server_default.username``
* Value in ``server_default.hostname``
* Path in ``server[].private_key_path``
* Value in ``server[].username``
* Value in ``server[].hostname``
* Commands in ``requirements.<requirement_id>``
* Path in ``write_status_to``

Extra Environment Variables
---------------------------

Noodles also provides some extra environment variables when executing the
command over SSH:

* ``NOODLES_EXPERIMENT_NAME`` (The current experiment name)
* ``NOODLES_SERVER_NAME`` (The current server name of the target server)
* ``NOODLES_SERVER_PORT`` (The port to connect to the target server)
* ``NOODLES_SERVER_USERNAME`` (The username of the target server)
* ``NOODLES_SERVER_HOSTNAME`` (The hostname of the target server)
* ``NOODLES_SERVER_AUTHORITY`` (Username and hostname of the target server, in
  the form of ``<username>@<hostname>``)
