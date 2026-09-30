import asyncio
import unittest
from types import SimpleNamespace
from typing import ClassVar
from unittest.mock import patch

import coiled
import coiled.batch
from pydantic import SecretStr

from prefect_coiled.worker import CoiledWorker


class FakeCloud:
    instances: ClassVar[list["FakeCloud"]] = []

    def __init__(self, *, token, workspace):
        self.token = token
        self.workspace = workspace
        self.closed = False
        self.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.closed = True


class FakeWorker:
    def get_flow_run_logger(self, flow_run):
        return None


def configuration(token, workspace):
    return SimpleNamespace(
        credentials=SimpleNamespace(api_token=SecretStr(token)),
        workspace=workspace,
        labels={},
        command=["python", "flow.py"],
        image=None,
        software=None,
        env={},
        region=None,
        vm_types=None,
        arm=None,
        cpu=None,
        memory=None,
        gpu=None,
        additional_coiled_options=None,
    )


class CoiledWorkerTests(unittest.IsolatedAsyncioTestCase):
    async def test_concurrent_runs_use_request_specific_clouds(self):
        FakeCloud.instances = []
        submissions = []
        waiting = 0
        both_waiting = asyncio.Event()

        def submit_job(**kwargs):
            cloud = kwargs["cloud"]
            submissions.append(cloud)
            return {"job_id": cloud.token}

        def wait_for_job(job_id, cloud):
            self.assertEqual(job_id, cloud.token)
            self.assertFalse(cloud.closed)
            return {}

        async def run_in_worker_thread(function, **kwargs):
            nonlocal waiting
            waiting += 1
            if waiting == 2:
                self.assertEqual(
                    sum(not instance.closed for instance in FakeCloud.instances), 2
                )
                both_waiting.set()
            await both_waiting.wait()
            return function(**kwargs)

        worker = FakeWorker()
        flow_run = SimpleNamespace()

        with (
            patch.object(coiled, "Cloud", FakeCloud),
            patch.object(coiled.batch, "run", submit_job),
            patch.object(coiled.batch, "wait_for_job_done", wait_for_job),
            patch(
                "prefect_coiled.worker.run_sync_in_worker_thread",
                run_in_worker_thread,
            ),
        ):
            results = await asyncio.gather(
                CoiledWorker.run(
                    worker, flow_run, configuration("token-a", "workspace-a")
                ),
                CoiledWorker.run(
                    worker, flow_run, configuration("token-b", "workspace-b")
                ),
            )

        self.assertEqual(
            [result.identifier for result in results], ["token-a", "token-b"]
        )
        self.assertEqual(
            [(cloud.token, cloud.workspace) for cloud in submissions],
            [("token-a", "workspace-a"), ("token-b", "workspace-b")],
        )
        self.assertEqual(len({id(cloud) for cloud in submissions}), 2)
        self.assertTrue(all(cloud.closed for cloud in submissions))
