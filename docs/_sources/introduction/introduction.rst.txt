Introduction
============

What is Noodles
---------------

Training Noodles (or simply Noodles) is a simple and powerful tool to help
training multiple programs on multiple servers.

Why Created This Tool
---------------------

When I was doing research, the work is still preliminary most of the time. I
have limited time and limited servers to run the experiments. I don't want to
use some black box tools or frameworks which have steep learning curves.
Besides, the research direction may change suddenly so that a tool may no
longer suite my needs.

So I created this tool aiming for simplicity and reproducibility. One spec file
is enough to run everything I need. And if something goes wrong? I can easily
reproduce everything without the tool just by looking at the spec file.

Features
--------

What can Noodles do? Basically everything one can do on a terminal. Noodles
not only helps to automatically deploy Linux commands on different servers but
also helps to manage their execution dependencies. The main benefits of Noodles
are the following:

* Automatically deploys experiments to available servers
* No need to change any existing code
* Considers CPU usage, GPU usage, memory usage, disk usage, and more
* Uses only SSH protocol
* Relies on minimal dependencies
* Allows fast prototyping

The fact that Noodles only uses SSH protocol means that Noodles doesn't assume
the type of a server, it can be a local machine, self-hosted server, Amazon EC2
instance or Google Computer Engine instance.
