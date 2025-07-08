"""Sensor platform for local_ip."""

from __future__ import annotations

from datetime import timedelta
from ipaddress import IPv4Address, IPv6Address
import logging

import aiodns
from aiodns.error import DNSError
from alibabacloud_alidns20150109 import models as alidns_models
from alibabacloud_tea_openapi import models as open_api_models

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .alidns import AlidnsClient
from .const import (
    CONF_ALI_ACCESS_KEY_ID,
    CONF_ALI_ACCESS_KEY_SECRET,
    CONF_ALI_DOMAIN_NAME,
    CONF_ALI_DOMAIN_RR,
    CONF_DNS_SERVER,
    CONF_DNS_SERVER_ALI,
    DNS_HOSTNAME,
    DNS_IPV4_TYPE,
    DNS_IPV6_TYPE,
    DNS_PORT,
    DNS_RESOLVER,
    DNS_RESOLVER_IPV6,
    DNS_TYPE,
)

DEFAULT_RETRIES = 2
MAX_RESULTS = 10

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=60)


def sort_ips(ips: list, querytype: str) -> list:
    """Join IPs into a single string."""

    if querytype.lower() == DNS_IPV6_TYPE.lower():
        ips = [IPv6Address(ip) for ip in ips]
    else:
        ips = [IPv4Address(ip) for ip in ips]
    return [str(ip) for ip in sorted(ips)][:MAX_RESULTS]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the platform from config_entry."""

    dns_server = entry.data.get(CONF_DNS_SERVER)
    if dns_server == CONF_DNS_SERVER_ALI:
        access_key_id = entry.data.get(CONF_ALI_ACCESS_KEY_ID)
        access_key_secret = entry.data.get(CONF_ALI_ACCESS_KEY_SECRET)
        dns_type = entry.data.get(DNS_TYPE)
        rr = entry.data.get(CONF_ALI_DOMAIN_RR)
        domain_name = entry.data.get(CONF_ALI_DOMAIN_NAME)
        domain = rr + "." + domain_name
        async_add_entities(
            [
                AliDdns(
                    name=domain,
                    access_key_id=access_key_id,
                    access_key_secret=access_key_secret,
                    dns_type=dns_type,
                    rr=rr,
                    domain_name=domain_name,
                )
            ],
            update_before_add=True,
        )


class AliDdns(SensorEntity):
    """A aliddns sensor."""

    # _attr_has_entity_name = True
    _attr_translation_key = "aliddns"
    _unrecorded_attributes = frozenset({"aliDnsClient", "resolver"})

    def __init__(
        self,
        name: str,
        access_key_id: str,
        access_key_secret: str,
        dns_type: str,
        rr: str,
        domain_name: str,
        aliDnsClient: AlidnsClient = None,
        resolver: aiodns.DNSResolver = None,
    ) -> None:
        """Initialize the sensor."""
        self.name = name
        self._attr_name = name
        self._attr_unique_id = f"{name}"
        self._retries = DEFAULT_RETRIES
        if resolver is None:
            dns_resolver = (
                DNS_RESOLVER if dns_type == DNS_IPV4_TYPE else DNS_RESOLVER_IPV6
            )
            self.resolver = aiodns.DNSResolver(
                nameservers=[dns_resolver], tcp_port=DNS_PORT, udp_port=DNS_PORT
            )
        if aliDnsClient is None:
            config = open_api_models.Config(
                access_key_id=access_key_id, access_key_secret=access_key_secret
            )
            config.endpoint = "alidns.cn-hangzhou.aliyuncs.com"
            self.aliDnsClient = AlidnsClient(config)
        self.dns_type = dns_type.upper()
        self.rr = rr
        self.domain_name = domain_name
        self._attr_extra_state_attributes = {
            "domain": name,
            "resolver": DNS_RESOLVER,
            "type": self.dns_type,
        }
        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(name, rr, domain_name)},
            manufacturer="ocean",
            model="1.0.0",
            name="",
        )

    async def async_update(self) -> None:
        """Get the current DNS IP address for hostname."""

        try:
            response = await self.resolver.query(host=DNS_HOSTNAME, qtype=self.dns_type)
        except DNSError as err:
            _LOGGER.warning("Exception while resolving host: %s", err)
            self.resolver.cancel()
            response = None
        if response:
            sorted_ips = sort_ips(
                [res.host for res in response], querytype=self.dns_type
            )
            ip = sorted_ips[0]
            self._attr_native_value = sorted_ips[0]
            self._attr_extra_state_attributes["ip_addresses"] = sorted_ips
            self._attr_available = True
            request = alidns_models.DescribeSubDomainRecordsRequest()
            request.sub_domain = self.rr + "." + self.domain_name
            request.type = self.dns_type
            records = await self.aliDnsClient.describe_sub_domain_records_async(request)
            body = records.body
            total_count = body.total_count
            domain_records = body.domain_records
            if total_count == 0:
                request = alidns_models.AddDomainRecordRequest()
                request.domain_name = self.domain_name
                request.rr = self.rr
                request.type = self.dns_type
                request.value = ip
                await self.aliDnsClient.add_domain_record_async(request)
            else:
                record = domain_records.record[0]
                value = record.value
                if value != ip:
                    request = alidns_models.UpdateDomainRecordRequest()
                    request.record_id = record.record_id
                    request.rr = self.rr
                    request.type = self.dns_type
                    request.value = ip
                    await self.aliDnsClient.update_domain_record_async(request)
            self._retries = DEFAULT_RETRIES
        elif self._retries > 0:
            self._retries -= 1
        else:
            self._attr_available = False
