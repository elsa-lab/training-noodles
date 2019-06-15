Command Line Arguments
======================

.. contents::

Usage
-----

.. code-block:: bash

   noodles <command_type> <path_to_spec> [optional_arguments]

Positional Arguments
--------------------

.. option:: <command_type>

   The command type.

   The command type is a user-defined key under the following items in the
   :ref:`spec file <spec_options>`:

   1. ``<top_level>.depends_on``
   2. ``<top_level>.requirements``
   3. ``<top_level>.commands``
   4. ``<top_level>.write_outputs``

   Where ``<top_level>`` can be one of the following top level keys in the
   spec:

   1. ``experiment_default``
   2. ``before_all_experiments[i]``
   3. ``experiments[i]``
   4. ``after_all_experiments[i]``

   ``i`` can be any index.

   :Example:
      The following code specifies the command type ``lets_do_it``:

      .. code-block:: yaml

         experiments:
         - name: run_script.exp1
           description: Run the script after uploading the script to the remote server
           envs:
             SCRIPT: exp1.sh
           depends_on:
             lets_do_it:
             - upload.exp1
           requirements:
             lets_do_it:
             - memory_usage: "<=0.5"
           commands:
             lets_do_it:
             - "cd $HOME"
             - "bash $SCRIPT"
           write_outputs:
             lets_do_it:
               stdout_to: $LOCAL_DIR/exp1.stdout.log
               stderr_to: $LOCAL_DIR/exp1.stderr.log

.. option:: <path_to_spec>

   Path to the spec file.

   :Example:
      ``specs/train.yml``

Optional Arguments
------------------

.. option:: -h, --help

   Show the help message and exit.

.. option:: -v, --verbose

   Print out verbose messages.

   If this option is used, verbose messages regarding to what Noodles is doing
   will be printed.

.. option:: -d, --debug

   Print out debug messages.

   If this option is used, the following things will be printed:

   1. Command line arguments used
   2. Original user spec
   3. Processed user spec
   4. Creation of temporary files
   5. Commands written to temporary files
   6. The commands to be run by Noodles
   7. Environment variables added by Noodles

.. option:: -s, --silent

   Silence all logging messages.
