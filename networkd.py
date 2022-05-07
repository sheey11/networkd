from campus import CampusNetwork
from pick import pick
import os, json, time, logging
from logging import Logger

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
daemon = CampusNetwork()
previous_state = ''

def callback(status: str) -> None:
    global previous_state
    if status != previous_state:
        previous_state = status
        if status == daemon._STATUS_ONLINE:
            logging.info("online now")
        elif status == daemon._STATUS_OFFLINE:
            logging.info("offline now")
        else:
            logging.info("connecting")

def get_config():
    username, password, network_type = '', '', ''
    if os.path.exists('./config.json'):
        with open('./config.json', 'r') as f:
            j_obj = json.loads(f.read())
            return j_obj['username'], j_obj['password'], j_obj['network_type']

    with open('./config.json', 'w') as f:
        username = input("用户名：")
        password = input("密码：")
        network_type, _ = pick(daemon.service_names, "选择网络类型: ")
        f.write(json.dumps( {
            'username': username,
            'password': password,
            'network_type': network_type
        }))
        f.flush()
    return username, password, network_type


if __name__ == '__main__':
    daemon.listen_for_network_change(1, callback)

    while True:
        username, password, ntype = get_config()
        ok, msg = daemon.login(username, password, ntype)
        if not ok:
            logging.error(msg)
        time.sleep(30)
