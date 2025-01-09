# `prefect-coiled`

Prefect worker for running flows on Coiled.

## Installation

To start using `prefect-coiled`:

```bash
pip install prefect-coiled  # or `pip -e .` install from source 
```

If you haven't used Coiled before, you'll need to create a Coiled account and log in:

```bash
coiled login
```
and then connect Coiled to your cloud account (AWS, Google Cloud, or Azure) where Coiled will run your flows.
You can either use our interactive setup CLI:

```bash
coiled setup
```

or via the web app UI at https://cloud.coiled.io/settings/setup

## Starting a worker

The worker polls a work pool for pending Prefect flows and then uses Coiled to run the flow in the cloud.

When running the worker, you can either have the worker implicitly pick up your Coiled API token
(from your local Coiled config file or environment variables),
or you can specify the API token using a Prefect credentials block set for the work pool.

### Locally configured Coiled API token

If you've already used the Coiled CLI or Python API, you're probably already logged in locally,
and a locally running Coiled Prefect worker will use your existing log in.
You can log in to Coiled by running

```bash
coiled login
```

or by setting your Coiled API token using the ``DASK__COILED_TOKEN`` environment variable.
See https://docs.coiled.io/user_guide/setup/tokens.html for more details.

Once you have a Coiled API token set where you'll be running the worker, you can start the worker like this:

```bash
prefect worker start -p "my-coiled-pool" --type "coiled"
```

### Coiled API token specified through Prefect credentials block

Things are more complicated if you need to specify the Coiled API token to use for the work pool,
but this does give you more flexibility and allows you to change the Coiled credentials
for a work pool without restarting the worker.

You'll need to create a credentials block, like so:

```python
from prefect_coiled import CoiledCredentials

CoiledCredentials(api_token=api_token).save("coiled-creds")
```

You then create the work pool:

```bash
prefect work-pool create --type coiled my-coiled-pool
```

This will return a URL to the work pool. Follow this URL, click the "..." menu and select "Edit".
Find the "CoiledCredentials" field and select the "coiled-creds" that you created before creating the work pool.
Save the pool.

Now, you can start a worker for this pool:

```bash
prefect worker start -p "my-coiled-pool"
```

The worker will use the credentials from the credentials block when running flows via Coiled.

## Create a deployment from a flow

Here's an example flow you might have in `readme_example.py`:

```python
from prefect import flow, task

@task
def foo(n):
    return n**2

@task
def do_something(x):
    print(x)

@flow(log_prints=True)
def my_flow():
    print("Hello from your Prefect flow!")
    X = foo.map(list(range(10)))
    do_something(X)
    return X
```

You can build and push a docker image with the code for this flow,
or you can use Coiled's "automatic package sync" feature to make a Coiled software environment with all your local packages and any code (like `readme_example.py`) in your working directory. 

Prefect has a Python API which supports building a docker image, and a YAML API which supports either approach.

### Python API with Docker

Every flow has a ``deploy()`` method which can create or update a Prefect deployment. Here's how you'd use this to deploy your flow:

```python
from prefect.docker import DockerImage
from readme_example import my_flow

arch = "amd64"
my_flow.deploy(
    name="my-coiled-deploy",
    work_pool_name="my-coiled-pool",
    image=DockerImage(name="prefect-docker-image", tag=arch, platform=f"linux/{arch}"),
    job_variables={"arm": True, "memory": "16GiB"},  # use VM with ARM cpu and 16GiB of memory for this flow
)
```

You can use the ``region``, ``arm``, ``cpu``, ``memory``, and ``gpu`` job variables to control the cloud hardware that your flow will run on.
These match the arguments to the ``coiled batch run`` CLI documented at https://docs.coiled.io/user_guide/api.html#coiled-batch-run

### YAML API with Coiled package sync

Here's an example ``prefect.yaml`` file that defines a deployment using Coiled package sync.

```yaml
name: prefect-worker
prefect-version: 3.1.11

build:
- prefect_coiled.deployments.steps.build_package_sync_senv:
    id: coiled_senv
    arm: true

pull:
- prefect.deployments.steps.set_working_directory:
    directory: /scratch/batch

deployments:
- name: my-coiled-deploy
  flow_name: my-coiled-flow
  entrypoint: readme_example:my_flow
  work_pool:
    name: my-coiled-pool
    job_variables:
      arm: true
      software: '{{ coiled_senv.name }}'
```

You can use the ``region``, ``arm``, ``cpu``, ``memory``, and ``gpu`` job variables to control the cloud hardware that your flow will run on.
These match the arguments to the ``coiled batch run`` CLI documented at https://docs.coiled.io/user_guide/api.html#coiled-batch-run

To create the deployment, you'll run

```bash
prefect deploy --prefect-file prefect.yaml
```

## Run the flow

Once the flow and deployment have been created and you have a Prefect Coiled worker running, you can run the flow:

```bash
prefect deployment run 'my-flow/my-coiled-deploy'
```
