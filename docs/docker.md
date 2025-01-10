The Coiled Prefect worker can either use Coiled "package sync" or Docker images for publishing your code.

Every flow has a ``deploy()`` method which can create or update a Prefect deployment. Here's how you'd use this to deploy your flow with a Docker image:

```python
from prefect.docker import DockerImage

arch = "amd64"
my_flow.deploy(
    name="my-coiled-deploy",
    work_pool_name="my-coiled-pool",
    image=DockerImage(name="prefect-docker-image", tag=arch, platform=f"linux/{arch}"),
    job_variables={"arm": True, "memory": "16GiB"},  # use VM with ARM cpu and 16GiB of memory for this flow
)
```
