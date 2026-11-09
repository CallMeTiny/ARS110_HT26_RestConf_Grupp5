import moduls_restconf

YANG = "ietf-routing:routing/routing-instance=default/routing-protocols"

routers = {
    "1.1.1.2": {
        "STATIC": ["0.0.0.0", 0, "192.168.11.70"]
    },

    "1.1.1.3": {
        "STATIC": ["192.168.11.0", 26, "192.168.11.69"],
        "STATIC": ["192.168.11.64", 30, "192.168.11.69"]
    }
}


def routing_conf(host, config):

    data = {
        "ietf-routing:routing-protocols": {
            "routing-protocol": [
                {
                    "type": "ietf-routing:static",
                    "name": "1",

                    "static-routes": {
                        "ietf-ipv4-unicast-routing:ipv4": {
                            "route": [
                                {
                                    "destination-prefix":
                                    f'{config["STATIC"][0]}/{config["STATIC"][1]}',

                                    "next-hop": {
                                        "next-hop-address":
                                        config["STATIC"][2]
                                     }
                                }
                            ]
                        }
                    }
                }
            ]
        }
    }

    moduls_restconf.patch(host, YANG, data)



def main():
    for host, config in routers.items():
        routing_conf(host, config)

if __name__ == "__main__":
    main()
