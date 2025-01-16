from prefect import flow, task
import coiled

@task
@coiled.function(n_workers=[0,3])
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


if __name__ == "__main__":
    # Option 1: Build and deploy Docker image with default architecture

    # Note that the image architecture will match your local machine
    # so on a recent Mac this will be an ARM image (linux/arm64 platform).
    my_flow.deploy(
        name="my-coiled-deploy",
        work_pool_name="my-coiled-pool",
        image="ntabris/prefect-docker-image",  # replace `ntabris` with your own repository
        # If the image is for ARM, you'll need to add this line so Coiled will use ARM VMs:
        # job_variables={"arm": True},
    )

    # Option 2: Explicitly specify the Docker image architecture

    from prefect.docker import DockerImage

    arm = True
    arch = "arm64" if arm else "amd64"

    my_flow.deploy(
        name="my-coiled-deploy",
        work_pool_name="my-coiled-pool",
        image=DockerImage(name="ntabris/prefect-docker-image", tag=arch, platform=f"linux/{arch}"),
        job_variables={"arm": arm},
    )

    # Option 3: Build a Coiled "package sync" environment and use that
    # - this don't work because Flow.deploy() requires you to specify image

    import coiled

    gpu = True
    arm = False

    senv_name = coiled.create_package_sync_software_env(gpu=gpu, arm=arm)["name"]

    my_flow.deploy(
        name="my-coiled-deploy",
        work_pool_name="my-coiled-pool",
        job_variables={"arm": arm, "gpu": gpu, "software": senv_name},
        # FIXME we want to use "software" and no image, but prefect will raise
        #   because image is required
        image="",
        build=False,
        push=False,
    )
