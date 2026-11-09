# IMPORTED RESTCONF CALLS ----------------------------------------------------
from calls.ietf_int import base_int
from calls.native_seriella import get_serial_ints
# Nedan är slopad och utkommenterad, kommer ta bort calls/ modulen.
#from calls.ietf_conn import parse_torp_conn
from calls.open_acl import get_acl
from calls.ietf_route import route_table
from calls.ios_xe_ospf import get_ospf
# DEPENDENCIES
import json
import ipaddress
import itertools

# VARIABLES -------------------------------------------------------------------------------

# routers: en dict av "hostname: ip", byt ut med satt MGMT IP för varje router
routers = {"OVERBY": "1.1.1.1", "TRESTAD": "1.1.1.2", "TORP": "1.1.1.3"}

# ipaddress objekt för MGMT addresseringen, fyll i med MGMT subnet
# Används i check_addressing() funktionen, där den räknar mängden subnets enligt uppgiftens krav.
mgmt_net = ipaddress.IPv4Network('1.1.1.0/24')
# EXEC ----------------------------------------------------------------------------------

"""
calls/ är alla RESTCONF HTTPS calls som görs. Här finns username:pass strängen och de tar en ip som argument. 
Varje funktion hämtar data för att leta fel.
Fel tilläggs i en egen lista, vanligtvis vid namn "error" eller "err"
Det som är rätt tilläggs även i en egen lista.
main funktionen kallar sedan dessa funktioner, och skriver ut alla fel och rätt för sig.
Saker är inte "hardcoded" som t.ex vilka interfaces och inte.
Istället används dict keys vanligtvis för att iterera över output.
"""


# Kollar att varje interface som är enabled faktiskt har en description.
# För varje descriptionlös interface tillägs ett felmeddelande i errors[] listan.
# Dessa errors skrivs ut i main()
def check_desc(rtr):
    errors = []
    for key in routers:
        ip = routers[key]
        if key == rtr:
            output = base_int(str(ip))
            intf = json.loads(output)
            base = intf['ietf-interfaces:interfaces']
            int_list = base['interface']
            enabled = 0
            descs = 0
            description = 0
            for i in int_list:
                if i['enabled'] == True:
                    enabled += 1
                    curr_name = i['name']
                    if curr_name != 'GigabitEthernet0':
                        try:
                            if i['description'] != '':
                                pass
                        except KeyError as exc:
                            error = f'{rtr}/{curr_name}'
                            errors.append(error)
            
            # Nedan triggas om rtr är TRESTAD/TORP
            # Kollar descriptions för interfaces med seriella länkar.

            if rtr in ['TRESTAD', 'TORP']:
                serial_output = get_serial_ints(ip)
                if serial_output:
                    serial_data = json.loads(serial_output)
                    for s_int in serial_data.get('Cisco-IOS-XE-native:Serial', []):
                        if 'shutdown' in s_int:
                            pass
                        else:
                            curr_name = f"Serial{s_int.get('name')}"
                            if 'description' not in s_int or s_int['description'] == '':
                                errors.append(f'{rtr}/{curr_name}')
            
            # Returnera lista med korrekta descriptions, och en lista med fel 
            # Dessa outputas sedan i main()
            return int_list, errors

# Tar en int_lst, rtr variabel.
# int_lst är en json dict med alla interfaces.
# rtr är en sträng, OVERBY/TORP/TRESTAD
# Denna används för att kolla mängden subnets och om dem stämmer överens.
# Funkar genom att skapa en dict för varje router. "subnets" variabeln
# Skapar sedan listor med de anslutna subnets för varje router.
# Räknar samtidigt totala mängden subnets med tot_subnets

def check_subnets(int_lst, rtr):
    err = False
    tot_subnets = 0
    misc_errs = []
    subnets = {rtr: []}
    for i in int_lst:
        if i['enabled'] == True:
            if 'ietf-ip:ipv4' in i:
                addr_lst = i['ietf-ip:ipv4']
                try:
                    ips = addr_lst['address']
                    prepp_ip4 = str(ips[0])
                    raw = prepp_ip4.replace('\'', '\"')
                    ip4s = json.loads(raw) 
                    ip = ip4s['ip']
                    if ip4s['netmask'] == '255.255.255.252':
                        ipmask = ip + '/30'
                        subnets[rtr].append(ipmask)
                    elif ip4s['netmask'] == '255.255.255.192':
                        ipmask = ip + '/26'
                        subnets[rtr].append(ipmask)
                    elif ip4s['netmask'] == '255.255.255.0':
                        ipmask = ip + '/24'
                        subnets[rtr].append(ipmask)
                except KeyError as exc:
                    if_name = i['name']
                    misc_str = f'IF_ERR: Enabled without addressing: {rtr}.{if_name}'
                    misc_errs.append(misc_str)

    # nedan används för seriella länkar, native anropet i calls/
    # I test-syfte, kommer den skippas om det inte finns seriella länkar 
    if rtr in ['TRESTAD', 'TORP']:
        ip_addr = routers[rtr]
        serial_output = get_serial_ints(ip_addr)
        if serial_output:
            serial_data = json.loads(serial_output)
            for s_int in serial_data.get('Cisco-IOS-XE-native:Serial', []):
                try:
                    if len(s_int.items()) == 1:
                        nem = s_int['name']
                        err_str = f'IF_ERR: Enabled without addressing: {rtr}.S{nem}'
                        misc_errs.append(err_str)

                    ip_info = s_int['ip']['address']['primary']
                    ip = ip_info['address']
                    mask = ip_info['mask']

                    if mask == '255.255.255.252':
                        subnets[rtr].append(ip + '/30')
                    elif mask == '255.255.255.192':
                        subnets[rtr].append(ip + '/26')
                    elif mask == '255.255.255.0':
                        subnets[rtr].append(ip + '/24')
                except KeyError:
                    pass

    return subnets, misc_errs

def check_routes(rtr):
    rt_errs = []
    tr_ospf_count = 0 
    ov_ospf_count = 0
    to_static_count = 0
    rt_dict = {rtr: []}
    ip = routers[rtr]
    output = route_table(ip)
    json_out = json.loads(str(output))
    if rtr == 'TORP':
        for item in json_out['ietf-routing:route']:
            prot = item['source-protocol']
            allow_stat = 'ietf-routing:static'
            allow_dir = 'ietf-routing:direct'
            if allow_stat not in prot and allow_dir not in prot:
                error = 'ROUTE_ERR: ROUTING PROTOCOL FOUND ON TORP'
                print(prot)
                rt_errs.append(error)
            if item['source-protocol'] == 'ietf-routing:static':
                dest = item['destination-prefix']
                to_static_count += 1
        if to_static_count < 2:
            rt_errs.append('ROUTE_ERR: LACKING STATIC ROUTES ON TORP')
        if to_static_count == 2 and len(rt_errs) == 0:
            return rt_errs
    elif rtr == 'TRESTAD':
        for item in json_out['ietf-routing:route']:
            if item['source-protocol'] == 'ietf-ospf:ospfv2':
                if '/26' in item['destination-prefix']:
                    tr_ospf_count += 1
                    if tr_ospf_count > 1:
                        err_str = 'OSPF_ERR: MORE THAN ONE OSPF ROUTE IN TRESTAD'
                        rt_errs.append(err_str)
        if tr_ospf_count < 1:
            err_str = 'OSPF_ERR: MISSING 1 OSPF ROUTE ON TRESTAD'
            rt_errs.append(err_str)
        if tr_ospf_count > 1:
            surplus = tr_ospf_count - 1
            err_str = 'OSPF_ERR: {surplus} OSPF ROUTES ON TRESTAD'
            rt_errs.append(err_str)
        if tr_ospf_count == 1 and len(rt_errs) == 0:
            return rt_errs
    elif rtr == 'OVERBY':
        for item in json_out['ietf-routing:route']:
            if item['destination-prefix'] == '0.0.0.0/0': 
                if item['source-protocol'] != 'ietf-ospf:ospfv2':
                    rt_errs.append('OSPF_ERR: DEFAULT ROUTE NOT SHARED THROUGH OSPF')
            if item['source-protocol'] == 'ietf-ospf:ospfv2':
                ov_ospf_count += 1
        if ov_ospf_count < 2:
            rt_errs.append('OSPF_ERR: MISSING OSPF ROUTES ON OVERBY')
        if ov_ospf_count > 2:
            rt_errs.append('OSPF_ERR: TOO MANY OSPF ROUTES ON OVERBY')
    else:
        print('invalid router name. Try: OVERBY|TRESTAD|TORP')
    return rt_errs

def check_addressing(raw_data):
    topology = {}
    all_interfaces = []
    subnet_errs = []
    
    for router, ip_list in raw_data.items():
        topology[router] = []
        for ip_str in ip_list:
            iface = ipaddress.IPv4Interface(ip_str)
            if iface.network != mgmt_net:
                topology[router].append(iface)
                all_interfaces.append(iface)
    all_ips = [iface.ip for iface in all_interfaces]

    print('\n============= CHECKING SUBNET CONFIGURATION =============')
    if len(all_ips) == len(set(all_ips)):
        print("PASS: NO DUPLICATE ADDRESSING")
    else:
        subnet_errs.append('ERROR: DUPLICATE ADDRESSING FOUND')
    unika_nets = list(set([iface.network for iface in all_interfaces]))
    prefix_counts = {24: 0, 26: 0, 30: 0}
    for net in unika_nets:
        prefix_counts[net.prefixlen] = prefix_counts.get(net.prefixlen, 0) + 1
    if prefix_counts[24] == 1 and prefix_counts[26] == 1 and prefix_counts[30] == 2:
        print("CORRECT SUBNETTING: 2 OF /30, 1 OF /26, 1 OF /24 ")
    else:
        subnet_errs.append(f'ERR: Incorrect subnetting: {prefix_counts[24]} of /24, {prefix_counts[26]} of /26, {prefix_counts[30]} of /30')
    return subnet_errs

def check_ospf_auth():
    # Kollar enbart OSPF connected routers, sparar allt i json
    overby = routers['OVERBY']
    trestad = routers['TRESTAD']
    overby_ospf = get_ospf(overby)
    overby_json = json.loads(overby_ospf)
    trestad_ospf = get_ospf(trestad)
    trestad_json = json.loads(trestad_ospf)
    err_lst = []
    corr_lst = []
    tr_inst_lst = trestad_json['Cisco-IOS-XE-ospf-oper:ospf-instance'] 
    ov_inst_lst = overby_json['Cisco-IOS-XE-ospf-oper:ospf-instance']
    if len(ov_inst_lst) + len(tr_inst_lst) == 2:
        ov_inst = ov_inst_lst[0]
        tr_inst = tr_inst_lst[0]
        ov_area = ov_inst['ospf-area']
        tr_area = tr_inst['ospf-area']
        ov_area_len = len(ov_area)
        tr_area_len = len(tr_area)
        if len(tr_area) + len(ov_area) == 2:
            ov_prim = ov_area[0]
            tr_prim = tr_area[0]
            for ov_intr in ov_prim['ospf-interface']:
                intr_auth = ov_intr['authentication']
                intr_name = ov_intr['name']
                try:
                    if intr_auth['key-string'] == '':
                        err_str = f'MISSING: OVERBY/{intr_name}'
                        err_lst.append(err_str)
                    else:
                        corr_str = f'CORRECT: OVERBY/{intr_name}'
                        corr_lst.append(corr_str)
                except KeyError as exc:
                    err_str = f'NO OSPF AUTH: OVERBY/{intr_name}'
                    err_lst.append(err_str)

            for tr_intr in tr_prim['ospf-interface']:
                intr_auth = tr_intr['authentication']
                intr_name = tr_intr['name']
                try:
                    if intr_auth['key-string'] == '':
                        err_str = f'MISSING: TRESTAD/{intr_name}'
                        err_lst.append(err_str)
                    
                    else:
                        corr_str = f'CORRECT: TRESTAD/{intr_name}'
                        corr_lst.append(corr_str)
                except KeyError as exc:
                    err_str = f'NO OSPF AUTH: TRESTAD/{intr_name}'
                    err_lst.append(err_str)
            return corr_lst, err_lst
        else:
            e_str = f'OSPF_ERR: SURPLUS OSPF AREAS!  OVERBY = {ov_area_len} TRESTAD = {tr_area_len}'
            err_lst.append(e_str)
    else:
        er_str = f'OSPF_ERR: SURPLUS OSPF INSTANCES! OVERBY = {len(ov_inst_lst)} TRESTAD = {len(tr_inst_lst)}' 
        err_lst.append(er_str)
    return corr_lst, err_lst
def check_acl():
    torp = routers["TORP"]
    acl_out = get_acl(torp)
    acl_json = json.loads(acl_out)
    try:
        acl_set = acl_json["openconfig-acl:acl-sets"]
        acl_lst = acl_set["acl-set"]
        for i in acl_lst:
            if "TELNET" in i["name"] or "telnet" in i["name"]:
                aces = i['acl-entries']
                for ace in aces['acl-entry']:
                    ipv4 = ace['ipv4']
                    ipconf = ipv4['config']
                    subnet = ipconf['source-address']
                    match_net = '192.168.11.'
                    match_mask = '/32'
                    if match_net and match_mask in subnet:
                        print(f'PASS: ACL correctly block HostBK at {subnet}')
                    elif match_net not in subnet:
                        print(f'ACL blocking HostBK is full subnet, {subnet}')
                    else:
                        print(f'Incorrectly configured ACL.')
    except KeyError as exc:
        pass
    
def main():
    print (f'======== CHECKING ACL COMPLIANCE ===========')
    check_acl()
    tr_routes = check_routes('TRESTAD')
    ov_routes = check_routes('OVERBY')
    to_routes = check_routes('TORP')

    print(f'=========CHECKING ROUTING===========')
    print(f'========= OVERBY =========\nERRORS:')
    if len(ov_routes) > 0:
        for err in ov_routes:
            print(err)
    elif len(ov_routes) == 0:
        print(f'CORRECT: No routing errors found on OVERBY')
    print(f'========= TRESTAD =========\nERRORS:')
    if len(tr_routes) > 0:
        for err in tr_routes:
            print(err)
    elif len(tr_routes) == 0:
        print(f'CORRECT: No routing errors found on TRESTAD')
    print(f'========= TORP =============\nERRORS:')
    if len(to_routes) > 0:
        for err in to_routes:
            print(err)
    elif len(to_routes) == 0:
        print(f'CORRECT: No routing errors found on TORP')
    
    desc_int_err = []
    subnets = {}
    for rtr in routers:
        int_lst, errors = check_desc(rtr)
        desc_int_err.extend(errors)
        subnets[rtr] = int_lst
        
    to_sub, to_misc = check_subnets(subnets['TORP'], 'TORP')
    ov_sub, ov_misc = check_subnets(subnets['OVERBY'], 'OVERBY')
    tr_sub, tr_misc = check_subnets(subnets['TRESTAD'], 'TRESTAD')
    raw_data = ov_sub.copy()
    raw_data.update(tr_sub)
    raw_data.update(to_sub)
    if len(tr_misc) > 0:
        for err_str in tr_misc:
            print(err_str)
    if len(ov_misc) > 0:
        for err_str in ov_misc:
            print(err_str)
    if len(to_misc) > 0:
        for err_str in to_misc:
            print(err_str)

    if len(desc_int_err) == 0:
        print(f'\nAll active interfaces have descriptions')
    else:
        print(f'\n============= MISSING {len(desc_int_err)} INTERFACE DESCRIPTIONS =============')
        for desc_item in desc_int_err:
            print(f'{desc_item}')
        if len(desc_int_err) < 6:
            print(f'Remainding interfaces have descriptions configured')
    subnet_errs = check_addressing(raw_data)
    if len(subnet_errs) == 0:
        print('\nNO ERRORS FOUND IN SUBNETTING')
    else:
        for item in subnet_errs:
            print(item)
    
    print('\n=========CHECKING OSPF AUTH FOR TORP/OVERBY INTERFACES=============')
    corr, err = check_ospf_auth()
    if len(corr) > 0:
        print(f'Correctly configured OSPF authentication interfaces:')
        for inf in corr:
            print(inf)
    if len(err) > 0:
        err_set = set(err)
        print(f'Missing OSPF authentication:')
        for inf in err_set:
            print(inf)
    
main()
