import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_ospf(ip):
    url = (
        f"https://{ip}/restconf/data/"
        "Cisco-IOS-XE-ospf-oper:ospf-oper-data/"
        "ospf-state/ospf-instance"
    )

    headers = {
        "Accept": "application/yang-data+json",
        "Authorization": "Basic YWRtaW46TmV0d29yayEzMzc="
    }

    response = requests.get(
        url,
        headers=headers,
        verify=False,
        timeout=20
    )

    return response.text
