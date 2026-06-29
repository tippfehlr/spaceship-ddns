"""
Update the DDNS record of a domain registered with spaceship
(https://www.spaceship.com/). You can get the API key and secret from
spaceship's website.
"""

import argparse
import datetime
import os

import requests

ENDPOINT = "https://spaceship.dev/api/v1/dns/records"

IPV4_URL = "https://api.ipify.org"
IPV6_URL = "https://api64.ipify.org"


def get_env_var(variable_name: str, required: bool = True):
    value = os.getenv(variable_name)

    if value is None and required:
        raise ValueError(
            f"Please use the CLI arguments or set the {variable_name} "
            "environment variable"
        )

    return value


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-d", "--domain",
        type=str,
        help="Domain to update",
        required=False,
    )
    parser.add_argument(
        "-k", "--api-key",
        type=str,
        help="API key",
        required=False,
    )
    parser.add_argument(
        "-s", "--api-secret",
        type=str,
        help="API secret",
        required=False,
    )
    parser.add_argument(
        "-N", "--name",
        type=str,
        help="Target DNS name(s). Use @ for domain root. "
             "Comma-separated for multiple names applied to the same domain.",
        required=False,
    )
    parser.add_argument(
        "-6", "--ipv6",
        action="store_const",
        const=True,
        default=False,
        help="Only update AAAA (IPv6) records",
    )
    parser.add_argument(
        "--ipv4-only",
        action="store_const",
        const=True,
        default=False,
        help="Only update A (IPv4) records",
    )
    args = parser.parse_args()

    api_key: str | None = args.api_key
    if api_key is None:
        api_key = get_env_var("SPACESHIP_DDNS_API_KEY")

    api_secret: str | None = args.api_secret
    if api_secret is None:
        api_secret = get_env_var("SPACESHIP_DDNS_API_SECRET")

    domain: str | None = args.domain
    if domain is None:
        domain = get_env_var("SPACESHIP_DDNS_DOMAIN")

    names_str: str | None = args.name
    if names_str is None:
        names_str = get_env_var("SPACESHIP_DDNS_NAMES", required=False)
    if names_str:
        names = [n.strip() for n in names_str.split(",") if n.strip()]
    else:
        names = ["@"]

    ipv6 = args.ipv6
    ipv4_only = args.ipv4_only

    update_aaaa = ipv6 or not ipv4_only
    update_a = not ipv6 or not ipv4_only

    return domain, names, api_key, api_secret, update_a, update_aaaa


def get_dns_entries(domain: str, api_key: str, api_secret: str):
    url = f"{ENDPOINT}/{domain}?take=500&skip=0"

    headers = {
        "X-API-Key": api_key,
        "X-API-Secret": api_secret,
    }
    response = requests.get(url, headers=headers)

    response_text = response.content.decode("utf8")
    date = datetime.datetime.now(tz=datetime.UTC).strftime("%Y-%m-%d_%H-%M-%S")
    print(f"(UTC) {date} HTTP {response.status_code} {response_text}")

    return response.json()["items"]


def delete_dns_entry(
    domain: str,
    api_key: str,
    api_secret: str,
    name: str,
    address: str,
    record_type: str = "A",
):
    url = f"{ENDPOINT}/{domain}"

    payload = [
        {
            "type": record_type,
            "name": name,
            "address": address,
        }
    ]
    headers = {
        "X-API-Key": api_key,
        "X-API-Secret": api_secret,
        "content-type": "application/json"
    }
    response = requests.delete(url, json=payload, headers=headers)

    response_text = response.content.decode("utf8")
    date = datetime.datetime.now(tz=datetime.UTC).strftime("%Y-%m-%d_%H-%M-%S")
    print(f"(UTC) {date} HTTP {response.status_code} {response_text}")
    print(payload)


def add_dns_entry(
    domain: str,
    api_key: str,
    api_secret: str,
    name: str,
    address: str,
    record_type: str = "A",
):
    url = f"{ENDPOINT}/{domain}"

    payload = {
        "force": True,
        "items": [
            {
                "type": record_type,
                "name": name,
                "address": address,
                "ttl": 1800,
            },
        ],
    }
    headers = {
        "X-API-Key": api_key,
        "X-API-Secret": api_secret,
        "content-type": "application/json",
    }
    response = requests.put(url, json=payload, headers=headers)

    response_text = response.content.decode("utf8")
    date = datetime.datetime.now(tz=datetime.UTC).strftime("%Y-%m-%d_%H-%M-%S")
    print(f"(UTC) {date} HTTP {response.status_code} {response_text}")
    print(payload)


def get_current_address(ipv6: bool) -> str | None:
    try:
        url = IPV6_URL if ipv6 else IPV4_URL
        return requests.get(url).content.decode("utf8")
    except requests.RequestException:
        return None


def update_domain(
    domain: str,
    api_key: str,
    api_secret: str,
    name: str,
    update_a: bool,
    update_aaaa: bool,
):
    current_ipv4 = None
    current_ipv6 = None

    if update_a:
        current_ipv4 = get_current_address(ipv6=False)
        if current_ipv4 is None:
            print("Warning: Unable to retrieve current IPv4 address")

    if update_aaaa:
        current_ipv6 = get_current_address(ipv6=True)
        if current_ipv6 is None:
            print("Warning: Unable to retrieve current IPv6 address")

    dns_entries = get_dns_entries(domain, api_key, api_secret)

    for entry in dns_entries:
        entry_name = entry.get("name")
        entry_type = entry.get("type")
        entry_address = entry.get("address")

        if entry_name != name:
            continue

        if entry_type == "A" and update_a and entry_address != current_ipv4:
            delete_dns_entry(
                domain=domain,
                api_key=api_key,
                api_secret=api_secret,
                name=name,
                address=entry_address,
                record_type="A",
            )

        if entry_type == "AAAA" and update_aaaa and entry_address != current_ipv6:
            delete_dns_entry(
                domain=domain,
                api_key=api_key,
                api_secret=api_secret,
                name=name,
                address=entry_address,
                record_type="AAAA",
            )

    if update_a and current_ipv4:
        dns_entry_exists = any(
            e.get("name") == name and e.get("type") == "A"
            for e in dns_entries
        )
        if not dns_entry_exists:
            add_dns_entry(
                domain=domain,
                api_key=api_key,
                api_secret=api_secret,
                name=name,
                address=current_ipv4,
                record_type="A",
            )

    if update_aaaa and current_ipv6:
        dns_entry_exists = any(
            e.get("name") == name and e.get("type") == "AAAA"
            for e in dns_entries
        )
        if not dns_entry_exists:
            add_dns_entry(
                domain=domain,
                api_key=api_key,
                api_secret=api_secret,
                name=name,
                address=current_ipv6,
                record_type="AAAA",
            )


def main():
    domain, names, api_key, api_secret, update_a, update_aaaa = parse_args()

    assert api_key is not None
    assert api_secret is not None
    assert domain is not None

    for name in names:
        update_domain(domain, api_key, api_secret, name, update_a, update_aaaa)


if __name__ == "__main__":
    main()
