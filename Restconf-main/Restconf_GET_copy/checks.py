import json
import ipaddress

from config import routers
from calls.ietf_int import base_int
from calls.native_seriella import get_serial_ints
from calls.ietf_route import route_table
from calls.ios_xe_ospf import get_ospf


EXPECTED_IPS = {
    "OVERBY": {
        "GigabitEthernet0/0/0": "192.168.11.1/26",
        "GigabitEthernet0/0/1": "192.168.11.65/30",
    },
    "TRESTAD": {
        "GigabitEthernet0/0/1": "192.168.11.66/30",
        "Serial0/1/0": "192.168.11.69/30",
    },
    "TORP": {
        "GigabitEthernet0/0/0": "192.168.42.1/24",
        "Serial0/1/0": "192.168.11.70/30",
    },
}

EXPECTED_ROUTES = {
    "OVERBY": [
        ("0.0.0.0/0", "ietf-ospf:ospfv2", "192.168.11.66"),
        ("192.168.11.68/30", "ietf-ospf:ospfv2", "192.168.11.66"),
    ],
    "TRESTAD": [
        ("0.0.0.0/0", "ietf-routing:static", "192.168.11.70"),
        ("192.168.11.0/26", "ietf-ospf:ospfv2", "192.168.11.65"),
    ],
    "TORP": [
        ("192.168.11.0/26", "ietf-routing:static", "192.168.11.69"),
    ],
}


# ===== HÄMTA SERIAL =====

def serial_interfaces(rtr):
    output = get_serial_ints(routers[rtr])

    if not output:
        raise ValueError(f"Kunde inte hämta serialinterface på {rtr}")

    data = json.loads(output)
    interfaces = data["Cisco-IOS-XE-native:Serial"]

    if isinstance(interfaces, dict):
        interfaces = [interfaces]

    return interfaces


# ===== INTERFACE OCH BESKRIVNINGAR =====

def check_desc(rtr):
    errors = []
    int_list = []

    try:
        data = json.loads(base_int(routers[rtr]))
        int_list = data["ietf-interfaces:interfaces"]["interface"]
    except (ValueError, KeyError, TypeError) as error:
        errors.append(f"INTERFACE GET ERROR {rtr}: {error}")

    # Kontrollera de GigabitEthernet-interface som uppgiften använder.
    for name in EXPECTED_IPS[rtr]:
        if name.startswith("Serial"):
            continue

        interface = next(
            (item for item in int_list if item.get("name") == name),
            None,
        )

        if interface is None:
            errors.append(f"MISSING INTERFACE {rtr}: {name}")
            continue

        if not interface.get("enabled", True):
            errors.append(f"INTERFACE DISABLED {rtr}: {name}")

        if not interface.get("description", "").strip():
            errors.append(f"NO DESCRIPTION {rtr}: {name}")

    if rtr in ["TRESTAD", "TORP"]:
        try:
            interfaces = serial_interfaces(rtr)
            interface = next(
                (
                    item for item in interfaces
                    if item.get("name") == "0/1/0"
                ),
                None,
            )

            if interface is None:
                errors.append(f"MISSING INTERFACE {rtr}: Serial0/1/0")
            else:
                if "shutdown" in interface:
                    errors.append(
                        f"INTERFACE DISABLED {rtr}: Serial0/1/0"
                    )

                if not interface.get("description", "").strip():
                    errors.append(
                        f"NO DESCRIPTION {rtr}: Serial0/1/0"
                    )

        except (ValueError, KeyError, TypeError) as error:
            errors.append(f"SERIAL GET ERROR {rtr}: {error}")

    return int_list, errors


# ===== HÄMTA ADRESSER PER INTERFACE =====

def check_subnets(int_lst, rtr):
    addresses = {}

    for interface in int_lst:
        name = interface.get("name")

        if name not in EXPECTED_IPS[rtr]:
            continue

        ipv4 = interface.get("ietf-ip:ipv4", {})

        for address in ipv4.get("address", []):
            mask = address.get("netmask")

            if mask is None:
                mask = address.get("prefix-length")

            if mask is not None:
                value = ipaddress.IPv4Interface(
                    f"{address['ip']}/{mask}"
                )
                addresses.setdefault(name, []).append(str(value))

    if rtr in ["TRESTAD", "TORP"]:
        try:
            for interface in serial_interfaces(rtr):
                if interface.get("name") != "0/1/0":
                    continue

                primary = (
                    interface.get("ip", {})
                    .get("address", {})
                    .get("primary", {})
                )

                if "address" in primary and "mask" in primary:
                    value = ipaddress.IPv4Interface(
                        f"{primary['address']}/{primary['mask']}"
                    )
                    addresses["Serial0/1/0"] = [str(value)]

        except (ValueError, KeyError, TypeError):
            # Saknad adress rapporteras av check_addressing.
            pass

    return {rtr: addresses}


# ===== ROUTING =====

def check_routes(rtr):
    errors = []

    try:
        data = json.loads(route_table(routers[rtr]))
        routes = data["ietf-routing:route"]
    except (ValueError, KeyError, TypeError) as error:
        return [f"ROUTING GET ERROR {rtr}: {error}"]

    for prefix, protocol, next_hop in EXPECTED_ROUTES[rtr]:
        found = any(
            route.get("destination-prefix") == prefix
            and route.get("source-protocol") == protocol
            and route.get("next-hop", {}).get("next-hop-address")
            == next_hop
            and "active" in route
            for route in routes
        )

        if not found:
            errors.append(
                f"ROUTE ERROR {rtr}: expected active {prefix} "
                f"via {next_hop}, protocol {protocol}"
            )

    if rtr == "TORP":
        for route in routes:
            protocol = route.get("source-protocol")

            if protocol not in [
                "ietf-routing:static",
                "ietf-routing:direct",
            ]:
                errors.append(
                    f"UNEXPECTED ROUTING PROTOCOL TORP: {protocol}"
                )

    return errors


# ===== KONTROLLERA EXAKTA IP-ADRESSER =====

def check_addressing(raw_data):
    errors = []
    all_ips = []

    for rtr, expected_interfaces in EXPECTED_IPS.items():
        actual_interfaces = raw_data.get(rtr, {})

        for name, expected_ip in expected_interfaces.items():
            actual = actual_interfaces.get(name, [])

            if actual != [expected_ip]:
                errors.append(
                    f"ADDRESS ERROR {rtr}/{name}: "
                    f"expected {expected_ip}, found {actual}"
                )

            for address in actual:
                all_ips.append(ipaddress.IPv4Interface(address).ip)

    if len(all_ips) != len(set(all_ips)):
        errors.append("ERROR: DUPLICATE ADDRESSING FOUND")

    if not errors:
        print("PASS: ALL EXPECTED INTERFACE ADDRESSES ARE CORRECT")

    return errors


# ===== OSPF AUTHENTICATION =====

def check_ospf_auth():
    errors = []
    correct = []

    for rtr in ["OVERBY", "TRESTAD"]:
        try:
            data = json.loads(get_ospf(routers[rtr]))
            instances = data["Cisco-IOS-XE-ospf-oper:ospf-instance"]

            if len(instances) != 1:
                errors.append(
                    f"OSPF INSTANCE ERROR {rtr}: "
                    f"expected 1, found {len(instances)}"
                )
                continue

            instance = instances[0]

            if instance.get("process-id") != 1:
                errors.append(f"OSPF PROCESS ERROR {rtr}: expected 1")

            areas = instance.get("ospf-area", [])

            if len(areas) != 1 or areas[0].get("area-id") != 0:
                errors.append(f"OSPF AREA ERROR {rtr}: expected area 0")
                continue

            interface = next(
                (
                    item for item in areas[0].get("ospf-interface", [])
                    if item.get("name") == "GigabitEthernet0/0/1"
                ),
                None,
            )

            if interface is None:
                errors.append(
                    f"MISSING OSPF INTERFACE: {rtr}/GigabitEthernet0/0/1"
                )
            elif (
                interface.get("authentication", {}).get("key-string")
                != "cisco"
            ):
                errors.append(
                    f"WRONG OSPF KEY: {rtr}/GigabitEthernet0/0/1"
                )
            else:
                correct.append(
                    f"CORRECT KEY: {rtr}/GigabitEthernet0/0/1"
                )

        except (ValueError, KeyError, TypeError) as error:
            errors.append(f"OSPF GET ERROR {rtr}: {error}")

    # Serialnyckeln kontrolleras separat i native-konfigurationen.
    try:
        interface = next(
            (
                item for item in serial_interfaces("TRESTAD")
                if item.get("name") == "0/1/0"
            ),
            None,
        )

        if interface is None:
            errors.append("MISSING INTERFACE: TRESTAD/Serial0/1/0")
        else:
            key = (
                interface.get("ip", {})
                .get("Cisco-IOS-XE-ospf:router-ospf", {})
                .get("ospf", {})
                .get("authentication-key", {})
                .get("auth-key")
            )

            if key == "cisco":
                correct.append("CORRECT KEY: TRESTAD/Serial0/1/0")
            else:
                errors.append("WRONG OSPF KEY: TRESTAD/Serial0/1/0")

    except (ValueError, KeyError, TypeError) as error:
        errors.append(f"SERIAL AUTH GET ERROR TRESTAD: {error}")

    return correct, errors
