ipyexperimenter
===============================

An ipywidget for managing and running several related parameterized experiments

Installation
------------

To install use pip:

    $ pip install ipyexperimenter
    $ jupyter nbextension enable --py --sys-prefix ipyexperimenter

To install for jupyterlab

    $ jupyter labextension install ipyexperimenter

For a development installation (requires npm),

    $ git clone https://github.com/tslaton/ipyexperimenter.git
    $ cd ipyexperimenter
    $ pip install -e .
    $ jupyter nbextension install --py --symlink --sys-prefix ipyexperimenter
    $ jupyter nbextension enable --py --sys-prefix ipyexperimenter
    $ jupyter labextension install js

When actively developing your extension, build Jupyter Lab with the command:

    $ jupyter lab --watch

This take a minute or so to get started, but then allows you to hot-reload your javascript extension.
To see a change, save your javascript, watch the terminal for an update.

Note on first `jupyter lab --watch`, you may need to touch a file to get Jupyter Lab to open.

