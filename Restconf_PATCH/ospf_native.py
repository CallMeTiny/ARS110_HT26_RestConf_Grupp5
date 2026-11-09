import moduls_restconf


YANG_ROUTER = "Cisco-IOS-XE-native:native/router"
YANG_INTERFACE = "Cisco-IOS-XE-native:native/interface"


routers = {
    "1.1.1.1": {  # OVERBY
        "networks": [
            ["192.168.11.0", "0.0.0.63"],
            ["192.168.11.64", "0.0.0.3"]
        ],

        "passive": [
            "GigabitEthernet0/0/0"
        ],

        "auth_interfaces": [
            "GigabitEthernet0/0/0",
            "GigabitEthernet0/0/1"
        ],

        "default_originate": False
    },

    "1.1.1.2": {  # TRESTAD
        "networks": [
            ["192.168.11.64", "0.0.0.3"],
            ["192.168.11.68", "0.0.0.3"]
        ],

        "passive": [],

        "auth_interfaces": [
            "GigabitEthernet0/0/1"
        ],

        "default_originate": True
    }
}


def ospf_conf(host, config):

    networks = []

    for network in config["networks"]:
        networks.append(
            {
                "ip": network[0],
                "wildcard": network[1],
                "area": 0
            }
        )

    process = {
        "id": 1,

        "area": [
            {
                "area-id": 0,
                "authentication": {}
            }
        ],

        "network": networks
    }

    # Passive interface
    if config["passive"]:
        process["passive-interface"] = {
            "interface": config["passive"]
        }

    # Default-information originate
    if config["default_originate"]:
        process["default-information"] = {
            "originate": {}
        }

    data = {
        "Cisco-IOS-XE-native:router": {
            "Cisco-IOS-XE-ospf:router-ospf": {
                "ospf": {
                    "process-id": [
                        process
                    ]
                }
            }
        }
    }

    response = moduls_restconf.patch(host,YANG_ROUTER,data)

    if response is None:
        return

    response.raise_for_status()


def ospf_auth_conf(host, interface):

    if interface.startswith("GigabitEthernet"):

        interface_type = "GigabitEthernet"

        interface_name = interface.replace(
            "GigabitEthernet",
            ""
        )

    elif interface.startswith("Serial"):

        interface_type = "Serial"

        interface_name = interface.replace(
            "Serial",
            ""
        )

    else:
        raise ValueError(
            f"Okänd interface-typ: {interface}"
        )

    encoded_name = interface_name.replace("/", "%2F")

    YANG = (
        f"{YANG_INTERFACE}/"
        f"{interface_type}={encoded_name}"
    )

    data = {
        f"Cisco-IOS-XE-native:{interface_type}": {

            "name": interface_name,

            "ip": {
                "Cisco-IOS-XE-ospf:router-ospf": {
                    "ospf": {

                        "authentication": {
                            "clear-text": [
                                None
                            ]
                        },

                        "authentication-key": {
                            "auth-key": "cisco"
                        }
                    }
                }
            }
        }
    }

    response = moduls_restconf.patch(host,YANG,data)

    if response is None:
        return

    response.raise_for_status()


def main():

    for host, config in routers.items():

        ospf_conf(host, config)

        for interface in config["auth_interfaces"]:
            ospf_auth_conf(host, interface)


if __name__ == "__main__":
    main()
