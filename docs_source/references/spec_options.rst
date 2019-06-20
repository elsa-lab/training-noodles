.. _spec_options:

Spec Options
============

.. contents::

All the following keys are optional. If the user spec doesn't specify them,
the default options will be used from the `default specs`_.

General Options
---------------

.. option:: name

   :Type: String

   Name of the spec.

.. option:: description

   :Type: String

   Description of the spec.

Experiments
-----------

.. option:: experiment_default

   :Type: Mapping

   The default options for each experiment in :option:`experiments`. Available
   options are:

   .. option:: experiment_default.name

      :Type: String
      :Default: ``<default>``

      Name of the experiment.

   .. option:: experiment_default.envs

      :Type: Mapping
      :Format:
         .. code-block:: yaml

            "<Environment variable name 1>": "<Value 1>"
            "<Environment variable name 2>": "<Value 2>"
            ...
      :Default: ``{}``
      :Example:
         .. code-block:: yaml

            experiment_default:
              envs:
                LOCAL_DIR: $HOME/test
                REMOTE_FILE: $HOME/test.log

      Default environment variables.

      These environment variables will be added to each experiment no matter
      what the command type is. It's convenient to set commonly used
      environment variables here.

   .. option:: experiment_default.depends_on

      :Type: Mapping
      :Format:
         .. code-block:: yaml

            "<Command type 1>":
            - "<Name of other experiment 1>"
            - "<Name of other experiment 2>"
            - ...
            "<Command type 2>":
            - ...
            ...
      :Default: ``{}``
      :Example:
         .. code-block:: yaml

            experiment_default:
              depends_on:
                run:
                - Installation
                - Configuration

      A list of dependent experiments.

      Noodles will check whether all experiments in ``depends_on`` are already
      successfully deployed. If one of the experiments hasn't been deployed,
      Noodles would skip it and retry this experiment in the next deployment
      round.

   .. option:: experiment_default.requirements

      :Type: Mapping
      :Format:
         .. code-block:: yaml

            "<Command type 1>":
            - "<Requirement ID 1>": "<Expression 1>"
            - "<Requirement ID 2>": "<Expression 2>"
            - "static:<Requirement ID 3>": "<Expression 3>"
            - "dynamic:<Requirement ID 4>": "<Expression 4>"
            - ...
            "<Command type 2>":
            - ...
            ...
      :Default: ``{}``
      :Example:
         .. code-block:: yaml

            experiment_default:
              requirements:
                run:
                - cpu_usage: "<=70"
                - cpu_load: "<=32"
                - gpu_usage: "<=50"
                - static:free_quota: ">=0.2"
                - dynamic:has_lock_file: "==No"
                stop:
                - has_lock_file: "==Yes"
                download:
                - count_output_files: "!=0"

      A list of requirements.

      Each requirement ID (e.g., ``cpu_usage``) is mapped to a group of
      commands specified in :option:`requirements`. The mapped commands would
      be run on each server in :math:`S` (See :ref:`deploy_all_experiments`).
      The metric is then compared to the expression, which is composed of
      ``<Operator><Value>``.

      List of available operators are:

      * ==
      * !=
      * <
      * >
      * <=
      * >=

      Noodles would try to convert the value following operator using Python
      builtin function :py:func:`ast.literal_eval`. It it fails, the original
      value would be used in its original string form.

      Each command can specify an extra prefix ``static:`` or ``dynamic:``. If
      a prefix ``static:`` is used, Noodles will not check the requirement when
      some other experiment has checked it before in the same deployment round.

      On the other hand, if a prefix ``dynamic:`` is used, every requirement
      will be checked for each experiment. By default, ``dynamic:`` behavior is
      chosen when the prefix is omitted. See :ref:`check_requirements` for the
      procedure.

   .. option:: experiment_default.commands

      :Type: Mapping
      :Format:
         .. code-block:: yaml

            "<Command type 1>": "<Command 1>"
            "<Command type 2>":
            - "<Command A>"
            - "<Command B>"
            - "local:<Command C>"
            - "remote:<Command D>"
            - ...
            ...
      :Default: ``{}``
      :Example:
         .. code-block:: yaml

            experiment_default:
              commands:
                run: "touch exp.lock && ./exp1.sh $PARAMETER"
                stop:
                - pkill exp1
                - rm exp.lock
                download:
                - local:scp $NOODLES_SERVER_AUTHORITY:$REMOTE_FILE $LOCAL_DIR

      Commands to be run on a server.

      Commands will only be executed on servers when the above requirements are
      met.

      Each command can specify an extra prefix ``local:`` or ``remote:`` to
      specify whether to run the command on local or remote machine
      respectively. By default, all commands are deployed to remaining servers
      selected from :option:`servers` if no prefix is specified.

      It's useful to add ``local:`` to a command to check the problems on local
      machine if the command fails on a remote server.

   .. option:: experiment_default.write_outputs

      :Type: Mapping
      :Format:
         .. code-block:: yaml

            "Command type 1>":
              stdout_to: "<Path to write STDOUT output>"
              stderr_to: "<Path to write STDERR output>"
            "Command type 2>":
              stdout_to: ...
              stderr_to: ...
            ...
      :Default: ``{}``
      :Example:
         .. code-block:: yaml

            experiment_default:
              write_outputs:
                run:
                  stdout_to: $LOCAL_DIR/exp1.stdout.log
                  stderr_to: $LOCAL_DIR/exp1.stderr.log

      The paths to write STDOUT and STDERR outputs.

      By default, STDOUT is written to the terminal and STDERR is written to
      the terminal only when it's nonempty.

      User can redirect the outputs to files by specifying paths in options
      ``stdout_to`` and/or ``stderr_to`` for STDOUT and STDERR respectively
      under the option ``write_outputs``. If ``stderr_to`` is specified, STDERR
      will be written no matter it's empty or not.

.. option:: before_all_experiments

   :Type: List
   :Format: Same as :option:`experiments`
   :Default: ``[]``
   :Example: See example in :option:`experiments`

   A list of experiments to runs before running ``experiments``.

.. option:: experiments

   :Type: List
   :Format:
      .. code-block:: yaml

         - "<Experiment 1>"
         - "<Experiment 2>"
         - ...
   :Default: ``[]``
   :Example:
      .. code-block:: yaml

         experiments:
         - name: Experiment 1
           envs:
             LOCAL_DIR: $HOME/exp1
             REMOTE_FILE: $HOME/exp1.log
             PARAMETER: 3
           depends_on:
             run:
             - Installation
             - Configuration
           requirements:
             run:
             - cpu_usage: "<=70"
             - cpu_load: "<=32"
             - gpu_usage: "<=50"
             - free_quota: ">=0.2"
             - has_lock_file: "==No"
             stop:
             - has_lock_file: "==Yes"
             download:
             - count_output_files: "!=0"
           commands:
             run: "touch exp.lock && ./exp1.sh $PARAMETER"
             stop:
             - pkill exp1
             - rm exp.lock
             download:
             - local:scp $NOODLES_SERVER_AUTHORITY:$REMOTE_FILE $LOCAL_DIR
           write_outputs:
             run:
               stdout_to: $LOCAL_DIR/exp1.stdout.log
               stderr_to: $LOCAL_DIR/exp1.stderr.log
         - name: Experiment 2
           envs:
             LOCAL_DIR: $HOME/exp2
             REMOTE_FILE: $HOME/exp2.log
             PARAMETER: 5
           ...
         ...

   A list of main experiments.

   Each experiment would override the options in :option:`experiment_default`.
   See :option:`experiment_default`.

.. option:: after_all_experiments

   :Type: List
   :Format: Same as :option:`experiments`
   :Default: ``[]``
   :Example: See example in :option:`experiments`

   A list of experiments to run after running ``experiments``.

Servers
-------

.. option:: server_default

   :Type: Mapping
   :Example:
      .. code-block:: yaml

         server_default:
           name: <default>
           private_key_path: $HOME/.ssh/id_rsa
           port: 22
           username: user1
           hostname: server1.example.com

   The default options for each server in :option:`servers`. Available
   options are:

   .. option:: server_default.name

      :Type: String
      :Default: ``<default>``

      Default name of the server.

   .. option:: server_default.private_key_path

      :Type: String
      :Default: ``HOME/.ssh/id_rsa``

      Path to the private key on local machine.

   .. option:: server_default.port

      :Type: Integer
      :Default: ``22``

      Port to connect.

   .. option:: server_default.username

      :Type: String
      :Default: ``$USER``

      Username on the server (e.g., ``user1``).

   .. option:: server_default.hostname

      :Type: String
      :Default: ``localhost``

      Hostname of the server (e.g., ``example.com``, ``123.123.123.123``).

      If the hostname is a special value ``localhost``, the commands will be
      run on local machine without :program:`ssh`.

.. option:: servers

      :Type: List
      :Format:
         .. code-block:: yaml

            - "<Server 1>"
            - "<Server 2>"
            - ...
      :Default: ``[]``
      :Example:
         .. code-block:: yaml

            servers:
            - name: Server 1
              username: user1
              hostname: server1.example.com
            - name: Server 2
              private_key_path: temp/id_rsa
              port: 64
              username: user2
              hostname: 123.123.123.123
            - name: Local server
              username: $USER
              hostname: localhost

      A list of servers.

      Each server would override the options in :option:`server_default`. See
      :option:`server_default`.

Requirements
------------

.. option:: requirements

   :Type: Mapping
   :Default: See ``requirements`` in `default specs`_.
   :Format:
      .. code-block:: yaml

         "<Requirement ID 1>": "<Command 1>"
         "<Requirement ID 2>":
         - "<Command A>"
         - "<Command B>"
         - ...
         ...
   :Example:
      .. code-block:: yaml

         requirements:
           # Check whether the file exists
           has_file: "[ -f $PATH ] && echo -n Yes || echo -n No"
           # Get average CPU usage over 3 seconds (Output: Three floats between 0-100 (%)) (Reference: https://askubuntu.com/a/941997)
           cpu_usage:
           - "(grep 'cpu ' /proc/stat;sleep 0.1;grep 'cpu ' /proc/stat) | awk -v RS='' '{print ($13-$2+$15-$4)*100/($13-$2+$15-$4+$16-$5)}'"
           - "sleep 1.5"
           - "(grep 'cpu ' /proc/stat;sleep 0.1;grep 'cpu ' /proc/stat) | awk -v RS='' '{print ($13-$2+$15-$4)*100/($13-$2+$15-$4+$16-$5)}'"
           - "sleep 1.5"
           - "(grep 'cpu ' /proc/stat;sleep 0.1;grep 'cpu ' /proc/stat) | awk -v RS='' '{print ($13-$2+$15-$4)*100/($13-$2+$15-$4+$16-$5)}'"
           # Get average CPU load over last 1 minute (Output: CPU load greater or equal to 0.0) (Reference: https://stackoverflow.com/a/24839903)
           cpu_load: awk '{print $1}' /proc/loadavg

   Commands to run to check requirements on servers.

   After executing the commands on server, Noodles would try to convert the
   text in each line in STDOUT output using Python builtin function
   :py:func:`ast.literal_eval` and calculate the mean as the metric. If it
   fails, the original STDOUT would be used as metric.

Deployment
----------

.. option:: write_status_to

   :Type: Mapping
   :Default: ``{}``
   :Format:
      .. code-block:: yaml

         "<Command type 1>": "<Path 1>"
         "<Command type 2>": "<Path 2>"
         ...

   The path for Noodles to write deployment status.

   The list of status to be written are:

   * Start time: <Start time of current Noodles run>
   * Previous round time: <Time of the end of previous deployment round>
   * Elapsed time: <Elapsed time from start time>
   * Stage: <Current stage (:option:`before_all_experiments`,
     :option:`experiments` or :option:`after_all_experiments`)>
   * Round #: <Current deployment round number>
   * Deployed experiments: <A list of deployed experiment names>
   * Undeployed experiments: <A list of undeployed experiment names>
   * Undeployed experiments (For command): <A
     :ref:`filter string <choose_only_some_experiments>` of comma-separated
     undeployed experiment names>

   The file will be updated before the first deployment and after each
   successful deployment.

.. option:: round_interval

   :Type: Number
   :Default: ``10``

   The interval to run each deployment round.

   See how it's used in :ref:`deploy_all_experiments`.

.. option:: deployment_interval

   :Type: Number
   :Default: ``0``

   The interval to deploy each experiment in each round.

   See how it's used in :ref:`deploy_one_experiment`.

Error Handling
--------------

.. option:: check_any_errors

   :Type: Boolean
   :Default: ``True``

   Whether to check any nonzero return code and nonempty stderr.

   When it's turned on, any nonzero return code and/or nonempty STDERR will
   trigger Noodles to check a matching error handler in
   :option:`error_handlers`. Otherwise, any errors will be ignored.

.. option:: error_handlers

   :Type: List
   :Default: ``[]``
   :Format:
      .. code-block:: yaml

         - name: "<Name 1>"
           return_code: "<return code pattern 1>"
           stderr_pattern: "<STDERR pattern 1>"
           action: "<Action to take 1>"
         - name: "<Name 2>"
           ...
         ...
   :Example:
      .. code-block:: yaml

         error_handlers:
         - name: Abort when command not found
           return_code: "\\d+"
           stderr_pattern: "^bash: line \\d+: .+: command not found\\s+$"
           action: abort
         - name: Ignore SSH resolve hostname error
           return_code: 255
           stderr_pattern: "^ssh: Could not resolve hostname .+: Name or service not known\\s+$"
           action: retry
         - name: Ignore git clone already exists error
           return_code: 0
           stderr_pattern: "^fatal: destination path '.+' already exists and is not an empty directory.\\s+$"
           action: continue

   List of error handlers.

   If the option :option:`check_any_errors` is turned on and any nonzero return
   code and/or nonempty STDERR are generated after executing some commands,
   Noodles will check each error handler in this option and take the predefined
   action.

   Available actions are:

   * ``abort`` (Noodles will abort the whole procedure, raise an error and
     exit)
   * ``retry`` (Noodles will skip the experiment and retry it in the next
     deployment round)
   * ``continue`` (Noodles will ignore the errors and treat the deployment
     as successful)

   ``return_code`` and ``stderr_pattern`` will be passed into the argument
   ``pattern`` in Python builtin function ``re.match(pattern, string)``, the
   argument ``string`` will be the return code or STDERR string to be handled.

   A error handler is only matched when both ``return_code`` and
   ``stderr_pattern`` have full match (i.e., the match returned by
   :py:func:`re.match` is exactly the same as the argument ``string``).

.. _default specs: https://github.com/sc420/training-noodles/blob/master/training_noodles/specs/defaults.yml
