Caveats
=======

All the commands written in the spec file will be executed by ``bash`` without
any `additional arguments`_ like ``--login``. You should explicitly set the
environment variables to avoid unexpected errors. For example, the two most
commonly used environment variables are:

1. ``PATH``
2. ``LD_LIBRARY_PATH``

You should set them before the start of each experiment.

.. _additional arguments: https://linux.die.net/man/1/bash
