# Installation

```bash
pip install prefect coiled coiled-prefect
```

If you haven't used Prefect Cloud before, you'll need to create an account and log in:

```bash
prefect cloud login
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

# Create the Prefect work pool and deployment

```bash
prefect work-pool create --type coiled example-coiled-pool
prefect deploy --prefect-file prefect.yaml
```

If you make any changes to the deployment (for example, if you want to run your flow on a VM with more memory or a GPU),
then you'll rerun the deploy command after editing the YAML file. Otherwise, there's no need to run these commands more than once.

# Run the flow on Coiled

Start the worker which will poll for work and submit it to Coiled:

```bash
prefect worker start --pool 'example-coiled-pool'
```

This will automatically pick up the Coiled API token that was set when you ran `coiled login`.
If you're running the worker elsewhere, you can specify the Coiled API token in various ways explained in
https://docs.coiled.io/user_guide/setup/tokens.html

The Prefect worker is not where your flow will run, but it needs to be running in order to submit the flow to Coiled.

To run the deployment, you can either run this in another terminal window:

```bash
prefect deployment run 'my-flow/example-coiled-deploy'
```

or use the Prefect UI to initiate a run of the deployment.
