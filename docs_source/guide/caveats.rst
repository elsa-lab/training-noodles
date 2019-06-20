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

You should explicitly set the environment variables to avoid unexpected
errors. The two most commonly used environment variables are:

1. ``PATH``
2. ``LD_LIBRARY_PATH``

You should set them before the start of each experiment.

Choose the Type of Shells
-------------------------

The commands executed on remote machines will use *non-interactive* *non-login*
shell by default. That means the following files **won't** be used at all:

#. ``/etc/profile``
#. ``/etc/bash.bash_logout``
#. ``~/.bash_profile`` or ``~/.bash_login`` or ``~/.profile`` (bash would
   choose the first one if the file exists for *login* shells)
#. ``~/.bashrc``
#. ``~/.bash_logout``
#. ``~/.inputrc``

(For more information, see sections *Invocation* and *Files* in Linux man page
bash_)

If you want to use a *non-interactive* *login* shell, change the spec option
:option:`shell_stdin` to ``bash -s -l``.

It's not recommended to use interactive shells because interactive shells may
require user inputs and get stuck if no user is present at the moment.

.. _bash: https://linux.die.net/man/1/bash
