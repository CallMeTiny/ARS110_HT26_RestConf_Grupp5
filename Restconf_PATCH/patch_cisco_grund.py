import moduls_restconf
import time

YANG = "Cisco-IOS-XE-native:native"

routers = {
    "1.1.1.1": "OVERBY",
    "1.1.1.2": "TRESTAD",
    "1.1.1.3": "TORP"
}


def grund_conf(host, hostname):
    data = {
        "Cisco-IOS-XE-native:native": {

            "hostname": hostname,

             "enable": {
                 "secret": {
                     "type": "9",
                     "secret": (
                         "$9$ilHFCvyIm3HnUU$"
                         "/fRmBdbczQunyNFpS3nzNY6iR25ytl0Lj8BPkqrUp.Q"
                     ),
                 }
             },

              "username": [
                  {
                      "name": "admin01",
                      "privilege": 15,
                      "password": {
                          "encryption": "0",
                          "password": "cisco123",
                      },
                  }
              ],

             "line": {
                 "console": [
                     {
                         "first": "0",
                         "password": {
                             "secret": "cisco"
                         },
                     }
                 ],

                 "vty": [
                     {
                         "first": 0,
                         "last": 15,
                         "password": {
                             "secret": "cisco"
                         },
                         "transport": {
                             "input": {
                                 "input": ["telnet"]
                             }
                         },
                     }
                 ],
             },
         }
     }

    response = moduls_restconf.patch(host, YANG, data)

    if response is None:
        return

    response.raise_for_status()


def main():
    for host, hostname in routers.items():
        grund_conf(host, hostname)

if __name__ == "__main__":
    main()
    time.sleep(5)
