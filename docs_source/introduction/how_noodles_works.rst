How Noodles Works
=================

Noodles deploys a number of experiments to the servers in each
*deployment round*. Noodles checks the requirements on the servers and submit
the commands only if the requirements are met. The general procedure is
described in the section :ref:`deploy_all_experiments`.

.. _deploy_all_experiments:

Deploy Experiments to Servers
-----------------------------

#. Initialize the list of experiments in :math:`E`
#. For each deployment round:

   #. Initialize the list of servers in :math:`S`
   #. Initialize the list of metrics in :math:`M`
   #. For each experiment :math:`e` in :math:`E`:

      #. If any dependent experiment of :math:`e` hasn't been deployed,
         continue to next experiment (``depends_on``)
      #. Noodles checks requirements (See section :ref:`check_requirements`)
      #. Noodles compares the metrics (results from the above step) to the
         user-defined expression
      #. If the expression is satisfied, deploy the experiment :math:`e` (See
         section :ref:`deploy_one_experiment`.

   #. If :math:`E` is empty, break
   #. Wait for some time (``round_interval``)

.. _check_requirements:

Check Requirements
------------------

#. For each requirement ID :math:`r` and corresponding commands :math:`C`:

   #. Initialize the boolean ``check := false``
   #. If the requirement is static:

      * If requirement ID :math:`r` is not in metrics :math:`M`, set
        ``check := true``

   #. Else if the requirement is dynamic (default behavior):

      * Set ``check := true``

   #. If ``check = true``, Noodles runs commands :math:`C` on each server in
      :math:`S` and treat the results as metrics

.. _deploy_one_experiment:

Deploy One Experiment
---------------------

#. Noodles runs the user-defined commands on the first satisfied server
#. Initialize the boolean ``success := true``
#. If there are any errors and error checking is enabled
   (``check_any_errors``):

   #. Check if there is any matching user-defined error handler
      (``error_handlers``)
   #. If there is a match:

      #. Execute the response commands
      #. If the action is ``abort``, raise the error and exit
      #. If the action is ``retry``, set ``success := false``
      #. If the action is ``continue``, set ``success := true``

   #. Else:

      #. Raise the error and exit

#. If ``success = true``:

   #. Remove the current experiment from :math:`E`
   #. Remove the satisfied server from :math:`S`
   #. If :math:`S` is empty, break the inner loop in
      :ref:`deploy_all_experiments`
   #. Wait for some time (``deployment_interval``)
