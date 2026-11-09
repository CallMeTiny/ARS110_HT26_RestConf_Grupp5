import requests
import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_ospf(ip):
    url = f"https://{ip}/restconf/data/Cisco-IOS-XE-ospf-oper:ospf-oper-data/ospf-state/ospf-instance"

    payload = ""
    headers = {
      'Accept': 'application/yang-data+json',
      'Content-Type': 'application/yang-data+json',
      'Authorization': 'Basic Y2hyYmVuMDE6Y2lzY28='
    }

    response = requests.request("GET", url, headers=headers, data=payload, verify=False)

    return response.text
