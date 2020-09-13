import sys
import json
import requests

from bs4 import BeautifulSoup

class TransmissionDelegate:
    def __init__(self, trans_id, trans_pw, trans_host, trans_port,
            history_delegate=None):
        self.__id = trans_id
        self.__pw = trans_pw
        self.__ip = trans_host
        self.__port = trans_port
        self.__history_delegate = history_delegate
        self.__url = "http://%s:%s@%s:%s/transmission/rpc" % (self.__id, self.__pw,
                self.__ip,self.__port)
        _ = self.__rpc_get_session()

        if _ is None:
            print("Failed to connect transmission - %s:%s" % (self.__ip, self.__port))
            sys.exit()
        else:
            self.__session = _

    def __rpc_get_session(self):
        res = requests.get(self.__url)
        bs = BeautifulSoup(res.text, "html.parser")
        code_text = bs.find('code').text
        array = code_text.split()

        if len(array) == 2 and array[0] == "X-Transmission-Session-Id:":
            session_id ={ array[0].replace(":", "") : array[1]}
            return session_id

        return None

    def __rpc_post(self, payload):
        headers = {'content-type': 'application/json'}
        headers.update(self.__session)

        response = requests.post(
            self.__url, data=json.dumps(payload), headers=headers).json()

        assert response["result"] == "success"
        return response

    def add_magnet_transmission_remote(self, magnet_info):
        if self.__history_delegate is not None:
            if self.__history_delegate.check_magnet_history(magnet_info.magnet):
                return False

        payload = {
                "arguments":{
                    "filename": magnet_info.magnet
                    },
                "method": "torrent-add"
                }

        res = self.__rpc_post(payload)
        if res['result'] == 'success':
            print("Success to add magnet for [%s]." % magnet_info.title)
        else:
            return False

        if self.__history_delegate is not None:
            self.__history_delegate.add_magnet_info_to_history(magnet_info.get_list())
            return True

        return False

    def list_download_done(self):
        payload = {
            "arguments":{
                "fields": ["id", "name", "isFinished", "percentDone"]
                },
            "method": "torrent-get"
        }
        res = self.__rpc_post(payload)

        for torrent in res["arguments"]["torrents"]:
            if torrent["isFinished"] or torrent["percentDone"] == 1:
                print(torrent["name"])
        return

    def remove_transmission_remote(self, contain_name):
        "TODO: 상태가 Finished 이고  contain_name 인 토렌트 id를 구해서 삭제"

        """
        payload = {
            "arguments":{
                "fields": ["id", "name", "isFinished"]
                },
            "method": "torrent-get"
        }

        res = self.__rpc_post(payload)
        print(res)

        for torrent in res["arguments"]["torrents"]:
            if contain_name in torrent["name"] and torrent["isFinished"]:
                payload = {
                    "method": "torrent-remove",
                    "arguments":{"ids":[torrent["id"]]}
                    }
                res = self.__rpc_post(payload)
        return
        """
