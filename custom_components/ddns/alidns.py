"""ali dns client."""

import asyncio
from functools import partial
import logging
import sys
from typing import Optional

from alibabacloud_alidns20150109 import models as alidns_20150109_models
from alibabacloud_alidns20150109.client import Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_tea_util import models as util_models

logging.basicConfig(level=logging.INFO)


class AlidnsClient(Client):
    """ali dns."""

    def __init__(
        self,
        config: open_api_models.Config,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ):
        super().__init__(config)
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

    async def describe_sub_domain_records_async(
        self,
        request: alidns_20150109_models.DescribeSubDomainRecordsRequest,
    ) -> alidns_20150109_models.DescribeSubDomainRecordsResponse:
        runtime = util_models.RuntimeOptions()
        return await self.loop.run_in_executor(
            None,
            partial(self.describe_sub_domain_records_with_options, request, runtime),
        )

    async def add_domain_record_async(
        self,
        request: alidns_20150109_models.AddDomainRecordRequest,
    ) -> alidns_20150109_models.AddDomainRecordResponse:
        runtime = util_models.RuntimeOptions()
        return await self.loop.run_in_executor(
            None,
            partial(self.add_domain_record_with_options, request, runtime),
        )

    async def update_domain_record_async(
        self,
        request: alidns_20150109_models.UpdateDomainRecordRequest,
    ) -> alidns_20150109_models.UpdateDomainRecordResponse:
        runtime = util_models.RuntimeOptions()
        return await self.loop.run_in_executor(
            None,
            partial(self.update_domain_record_with_options, request, runtime),
        )
