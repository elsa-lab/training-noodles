Caveats
=======

Set Working Directory
---------------------

The initial working directory on the local machine and remote machines may be
different, so it's better to explicitly set the working directory. Two
recommended options are:

1. Use absolute paths all the time
2. ``cd`` to a directory first and use relative paths afterwards

Set Environment Variables
-------------------------

The commands executed on remote machines will use *non-interactive* *non-login*
shell (This will be changed in latter version by allowing customizable shell
commands and arguments). You should explicitly set environment variables to
avoid unexpected errors. For example, the two most commonly used environment
variables are:

1. ``PATH``
2. ``LD_LIBRARY_PATH``

You should set them before the start of each experiment.
