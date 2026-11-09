import moduls_restconf
import time

YANG = "ietf-interfaces:interfaces"

routers = {
    "1.1.1.1": {
        "0/0/0": {
            "enabled": True,
            "ip": "192.168.11.1",
            "prefix": "255.255.255.192",
            "description": "Connected --> HostBK"
        },
       "0/0/1": {
            "enabled": True,
            "ip": "192.168.11.65",
            "prefix": "255.255.255.252",
            "description": "Connected --> Router-TRESTAD"
        }
    },
    "1.1.1.2": {
        "0/0/0": {
            "enabled": False
        },
       "0/0/1": {
            "enabled": True,
            "ip": "192.168.11.66",
            "prefix": "255.255.255.252",
            "description": "Connected --> Router-OVERBY"
        }
    },
    "1.1.1.3": {
        "0/0/0": {
            "enabled": True,
            "ip": "192.168.42.1",
            "prefix": "255.255.255.0",
            "description": "Connected --> HostMC"
        },
        "0/0/1": {
            "enabled": False
        }        
    }
}

def interface_conf(host, interface, config):
    
    if config["enabled"] == False:
        data = {
            "ietf-interfaces:interfaces": {
                "interface": [
                    {
                        "name": f"GigabitEthernet{interface}",
                        "type": "iana-if-type:ethernetCsmacd",
                        "enabled": False,
                    }
                ]
            }
        }
        
    else:
        data = {
            "ietf-interfaces:interfaces": {
                "interface": [
                    {
                        "name": f"GigabitEthernet{interface}",
                        "description": config["description"],
                        "type": "iana-if-type:ethernetCsmacd",
                        "enabled": True,
                        "ietf-ip:ipv4": {
                            "address": [
                                {
                                    "ip": config["ip"], 
                                    "netmask": config["prefix"]
                                }
                            ]
                        }
                    }
                ]
            }
        }

    moduls_restconf.patch(host, YANG, data)



def main():
    for host, interfaces in routers.items():
        for interface, config in interfaces.items():
            interface_conf(host, interface, config)

        time.sleep(1)
        moduls_restconf.save(host)

if __name__ == "__main__":
    main()





