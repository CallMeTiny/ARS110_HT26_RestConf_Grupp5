import moduls_restconf

YANG_ACL = "openconfig-acl:acl"

host = "1.1.1.3"

ACL_name = "BLOCK_TELNET"

ACL = [
    {
        "sequence": 10,
        "source": "192.168.11.10/32",
        "protocol": "openconfig-packet-match-types:IP_TCP",
        "source_port": "ANY",
        "destination_port": 23,
        "action": "openconfig-acl:DROP"
    },
    {
        "sequence": 20,
        "protocol": "cisco-xe-openconfig-acl-ext:IP",
        "source_port": "ANY",
        "destination_port": "ANY",
        "action": "openconfig-acl:ACCEPT"
    }
]


def acl_conf(host):

    entries = []

    for rule in ACL:

        entry = {
            "sequence-id": rule["sequence"],

            "config": {
                "sequence-id": rule["sequence"]
            },

            "ipv4": {
                "config": {
                    "protocol": rule["protocol"]
                }
            },

            "transport": {
                "config": {
                    "source-port": rule["source_port"],
                    "destination-port": rule["destination_port"]
                }
            },

            "actions": {
                "config": {
                    "forwarding-action": rule["action"],
                    "log-action": "openconfig-acl:LOG_NONE"
                }
            }
        }

        if "source" in rule:
            entry["ipv4"]["config"]["source-address"] = rule["source"]

        entries.append(entry)

    data_ACL = {
        "openconfig-acl:acl": {
            "acl-sets": {
                "acl-set": [
                    {
                        "name": ACL_name,
                        "type": "openconfig-acl:ACL_IPV4",

                        "config": {
                            "name": ACL_name,
                            "type": "openconfig-acl:ACL_IPV4"
                        },

                        "acl-entries": {
                            "acl-entry": entries
                        }
                    }
                ]
            }
        }
    }

    moduls_restconf.patch(host, YANG_ACL, data_ACL)


def main():
    acl_conf(host)


if __name__ == "__main__":
    main()