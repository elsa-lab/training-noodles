# Training Noodles

A collection of tools to aid training multiple programs on multiple servers with one human.

## Installation

Run the following command:

```bash
pip install -e .
```

## Features

* Is simple to use
* Is easy to extend
* Considers both CPU and GPU usage
* Uses only SSH protocol
* Relies on minimal dependencies

## Objective

We want to train multiple programs on multiple servers, here are what most people typically do (including me):

1. Open a terminal to connect to `server1`
2. Run `command1`
3. Open a terminal to connect to `server2`
4. Run `command2` (or `command1` with different parameters, inputs, etc.)
5. Close all terminals and do other stuff...
6. Open a terminal to connect to `server1`
7. Is it done yet? No
8. Open a terminal to connect to `server2`
9. Is it done yet? Yes
10. Download the outputs from `server2`
11. Run `command3` on `server2`

What a mess! I just want this:

1. Prepare a list of commands to run (`command1`, `command2`, `command3`)
2. Prepare a spec file
3. Distribute the training to all servers automatically
4. Run a subsequent command automatically whenever a previous one finishes
5. Get notification whenever a training finishes
6. Download the outputs automatically whenever a training finishes

And the spec should be really simple just by looking at it. No need for a bunch of tutorial.

## Examples

Here are some examples showing how the tools are used, I call the tools instant noodles:

```bash
noodles run my_training.yml
noodles status my_training.yml
noodles stop my_training.yml
noodles download my_training.yml
noodles upload my_training.yml
```

You can also choose only some experiments:

```bash
noodles run my_training.yml:experiment1,experiment2
```
