# Training Noodles

A simple and powerful tool to help training **multiple** programs on **multiple** servers with only one human.

## Installation

Run the following command:

```bash
pip install -e .
```

## Features

* Is simple to use
* Is easy to customize
* No need to change any existing code
* Considers CPU usage, GPU usage, memory usage, disk usage, and more
* Uses only SSH protocol
* Relies on minimal dependencies
* Just like instant noodles

## Examples

Here are some examples showing how the tools are used:

```bash
noodles run my_training.yml
noodles status my_training.yml
noodles monitor my_training.yml
noodles stop my_training.yml
noodles download my_training.yml
noodles upload my_training.yml
```

You can also choose only some experiments:

```bash
noodles run my_training.yml:experiment1,experiment2
```
