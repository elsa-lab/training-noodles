Use Case
========

Train 4 Experiments on 3 Servers
--------------------------------

If we want to run 4 experiments on 3 servers, more specifically, we need to

1. Upload the code to one of the servers which has low CPU usage
2. Run the code on the server
3. Download experimental results when they're ready

.. _fig_round_1:
.. figure:: ../../images/round_1.png
   :name: deployment_round_1

   Deployment round 1.

In the first deployment round (See :numref:`deployment_round_1`), Noodles will
use the user-defined commands to check CPU usage on the servers.

The CPU usage is high on *Server 1* because there are some other programs
running, so Noodles uses `scp` to upload the code *Code 1* and *Code 2*, and
run them on *Server 2* and *Server 3* respectively.

As for how to upload the code, it's just a list of commands written by us,
Noodles just follows the commands.

.. figure:: ../../images/round_2.png
   :name: deployment_round_2

   Deployment round 2.

In the second deployment round (See :numref:`deployment_round_2`), we tell
Noodles to check experimental results on all servers.

Noodles finds that *Server 3* has just finished running *Code 2*, so it
downloads the experimental results and process the data on local machine as we
tell it to do so.

.. figure:: ../../images/round_3.png
   :name: deployment_round_3

   Deployment round 3.

In the third deployment round (See :numref:`deployment_round_3`), *Code 3* and
*Code 4* still need to be deployed. Noodles checks the CPU usage on all servers
again. As *Server 1* has just become free now, Noodles can deploy *Code 3* and
*Code 4* to *Server 1* and *Server 3* respectively.

The deployment round would continue until all experiments are successfully
deployed. As in this case, Noodles will try to download and process the
experimental results of *Code 1*, *Code 3* and *Code 4* in later rounds.
