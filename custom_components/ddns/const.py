"""DDNS constants."""

from homeassistant.const import Platform

DOMAIN = "ddns"
PLATFORMS = [Platform.SENSOR]

DNS_HOSTNAME = "myip.opendns.com"
DNS_RESOLVER = "208.67.222.222"
DNS_RESOLVER_IPV6 = "2620:119:53::53"
DNS_TYPE = "dns_type"
DNS_IPV4_TYPE = "a"
DNS_IPV6_TYPE = "aaaa"
DNS_PORT = 53

CONF_DNS_SERVER = "dns_server"
CONF_DNS_SERVER_ALI = "ali"
CONF_DNS_SERVER_TENCENT = "tencent"
CONF_ALI_ACCESS_KEY_ID = "access_key_id"
CONF_ALI_ACCESS_KEY_SECRET = "access_key_secret"
CONF_TENCENT_SECRET_ID = "secret_id"
CONF_TENCENT_SECRET_KEY = "secret_key"
CONF_DOMAIN_RR = "rr"
CONF_DOMAIN_NAME = "domain_name"
