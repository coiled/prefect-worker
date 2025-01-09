import coiled
from typing_extensions import TypedDict


class BuildCoiledSenvResult(TypedDict):
    name: str


def build_package_sync_senv(workspace=None, gpu=False, arm=False, strict=False):
    with coiled.Cloud(workspace=workspace) as cloud:
        package_sync_env_alias = cloud._sync(
            coiled.capture_environment.scan_and_create,
            cloud=cloud,
            force_rich_widget=True,  # TODO fix detection of whether rich widget will work
            workspace=workspace,
            gpu_enabled=gpu,
            architecture=coiled.types.ArchitectureTypesEnum.ARM64
            if arm
            else coiled.types.ArchitectureTypesEnum.X86_64,
            package_sync_strict=strict,
        )
        senv_name = package_sync_env_alias["name"]

    return BuildCoiledSenvResult(name=senv_name)
