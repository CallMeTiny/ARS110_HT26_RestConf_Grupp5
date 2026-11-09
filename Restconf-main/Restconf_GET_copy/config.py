import ipaddress


routers = {
    "OVERBY": "1.1.1.1",
    "TRESTAD": "1.1.1.2",
    "TORP": "1.1.1.3"
}

mgmt_net = ipaddress.IPv4Network("1.1.1.0/24")
