import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_serial_ints(ip):
    url = f"https://{ip}/restconf/data/Cisco-IOS-XE-native:native/interface/Serial"

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

    if response.status_code != 200:
        return None

    return response.text
