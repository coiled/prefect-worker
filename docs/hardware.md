You can use the ``region``, ``arm``, ``cpu``, ``memory``, and ``gpu`` job variables to control the cloud hardware that your flow will run on.
These match the arguments to the ``coiled batch run`` CLI documented at https://docs.coiled.io/user_guide/api.html#coiled-batch-run

When using package sync for software, you also need to set ``arm`` and ``gpu`` so that the correct type of software environment is built. See [here](../example/prefect.yaml) for an example.

When using Docker, you need to make sure that the architecture of the image is correct. See [here](docker.md) for an example.
