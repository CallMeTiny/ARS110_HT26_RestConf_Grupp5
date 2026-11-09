import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def base_int(router):
    """Hämta interfacekonfiguration från routerns IP-adress."""
    url = f"https://{router}/restconf/data/ietf-interfaces:interfaces"

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
