import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def route_table(ip):
    url = (
        f"https://{ip}/restconf/data/"
        "ietf-routing:routing-state/routing-instance=default/"
        "ribs/rib=ipv4-default/routes/route"
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
