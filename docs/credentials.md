# Coiled API token specified through Prefect credentials block

Things are more complicated if you need to specify the Coiled API token to use for the work pool,
but this does give you more flexibility and allows you to change the Coiled credentials
for a work pool without restarting the worker, or use different Coiled credentials for different deployments run via the same worker.

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
