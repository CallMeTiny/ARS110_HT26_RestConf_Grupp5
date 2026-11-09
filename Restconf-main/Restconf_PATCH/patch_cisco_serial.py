import moduls_restconf
import time

YANG = "Cisco-IOS-XE-native:native/interface/Serial=0%2F1%2F0"
YANG_SHUT = "Cisco-IOS-XE-native:native/interface/Serial=0%2F1%2F1"


routers = {
    "1.1.1.2": {
        "ip": "192.168.11.69",
        "description": "Connected --> TORP",
        "ospf_auth": True,
        "acl": False,
        "clock_rate": "64000",
    },
    "1.1.1.3": {
        "ip": "192.168.11.70",
        "description": "Connected --> TRESTAD",
        "ospf_auth": False,
        "acl": "BLOCK_TELNET",
        "clock_rate": None,
    },
}


def interface_conf(host, config):
    data = {
        "name": "0/1/0",
        "description": config["description"],
        "ip": {
            "address": {
                "primary": {
                    "address": config["ip"],
                    "mask": "255.255.255.252",
                }
            }
        },
    }
    data_shut = {
            "name": "0/1/1",
            "shutdown": [None]
            }
    if config["ospf_auth"]:
        data["ip"]["Cisco-IOS-XE-ospf:router-ospf"] = {
            "ospf": {
                "authentication-key": {
                    "auth-key": "cisco"
                }
            }
        }

    if config["acl"]:
        data["ip"]["access-group"] = {
            "in": {
                "acl": {
                    "acl-name": config["acl"],
                    "in": [None],
                }
            }
        }

    if config["clock_rate"]:
        data["Cisco-IOS-XE-serial:DCE-mode-config"] = {
            "clock": {
                "rate": config["clock_rate"]
            }
        }

    payload = {
        "Cisco-IOS-XE-native:Serial": data
    }
    payload_shut = {
        "Cisco-IOS-XE-native:Serial": data_shut
            }

    response = moduls_restconf.patch(host, YANG, payload)
    response_shut = moduls_restconf.patch(host, YANG_SHUT, payload_shut)

    if response is None:
        return

    if not response.ok:
        return

    response.raise_for_status()


    time.sleep(5)
    moduls_restconf.no_shutdown(host, YANG)
    time.sleep(5)


def main():
    for host, config in routers.items():
        interface_conf(host, config)

if __name__ == "__main__":
    main()
