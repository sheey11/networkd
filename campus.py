#!/usr/bin/env python3

# author:           sheey
# dependencies:     requests
# date:             2019/10/10

import requests, re, time
from urllib.parse import quote
import logging

from threading import Thread

from typing import Any, Callable, Dict, List, Optional, Tuple, Union, Mapping

class CampusNetwork:
    _sess: requests.Session

    _page_info: Mapping[str, Any]
    _service: Mapping[str, Any]

    service_names: List[str] = []
    current_service: str
    user_name: str
    user_id: str
    logged_in: bool

    _baseUrl: str = ''
    _query_str: str = ''

    _online_status: Mapping[str, Any]

    _GET_USER_INFO_FAIL = 'fail' # 获取用户信息失败，用户可能已经下线
    _GET_USER_INFO_RETRY = 'wait' # 用户信息不完整，请稍后重试
    _GET_USER_INFO_SUCCESS = 'success' # 获取用户信息成功

    _STATUS_ONLINE = 'online'
    _STATUS_OFFLINE = 'offline'
    _STATUS_CONNECTING = 'connecting'

    _inner_status: str = _STATUS_OFFLINE

    _monitor_thread: Thread = Thread()
    _monitor_callbacks: List[Callable[[str], None]] = []
    _monitor_closure_stop: Callable[[], None]

    def __init__(self, base_url: str = ''):
        self._sess = requests.Session()
        self._sess.keep_alive = False
        if base_url != '':
            if base_url.startswith('http://'):
                self._baseUrl = base_url
            else:
                self._baseUrl = 'http://' + base_url
        else:
            self._baseUrl = ''
        self.satisfy_url_and_query_string()
        self.get_service()
        self.fetch_status()

    def compose_url(self, path: str) -> str:
        if not path.startswith('/'):
            path = '/' + path
        if self._baseUrl.endswith('/'):
            return self._baseUrl[:-1] + path
        return self._baseUrl + path

    def fetch_status(self):
        j = { 'result': self._GET_USER_INFO_RETRY }
        while j['result'] == self._GET_USER_INFO_RETRY:
            res = self._sess.post(self.compose_url('/eportal/InterFace.do?method=getOnlineUserInfo'))
            res.encoding = 'utf-8'
            j = res.json()
            time.sleep(0.1)

        self._online_status = j
        self.current_service = j['service']
        self.user_name = j['userName']
        self.user_id = j['userId']
        self.logged_in = j['result'] == self._GET_USER_INFO_SUCCESS

        self._inner_status = self._STATUS_ONLINE if self.logged_in else self._STATUS_OFFLINE

    def get_service(self):
        res = self._sess.post(self.compose_url("/eportal/InterFace.do?method=pageInfo"), data="queryString=", headers={
            "Content-Type": "application/x-www-form-urlencoded"
        })
        res.encoding = 'utf-8'

        self._page_info = res.json()
        self._service = self._page_info['service']
        self.service_names = [service for service in self._service]
        self.service_names.sort()

    def satisfy_url_and_query_string(self) -> None:
        status_code = 0
        while status_code != 200 and status_code != 204:
                res = self._sess.get("http://www.gstatic.com/generate_204", timeout=5)
                logging.debug('gstatic responds with: %d' % res.status_code)
                status_code = res.status_code
        if res.status_code == 204:
            return

        match = re.search('(?<=http://).+?(?=/)', res.text)
        if match is not None:
            self._baseUrl = 'http://' + match.group()

        match = re.search('(?<=index.jsp\\?)(.+?)(?=\')', res.text)
        if match is not None:
            self._query_str = match.group()
        self._query_str = quote(self._query_str, encoding='utf-8')

    def login(self, uname, passwd, service) -> Tuple[bool, str]:
        try:
            self.fetch_status()
            if self.logged_in:
                return True, '已在线上'

            self._inner_status = self._STATUS_CONNECTING
            self._notify_network_change(self._inner_status)
            self.satisfy_url_and_query_string()

            LOGIN_URL = self.compose_url('/eportal/InterFace.do?method=login')
            service = quote(service, encoding='utf-8')
            HEADER = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.190 Safari/537.36",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
            }
            # userId, passwd, service, queryString
            DATA = "userId=%s&password=%s&service=%s&queryString=%s&operatorPwd=&operatorUserId=&validcode=&passwordEncrypt=false"
            DATA = DATA % (uname, passwd, service, self._query_str)

            res = self._sess.post(LOGIN_URL, data=DATA, headers=HEADER)
            res.encoding = 'utf-8'
            ret = res.json()

            self.fetch_status()
            return ret['result'] == 'success', ret['message']
        except Exception as e:
            logging.exception(e)
            return False, "exception encontered"

    def logout(self) -> bool:
        DATA = "userIndex=%s" % self._online_status["userIndex"]
        res = self._sess.post(self.compose_url("eportal/InterFace.do?method=logout"), data=DATA, headers={
            "Content-Type": "application/x-www-form-urlencoded"
        })
        self.fetch_status()

        return res.status_code == 200

    def listen_for_network_change(self, interval: float, callback: Callable[[str], None]) -> None:
        if self._monitor_thread.is_alive():
            self._monitor_closure_stop()

        self._monitor_callbacks.append(callback)
        action, self._monitor_closure_stop = self._get_monitor_actions(interval)

        self._monitor_thread = Thread(None, action)
        self._monitor_thread.setDaemon(True)
        self._monitor_thread.start()

    def get_network_access(self) -> str:
        return self._STATUS_ONLINE if self.logged_in else self._inner_status # and self.current_service != '校园网'

    def _notify_network_change(self, status) -> None:
        for cb in self._monitor_callbacks:
            cb(status)

    def _get_monitor_actions(self, interval: float) -> Tuple[Callable[[], None], Callable[[], None]]:
        stop: bool = False

        def action():
            nonlocal stop
            first_run = True
            previous = self.get_network_access()
            while not stop:
                self.fetch_status()
                current = self.get_network_access()
                if current != previous or first_run:
                    self._notify_network_change(current)
                    first_run = False
                previous = current
                time.sleep(interval)

        def stop_monitor():
            nonlocal stop
            stop = True

        return action, stop_monitor
