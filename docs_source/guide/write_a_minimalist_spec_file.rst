.. _write_a_minimalist_spec_file:

Write a Minimalist Spec File
============================

Writing a spec file should be easy, let's build a minimalist spec file to print
the system information of a server.

Create a File
-------------

Let's create an empty file ``spec.yml`` in any directory.

Add a Name
----------

We should add the name of the spec for what it does by appending the following
snippet to ``spec.yml``.

.. code-block:: yaml

   name: Get server name

Add a Description
-----------------

We can optionally add a more verbose description. It's a good practice to let
people understand what the file is doing.

.. code-block:: yaml

   description: Use the command "uname" to get the server name

Add Experiments
---------------

Now it's time to add some experiments. In this example, we only want to check
the system information once, so there is only one experiment.

.. code-block:: yaml

   experiments:
   - name: Get server name
     commands:
       run: "uname -a"

``run`` is the :ref:`command type<command_types>` we'll be using. It can be any
other string (e.g., ``get_info``, ``get_info_on_the_server``)

.. tip::

   The experiments can be anything as long as they can be done by any Linux
   commands.

Add Servers
-----------

Then we should add some servers for the experiments to deploy. We should add at
least one server. Feel free to modify the following text to specify your own
server.

.. code-block:: yaml

   servers:
   - name: Server 1
     private_key_path: $HOME/.ssh/id_rsa
     username: $USER
     hostname: server1

``name`` is only used for Noodles to print the information,
``private_key_path`` is the path to the private key on the local machine,
``username`` is the username on the remote server (We use ``$USER`` to set the
same username as on the local machine), and ``hostname`` is usually a domain
name (e.g., ``example.com``) or an IP address (e.g., ``123.123.123.123``) of
the remote server.

.. note::

   Using password is not secure, so it's not supported by Noodles. If you
   haven't set up the SSH keys, please follow this tutorial_.

Final Spec File
---------------

The final spec file can be seen here and also on GitHub_:

.. literalinclude:: ../../examples/minimalist/spec.yml
   :language: yaml

Run the Spec File
-----------------

Execute the following command:

.. code-block:: bash

   noodles run spec.yml

and we should see something like:

.. code-block::
   :emphasize-lines: 6

   2019-06-10 16:42:23 run   INFO     Start stage "before_all_experiments"
   2019-06-10 16:42:23 run   INFO     Finished stage "before_all_experiments"
   2019-06-10 16:42:23 run   INFO     Start stage "experiments"
   2019-06-10 16:42:23 run   INFO     Deploy experiment "Get server name" to server "Server 1"
   2019-06-10 16:42:25 run   INFO     Commands output from STDOUT->
   Linux XXX 4.4.0-131-generic #157-Ubuntu SMP Thu Jul 12 15:51:36 UTC 2018 x86_64 x86_64 x86_64 GNU/Linux

   2019-06-10 16:42:25 run   INFO     Finished stage "experiments"
   2019-06-10 16:42:25 run   INFO     Start stage "after_all_experiments"
   2019-06-10 16:42:25 run   INFO     Finished stage "after_all_experiments"
   2019-06-10 16:42:25 run   INFO     Total elapsed time: 1.828s
   2019-06-10 16:42:25 run   INFO     Successfully deployed 100% (1/1) "run" experiments

See the highlighted line. If ``XXX`` is shown as the hostname of your server,
the deployment is successful.

.. _tutorial: https://www.digitalocean.com/community/tutorials/how-to-set-up-ssh-keys--2
.. _GitHub: https://github.com/sc420/training-noodles/blob/master/examples/minimalist/spec.yml
