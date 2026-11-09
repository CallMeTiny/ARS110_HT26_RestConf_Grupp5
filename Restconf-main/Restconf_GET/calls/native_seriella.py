import requests
import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_serial_ints(ip):
    url = f"https://{ip}/restconf/data/Cisco-IOS-XE-native:native/interface/Serial"
    headers = {
        'Accept': 'application/yang-data+json',
        'Authorization': 'Basic Y2hyYmVuMDE6Y2lzY28='
    }
    response = requests.get(url, headers=headers, verify=False)
    
    if response.status_code != 200:
        return None

    return response.text
