from typing import TYPE_CHECKING, Any, Dict, List, Optional

import dask.config
from anyio.abc import TaskStatus
from pydantic import Field, PrivateAttr, field_validator

from prefect.utilities.asyncutils import run_sync_in_worker_thread
from prefect.workers.base import (
    BaseJobConfiguration,
    BaseVariables,
    BaseWorker,
    BaseWorkerResult,
)

from .credentials import CoiledCredentials

if TYPE_CHECKING:
    from prefect.client.schemas import FlowRun


class CoiledWorkerJobConfiguration(BaseJobConfiguration):
    credentials: CoiledCredentials = Field(
        title="Coiled API token",
        default_factory=CoiledCredentials,
        description=(
            "The Coiled API token used to connect to Coiled. "
            "If not provided credentials will be inferred from "
            "the local environment."
        ),
    )
    workspace: Optional[str] = Field(
        default=None,
        description=(
            "The Coiled workspace to use. "
            "If not provided the default Coiled workspace for your user will be used."
        ),
    )
    software: Optional[str] = Field(
        default=None, description="Name of Coiled software environment to use"
    )
    image: Optional[str] = Field(
        default=None,
        description=(
            "Reference to Docker image, required if you aren't using Coiled software environment"
        ),
    )
    region: Optional[str] = Field(
        default=None,
        description="The region in which to run the job on Coiled; by default uses default region from Coiled workspace",
    )

    vm_types: Optional[List[str]] = Field(
        default=None,
        description=(
            "List of specific VM type(s) to use; "
            "often it's best to specify cpu and/or memory and let Coiled determine appropriate VM types."
        ),
    )
    arm: Optional[bool] = Field(default=None)
    cpu: Optional[int] = Field(
        default=None, description="Use a VM with this number of CPU (or vCPU) cores"
    )
    memory: Optional[str] = Field(
        default=None,
        description="Use a VM with this amount of memory; specify as a string such as '16 GiB'",
    )
    gpu: Optional[bool] = Field(
        default=None, description="Use a VM with NVIDIA GPU available"
    )

    additional_coiled_options: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Dictionary of any additional parameters to pass as keyword arguments for coiled.batch.run()",
    )

    _job_name: str = PrivateAttr(default=None)

    @field_validator("memory")
    @classmethod
    def _ensure_valid_memory(cls, value):
        try:
            dask.utils.parse_bytes(value)
            return value
        except ValueError:
            raise ValueError(
                f"{value!r} is not a valid memory value. You should specify memory as a string such as '16 GiB'."
            )


class CoiledVariables(BaseVariables):
    credentials: CoiledCredentials = Field(
        title="Coiled API token",
        default_factory=CoiledCredentials,
        description=(
            "The Coiled API token used to connect to Coiled. "
            "If not provided credentials will be inferred from "
            "the local environment."
        ),
    )
    workspace: Optional[str] = Field(
        default=None,
        description=(
            "The Coiled workspace to use. "
            "If not provided the default Coiled workspace for your user will be used."
        ),
    )
    software: Optional[str] = Field(
        default=None, description="Name of Coiled software environment to use"
    )
    image: Optional[str] = Field(
        default=None,
        description=(
            "Reference to Docker image, required if you aren't using Coiled software environment"
        ),
    )
    region: Optional[str] = Field(
        default=None,
        description="The region in which to run the job on Coiled; by default uses default region from Coiled workspace",
    )

    vm_types: Optional[List[str]] = Field(
        default=None,
        description=(
            "List of specific VM type(s) to use; "
            "often it's best to specify cpu and/or memory and let Coiled determine appropriate VM types."
        ),
    )
    arm: Optional[bool] = Field(default=None)
    cpu: Optional[int] = Field(
        default=None, description="Use a VM with this number of CPU (or vCPU) cores"
    )
    memory: Optional[str] = Field(
        default=None,
        description="Use a VM with this amount of memory; specify as a string such as '16 GiB'",
    )
    gpu: Optional[bool] = Field(
        default=None, description="Use a VM with NVIDIA GPU available"
    )

    additional_coiled_options: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Dictionary of any additional parameters to pass as keyword arguments for coiled.batch.run()",
    )


class CoiledWorkerResult(BaseWorkerResult):
    """
    The result of a Cloud Run worker V2 job.
    """


class CoiledWorker(BaseWorker):
    """
    The Cloud Run worker V2.
    """

    type = "coiled"
    job_configuration = CoiledWorkerJobConfiguration
    job_configuration_variables = CoiledVariables
    _description = "Execute flow runs via Coiled."  # noqa
    _display_name = "Coiled"
    _documentation_url = "https://docs.prefect.io/integrations/TODO"
    _logo_url = "https://docs.coiled.io/_static/Coiled-Logo.svg"  # noqa

    async def run(
        self,
        flow_run: "FlowRun",
        configuration: CoiledWorkerJobConfiguration,
        task_status: Optional[TaskStatus] = None,
    ) -> CoiledWorkerResult:
        """
        Runs the flow run on Coiled and waits for it to complete.

        Args:
            flow_run: The flow run to run.
            configuration: The configuration for the job.
            task_status: The task status to update.

        Returns:
            The result of the job.
        """
        logger = self.get_flow_run_logger(flow_run)

        from coiled.batch import run, wait_for_job_done

        # clean up labels so they can be applied as Coiled tags
        tags = (
            {
                key.replace("prefect.io/", ""): val
                for key, val in configuration.labels.items()
            }
            if configuration.labels
            else {}
        )

        # submit the job to run on Coiled
        creds_config = {}
        if configuration.credentials and configuration.credentials.api_token:
            creds_config = {
                "coiled.token": configuration.credentials.api_token.get_secret_value()
            }

        with dask.config.set(creds_config):
            run_info = run(
                command=configuration.command,
                workspace=configuration.workspace,
                container=configuration.image if not configuration.software else None,
                software=configuration.software,
                secret_env=configuration.env,
                region=configuration.region,
                vm_type=configuration.vm_types,
                arm=configuration.arm,
                cpu=configuration.cpu,
                memory=configuration.memory,
                gpu=configuration.gpu,
                tag=tags,
                logger=logger,
                **(configuration.additional_coiled_options or {}),
            )
        job_id = run_info.get("job_id")
        identifier = str(job_id)

        if task_status:
            task_status.started(identifier)

        # wait for Coiled job to be done
        with dask.config.set(creds_config):
            job_state = await run_sync_in_worker_thread(
                wait_for_job_done, job_id=job_id
            )

        return CoiledWorkerResult(
            status_code=-1 if "error" in job_state else 0,
            identifier=identifier,
        )
