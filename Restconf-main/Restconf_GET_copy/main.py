from config import routers
from checks import (
    check_routes,
    check_desc,
    check_subnets,
    check_addressing,
    check_ospf_auth
)


def main():

    print(f"\n========== Checking ROUTES ==========\n")
    tr_routes = check_routes('TRESTAD')
    ov_routes = check_routes('OVERBY')
    to_routes = check_routes('TORP')

    print(f'CHECKING OVERBY ROUTES\nERRORS: {ov_routes}')
    print(f'CHECKING TRESTAD ROUTES\nERRORS: {tr_routes}')
    print(f'CHECKING TORP ROUTES\nERRORS: {to_routes}')

    if len(tr_routes) == 0 and len(ov_routes) == 0 and len(to_routes) == 0:
        print(f'\nNO ROUTING ERRORS FOUND ON OVERBY, TRESTAD OR TORP')
        print("ROUTES = OK")
    else:
        print('ROUTING ERRORS FOUND:')
        for item in tr_routes + ov_routes + to_routes:
            print(item)


    print(f"\n========== Checking INTERFACE ==========\n")
    desc_int_err = []
    interfaces = {}

    for rtr in routers:
        int_lst, errors = check_desc(rtr)
        desc_int_err.extend(errors)
        interfaces[rtr] = int_lst


    print(f"\n========== Checking SUBNETS ==========\n")
    ov_sub = check_subnets(interfaces['OVERBY'], 'OVERBY')
    tr_sub = check_subnets(interfaces['TRESTAD'], 'TRESTAD')
    to_sub = check_subnets(interfaces['TORP'], 'TORP')

    raw_data = ov_sub.copy()
    raw_data.update(tr_sub)
    raw_data.update(to_sub)


    print(f"\n========== Checking DESCRIPTION ==========\n")
    if len(desc_int_err) == 0:
        print('All active interfaces have descriptions')
        print("DESCRIPTION = OK")
    else:
        print('\nERRORS ON DESCRIPTION FOR INTERFACES:')
        for error in desc_int_err:
            print(error)


    print(f"\n========== Checking ADDRESSING ==========\n")
    subnet_errs = check_addressing(raw_data)

    if len(subnet_errs) == 0:
        print('\nNO ERRORS FOUND IN SUBNETTING')
        print("ADDRESSING = OK")
    else:
        for error in subnet_errs:
            print(error)


    print(f"\n========== Checking OSPF AUTHENTICATION ==========\n")
    print('CHECKING INTERFACE OSPF AUTHENTICATION ON TRESTAD/OVERBY')

    corr, err = check_ospf_auth()

    if len(err) > 0:
        print(f'MISSING OSPF AUTH SETTINGS FOUND:\n{err}')

    if len(corr) > 0:
        print(f'CORRECTLY CONFIGURED OSPF AUTH SETTINGS FOUND:\n{corr}')
        print("OSPF AUTHENTICATION = OK")


main()
