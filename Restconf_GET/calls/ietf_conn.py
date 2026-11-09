import requests
import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_routes(routers):
    pass
def parse_torp_conn(torp_ip):
    """
        Hämtar enbart TORP routerns directly connected routes för antingen 
        192.168.11.0/24 | 192.168.42.0/24
        om den finns kommer payloaden returneras
        Med en sant/falsk flagga för vilken IP som satts upp.
        För att sedan verifiera att IP utrymmet inte används för andra länkar
        Detta görs via get_routes.
        Eftersom om den används i resterande länkar samtidigt är det fel.
    """ 
    #oct_one, oct_two, oct_three, oct_four = torp_ip
    check_24 = ''
    payload = ""
    headers = {
      'Accept': 'application/yang-data+json',
      'Content-Type': 'application/yang-data+json',
      'Authorization': 'Basic Y2hyYmVuMDE6Y2lzY28='
    }
    # Skicka reqs för TORPs directly connected antingen .11.0 eller .42.0 för att se om dem finns
    url_elvn = f"https://{torp_ip}/restconf/data/ietf-routing:routing-state/routing-instance=default/ribs/rib=ipv4-default/routes/route=192.168.11.0%2F24"
    url_frtw = "https://192.168.0.63/restconf/data/ietf-routing:routing-state/routing-instance=default/ribs/rib=ipv4-default/routes/route=192.168.42.0%2F24"
    next_hop = '"next-hop-address": "0.0.0.0"'
    for i in range(1):
        response1 = requests.request("GET", url_frtw, headers=headers, data=payload, verify=False)
        response2 = requests.request("GET", url_elvn, headers=headers, data=payload, verify=False)
        #json_elvn = json.loads(str(response2))
        print(response2)
        if response1.text == '' and response2.text != '': 
            if next_hop in response2.text:
                print("192.168.11.0/24 is directly connected")
                print(response2.text)
                return response2.text
            else:
                raise ValueError('192.168.0.11/24 is not directly connnected!')
        elif response2.text == '' and response1.text != '':
            if next_hop in response1.text:
                print("192.168.42.0/24 is directly connected")
                return response1.text
            else:
                raise ValueError('192.168.42.0/24 not directly connected!')
        elif response1.text == '' and response2.text == '':
            raise AttributeError("NO /24")




