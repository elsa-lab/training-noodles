.. _linux_terminal_for_windows:

Linux-based Terminal for Windows
================================

For Linux users, please skip this part and continue to :ref:`usage`.

For Windows users, I recommend using git-sdk_. You can use built-in Linux
commands and install packages. For more information about git-sdk, please see
build-extra_.

To install and use git-sdk, follow these steps:

1. Download git-sdk_
2. Install git-sdk (e.g., to the default directory ``C:\git-sdk-64``)
3. Open ``C:\git-sdk-64\git-bash.exe``

Install and Uninstall Packages
------------------------------

Use ``pacman -S`` to install packages and ``pacman -R`` to remove packages.

Commonly Used Packages
~~~~~~~~~~~~~~~~~~~~~~

1. Install Tmux for detached sessions: ``pacman -S tmux``
2. Install procps-ng for browsing procfs: ``pacman -S procps-ng``

Use git-sdk in Visual Studio Code
---------------------------------

To use git-sdk as the integrated terminal in VS Code, add the following JSON
snippet to the settings:

.. code-block:: json

   {
       "terminal.integrated.shell.windows": "C:\\git-sdk-64\\usr\\bin\\bash.exe"
   }

.. _git-sdk: https://github.com/git-for-windows/build-extra/releases
.. _build-extra: https://github.com/git-for-windows/build-extra
