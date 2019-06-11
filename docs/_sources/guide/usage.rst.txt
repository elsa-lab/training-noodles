.. _usage:

Usage
=====

Run Noodles
-----------

.. code-block:: bash

   noodles <command_type> <path_to_spec>

Noodles only uses one command type and one spec file at a time. The command
type is simply a key in the spec file to server for different purposes.

.. _choose_only_some_experiments:

Choose Only Some Experiments
----------------------------

Noodles can run only some experiments when a filter string is specified as
follows:

.. code-block:: bash

   noodles <command_type> <path_to_spec>:<filter_experiments>

``<filter_experiments>`` is a comma-separated string composed of experiment
names. For example, the command would be like this when we only want to run
experiments *exp1* and *exp3*:

.. code-block:: bash

   noodles run spec.yaml:exp1,exp3

.. _command_types:

Command Types
-------------

We may need different command types for the same experiment, for example, we
may need to run and stop the same experiment. We should write different
commands under two keys ``run`` and ``stop`` in the spec file.

Then we can run the experiments like this:

.. code-block:: bash

   noodles run spec.yml
   ...
   noodles stop spec.yml

Spec File
---------

The spec file should be written in YAML_. We'll introduce the how write a
minimalist spec file in the next topic :ref:`write_a_minimalist_spec_file`.

.. _YAML: https://en.wikipedia.org/wiki/YAML
