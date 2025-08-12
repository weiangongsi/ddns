"""Config flow for ddns."""

from __future__ import annotations

import asyncio
import contextlib
from typing import Any

import aiodns
from aiodns.error import DNSError
from alibabacloud_alidns20150109 import models as alidns_models
from alibabacloud_tea_openapi import models as open_api_models
from Tea.exceptions import TeaException
from tencentcloud.common.exception.tencent_cloud_sdk_exception import (
    TencentCloudSDKException,
)
from tencentcloud.dnspod.v20210323 import models as tencent_models
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers import selector

from .alidns import AlidnsClient
from .const import (
    CONF_ALI_ACCESS_KEY_ID,
    CONF_ALI_ACCESS_KEY_SECRET,
    CONF_DNS_SERVER,
    CONF_DNS_SERVER_ALI,
    CONF_DNS_SERVER_TENCENT,
    CONF_DOMAIN_NAME,
    CONF_DOMAIN_RR,
    CONF_TENCENT_SECRET_ID,
    CONF_TENCENT_SECRET_KEY,
    DNS_HOSTNAME,
    DNS_IPV4_TYPE,
    DNS_IPV6_TYPE,
    DNS_PORT,
    DNS_RESOLVER,
    DNS_RESOLVER_IPV6,
    DNS_TYPE,
    DOMAIN,
)
from .tencentdns import TencentdnsClient

data_schema_dns_server = vol.Schema(
    {
        vol.Required(
            CONF_DNS_SERVER, default=CONF_DNS_SERVER_ALI
        ): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[
                    CONF_DNS_SERVER_ALI,
                    CONF_DNS_SERVER_TENCENT,
                ],
                translation_key=CONF_DNS_SERVER,
            ),
        )
    }
)

data_schema_ali_access = vol.Schema(
    {
        vol.Required(CONF_ALI_ACCESS_KEY_ID): str,
        vol.Required(CONF_ALI_ACCESS_KEY_SECRET): str,
        vol.Required(DNS_TYPE, default=DNS_IPV4_TYPE): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[
                    DNS_IPV4_TYPE,
                    DNS_IPV6_TYPE,
                ],
                translation_key=DNS_TYPE,
            ),
        ),
        vol.Required(CONF_DOMAIN_RR): str,
        vol.Required(CONF_DOMAIN_NAME): str,
    }
)

data_schema_tencent_access = vol.Schema(
    {
        vol.Required(CONF_TENCENT_SECRET_ID): str,
        vol.Required(CONF_TENCENT_SECRET_KEY): str,
        vol.Required(DNS_TYPE, default=DNS_IPV4_TYPE): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[
                    DNS_IPV4_TYPE,
                    DNS_IPV6_TYPE,
                ],
                translation_key=DNS_TYPE,
            ),
        ),
        vol.Required(CONF_DOMAIN_RR): str,
        vol.Required(CONF_DOMAIN_NAME): str,
    }
)


async def async_validate_ali(
    access_key_id: str, access_key_secret: str, dns_type: str, rr: str, domain_name: str
) -> str:
    """Validate ali."""

    async def async_check_dns_type(dns_type: str) -> bool:
        """Return if able to resolve hostname."""

        result = False
        with contextlib.suppress(DNSError):
            dns_resolver = (
                DNS_RESOLVER if dns_type == DNS_IPV4_TYPE else DNS_RESOLVER_IPV6
            )
            _resolver = aiodns.DNSResolver(
                nameservers=[dns_resolver], udp_port=DNS_PORT, tcp_port=DNS_PORT
            )
            result = bool(
                await _resolver.query(host=DNS_HOSTNAME, qtype=dns_type.upper())
            )
        return result

    async def async_check_ali(
        access_key_id: str,
        access_key_secret: str,
        dns_type: str,
        rr: str,
        domain_name: str,
    ) -> str:
        """Return error code."""

        try:
            config = open_api_models.Config(
                access_key_id=access_key_id, access_key_secret=access_key_secret
            )
            config.endpoint = "alidns.cn-hangzhou.aliyuncs.com"
            client = AlidnsClient(config)
            request = alidns_models.DescribeSubDomainRecordsRequest()
            request.sub_domain = rr + "." + domain_name
            request.type = dns_type.upper()
            await client.describe_sub_domain_records_async(request)
        except TeaException as e:
            return e.code
        except Exception:  # noqa: BLE001
            return "invalid_params"

    tasks = await asyncio.gather(
        async_check_dns_type(dns_type),
        async_check_ali(access_key_id, access_key_secret, dns_type, rr, domain_name),
    )
    validate_dns_type = tasks[0]
    if not validate_dns_type:
        return "NotFind" + dns_type + "Ip"
    return tasks[1]


async def async_validate_tencent(
    secret_id: str, secret_key: str, dns_type: str, rr: str, domain_name: str
) -> str:
    """Validate ali."""

    async def async_check_dns_type(dns_type: str) -> bool:
        """Return if able to resolve hostname."""

        result = False
        with contextlib.suppress(DNSError):
            dns_resolver = (
                DNS_RESOLVER if dns_type == DNS_IPV4_TYPE else DNS_RESOLVER_IPV6
            )
            _resolver = aiodns.DNSResolver(
                nameservers=[dns_resolver], udp_port=DNS_PORT, tcp_port=DNS_PORT
            )
            result = bool(
                await _resolver.query(host=DNS_HOSTNAME, qtype=dns_type.upper())
            )
        return result

    async def async_check_tencent(
        secret_id: str,
        secret_key: str,
        dns_type: str,
        rr: str,
        domain_name: str,
    ) -> str:
        """Return error code."""

        try:
            client = TencentdnsClient(secret_id, secret_key)
            req = tencent_models.DescribeRecordListRequest()
            req.Domain = domain_name
            req.Subdomain = rr
            req.RecordType = dns_type.upper()
            await client.describeRecordList(req)
        except TencentCloudSDKException as e:
            if e.code != "ResourceNotFound.NoDataOfRecord":
                return e.code
        except Exception:  # noqa: BLE001
            return "invalid_params"

    tasks = await asyncio.gather(
        async_check_dns_type(dns_type),
        async_check_tencent(secret_id, secret_key, dns_type, rr, domain_name),
    )
    validate_dns_type = tasks[0]
    if not validate_dns_type:
        return "NotFind" + dns_type + "Ip"
    return tasks[1]


class DdnsConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for WanIp."""

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""

        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=data_schema_dns_server
            )
        if user_input[CONF_DNS_SERVER] == CONF_DNS_SERVER_ALI:
            return await self.async_step_ali()

        return await self.async_step_tencent()

    async def async_step_ali(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the ali step."""

        if user_input is None:
            return self.async_show_form(
                step_id="ali",
                data_schema=data_schema_ali_access,
            )
        access_key_id = user_input.get(CONF_ALI_ACCESS_KEY_ID)
        access_key_secret = user_input.get(CONF_ALI_ACCESS_KEY_SECRET)
        dns_type = user_input.get(DNS_TYPE)
        rr = user_input.get(CONF_DOMAIN_RR)
        domain_name = user_input.get(CONF_DOMAIN_NAME)
        domain = rr + "." + domain_name

        error_code = await async_validate_ali(
            access_key_id, access_key_secret, dns_type, rr, domain_name
        )
        if error_code:
            return self.async_show_form(
                step_id="ali",
                data_schema=data_schema_ali_access,
                errors={"base": error_code},
            )
        unique_id = f"{domain}_{dns_type}"
        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=domain,
            data={
                CONF_DNS_SERVER: CONF_DNS_SERVER_ALI,
                CONF_ALI_ACCESS_KEY_ID: access_key_id,
                CONF_ALI_ACCESS_KEY_SECRET: access_key_secret,
                DNS_TYPE: dns_type,
                CONF_DOMAIN_RR: rr,
                CONF_DOMAIN_NAME: domain_name,
            },
        )

    async def async_step_tencent(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the tencent step."""

        if user_input is None:
            return self.async_show_form(
                step_id="tencent",
                data_schema=data_schema_tencent_access,
            )
        secret_id = user_input.get(CONF_TENCENT_SECRET_ID)
        secret_key = user_input.get(CONF_TENCENT_SECRET_KEY)
        dns_type = user_input.get(DNS_TYPE)
        rr = user_input.get(CONF_DOMAIN_RR)
        domain_name = user_input.get(CONF_DOMAIN_NAME)
        domain = rr + "." + domain_name

        error_code = await async_validate_tencent(
            secret_id, secret_key, dns_type, rr, domain_name
        )
        if error_code:
            return self.async_show_form(
                step_id="ali",
                data_schema=data_schema_tencent_access,
                errors={"base": error_code},
            )
        unique_id = f"{domain}_{dns_type}"
        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=domain,
            data={
                CONF_DNS_SERVER: CONF_DNS_SERVER_TENCENT,
                CONF_TENCENT_SECRET_ID: secret_id,
                CONF_TENCENT_SECRET_KEY: secret_key,
                DNS_TYPE: dns_type,
                CONF_DOMAIN_RR: rr,
                CONF_DOMAIN_NAME: domain_name,
            },
        )
