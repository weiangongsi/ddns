"""ali dns client."""

import asyncio
from functools import partial
import logging
import sys
from typing import Optional

from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.dnspod.v20210323 import models
from tencentcloud.dnspod.v20210323.dnspod_client import DnspodClient

logging.basicConfig(level=logging.INFO)


class TencentdnsClient(DnspodClient):
    """ali dns."""

    def __init__(
        self,
        secret_id,
        secret_key,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ):
        cred = credential.Credential(secret_id, secret_key)
        httpProfile = HttpProfile()
        httpProfile.endpoint = "dnspod.tencentcloudapi.com"
        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        super().__init__(credential=cred, region="", profile=clientProfile)
        self.loop = loop or asyncio.get_event_loop()
        assert self.loop is not None
        if sys.platform == "win32":
            if not isinstance(self.loop, asyncio.SelectorEventLoop):
                try:
                    import winloop

                    if not isinstance(self.loop, winloop.Loop):
                        raise RuntimeError("needs a SelectorEventLoop on Windows.")
                except ModuleNotFoundError:
                    raise RuntimeError("needs a SelectorEventLoop on Windows.")

    async def describeRecordList(
        self,
        request: models.DescribeRecordListRequest,
    ) -> models.DescribeRecordListResponse:
        return await self.loop.run_in_executor(
            None,
            partial(self.DescribeRecordList, request),
        )

    async def createRecord(
        self,
        request: models.CreateRecordRequest,
    ) -> models.CreateRecordResponse:
        return await self.loop.run_in_executor(
            None,
            partial(self.CreateRecord, request),
        )

    async def modifyRecord(
        self,
        request: models.ModifyRecordRequest,
    ) -> models.ModifyRecordResponse:
        return await self.loop.run_in_executor(
            None,
            partial(self.ModifyRecord, request),
        )
