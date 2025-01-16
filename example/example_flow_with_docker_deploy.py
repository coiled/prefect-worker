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

    import coiled

    gpu = True
    arm = False
    arch = (
        coiled.types.ArchitectureTypesEnum.ARM64
        if arm
        else coiled.types.ArchitectureTypesEnum.X86_64
    )

    with coiled.Cloud() as cloud:
        # TODO make a cleaner sync API for this
        package_sync_env_alias = cloud._sync(
            coiled.capture_environment.scan_and_create,
            cloud=cloud,
            force_rich_widget=True,
            gpu_enabled=gpu,
            architecture=arch,
        )
        senv_name = package_sync_env_alias["name"]

    my_flow.deploy(
        name="my-coiled-deploy",
        work_pool_name="my-coiled-pool",
        job_variables={"arm": arm, "gpu": gpu, "software": senv_name},
        # TODO see if these work and if they're all required
        image="",
        build=False,
        push=False,
    )
