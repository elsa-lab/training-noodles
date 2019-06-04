# Training Noodles

A simple and powerful tool to help training **multiple** programs on **multiple** servers with only one human.

## Installation

Run the following command:

```bash
pip install -e .
```

## Features

* Automatically deploys experiments to available servers
* No need to change any existing code
* Considers CPU usage, GPU usage, memory usage, disk usage, and more
* Uses only SSH protocol
* Relies on minimal dependencies
* Allows fast prototyping

## Usage

```bash
noodles <command_type> <path_to_spec>
```

It's just that simple.

## Examples

Here are some examples showing how Noodles is used:

```bash
noodles run my_training.yml
noodles status my_training.yml
noodles monitor my_training.yml
noodles stop my_training.yml
noodles download my_training.yml
noodles upload my_training.yml
...
```

You can also choose only some experiments:

```bash
noodles run "my_training.yml:Experiment 1,Experiment 2"
```

See the example [Two Locals](examples/two_locals/README.md) to get started. See [Train TensorFlow Examples](examples/train_tensorflow_examples/README.md) for a more complex example.

## Default Spec

Noodles will use properties from default spec if the user spec doesn't specify them. See [training_noodles/specs/defaults.yml](training_noodles/specs/defaults.yml) for the default spec.
