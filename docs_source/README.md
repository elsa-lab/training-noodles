# Documentation Source

We use [Sphinx](http://www.sphinx-doc.org/en/master/) to convert `.rst` files to `.html` files for the documentation.

## Prerequisites

1. Install the following packages:

    ```bash
    pip install sphinx sphinx-autobuild sphinx-rtd-theme
    ```

2. Change the working directory to `docs_source`

## Build

To manually build the HTML files, execute the following:

```bash
make html
```

To automatically build the HTML files, execute the following:

```bash
make livehtml
```

## Publish

GitHub allows us to host the documentation in the `docs` directory in the `master` branch. We need to move the build files from `docs_source/_build/html/` to `docs/`. To do so, execute the following:

```bash
make publish
```
