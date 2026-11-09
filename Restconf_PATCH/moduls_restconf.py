import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

usernamePassword = "Basic YWRtaW46TmV0d29yayEzMzc="
 

# ===== Patch ===== #
def patch(host, YANG, data):
    try:
        response = requests.patch(
            url = f"https://{host}/restconf/data/{YANG}",
            headers = {
                "Accept": "application/yang-data+json",
                "Content-Type": "application/yang-data+json",
                "Authorization": usernamePassword
            },
            json = data,
            verify = False,
        )
        
        print(f"\n===========", host, "=============")
        print("YANG = ", YANG)
        print("response.status_code = ", response.status_code)
        print("response.text = ", response.text)

        return response

    except requests.exceptions.RequestException as error:
        print(f"\n=====!!!!!======", host, "=======!!!!!======")
        print("RESTCONF ERROR:", error)

        return None

# ===== Save ===== #
def save(host):
    response = requests.post(
        url = f"https://{host}/restconf/operations/cisco-ia:save-config",
        headers = {
            "Accept": "application/yang-data+json",
            "Authorization": usernamePassword
        },
        verify = False,
        timeout = 20,
    )

    print(f"\n=========== {host} save =============")
    print("SAVE running --> startup")
    print("response.status_code =", response.status_code)
    print("response.text =", response.text)

    return response

# ====No Shutdown ====#
def no_shutdown(host, YANG):
    response = requests.delete(
        url=f"https://{host}/restconf/data/{YANG}/shutdown",
        headers={
            "Accept": "application/yang-data+json",
            "Authorization": usernamePassword
        },
        verify=False,
        timeout=20,
    )

    print(f"\n=========== {host} no shutdown =============")
    print("YANG =", YANG)
    print("response.status_code =", response.status_code)
    print("response.text =", response.text)

    if response.status_code != 404:
        response.raise_for_status()

    return response