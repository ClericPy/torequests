# python2/3
#! coding: utf-8

import json
import time
from base64 import b64decode

import requests
import websocket
from requests.exceptions import ConnectionError


__all__ = ["Chrome", "Tab"]


class Tab(object):
    def __init__(self, tid, title, url, websocketURL):
        self.id = tid
        self._title = title
        self._url = url
        self._websocketURL = websocketURL
        self._message_id = 0
        self._ws = None

    def _send(self, request):
        self._message_id += 1
        request["id"] = self._message_id
        self.ws.send(json.dumps(request))
        res = self.recv()
        self.close_socket()
        return res

    def recv(self):
        try:
            data = self.ws.recv()
            return data
        except websocket._exceptions.WebSocketTimeoutException as e:
            return

    @property
    def ws(self):
        return self._ws if self._ws and self._ws.connected else self.connect()

    def connect(self, timeout=1):
        try:
            self._ws = websocket.create_connection(self.websocketURL, timeout=timeout)
            # break
        except websocket._exceptions.WebSocketBadStatusException:
            self._ws.close()
            try:
                self._ws.connect(self.websocketURL, timeout=timeout)
            except:
                pass
        except Exception as e:
            print(e, self.id)
        return self._ws

    def refresh_ws(self):
        self.ws.close()
        self._ws = self.connect()

    def wait_loading(self, url=None, timeout=None):
        # block
        self._send({"method": "Page.enable"})
        if url:
            self.set_url(url)
        return self.wait_event("Page.loadEventFired", timeout=timeout)

    def wait_event(self, event, timeout=None):
        # block
        timeout = timeout or float("inf")
        start_time = time.time()
        for _ in range(10):
            try:
                if time.time() - start_time >= timeout:
                    break
                data = self.recv()
                if not data:
                    continue
                data = json.loads(data)
                if data.get("method") == event:
                    break
            except websocket._exceptions.WebSocketTimeoutException:
                continue
            except websocket._exceptions.WebSocketConnectionClosedException:
                self.connect()
            except Exception as e:
                print("wait event %s failed for %s" % (event, e))
        self.close_socket()
        return data

    @property
    def title(self):
        return self._title

    @property
    def url(self):
        return self._url

    @property
    def websocketURL(self):
        return self._websocketURL

    @property
    def html(self):
        result = json.loads(self.evaluate("document.documentElement.outerHTML"))
        value = result["result"]["result"]["value"]
        return value.encode("utf-8")

    def reload(self):
        """
        Reload the page
        """
        return self._send({"method": "Page.reload"})

    def set_url(self, url):
        """
        Navigate the tab to the URL
        """
        self._url = url
        return self._send({"method": "Page.navigate", "params": {"url": url}})

    def set_zoom(self, scale):
        """
        Set the page zoom
        """
        return self.evaluate("document.body.style.zoom={}".format(scale))

    def evaluate(self, javascript):
        """
        Evaluate JavaScript on the page
        """
        return self._send(
            {"method": "Runtime.evaluate", "params": {"expression": javascript}}
        )

    def screenshot(self, format="png", quality=85, fromSurface=False):
        """
        Take a screenshot of the page
        """
        args = {
            "method": "Page.captureScreenshot",
            "params": {
                "format": format,
                "quality": quality,
                "fromSurface": fromSurface,
            },
        }
        result = self._send(args)
        data = json.loads(result)
        if data.has_key("error"):
            raise ValueError(data["error"]["data"])
        return b64decode(data.get("result", {}).get("data", ""))

    def __str__(self):
        return "%s" % (self.url)

    def __repr__(self):
        return 'Tab("%s", "%s", "%s", "%s")' % (
            self.id,
            self.title,
            self.url,
            self.websocketURL,
        )

    def close_socket(self):
        try:
            self._ws.close()
        except:
            pass

    def __del__(self):
        self.close_socket()


class Chrome(object):
    def __init__(self, host="localhost", port=9112):
        self._host = host
        self._port = port
        self._url = "http://%s:%d" % (self.host, self.port)
        self._errmsg = (
            "Connect error! Is Chrome running with -remote-debugging-port=%d"
            % self.port
        )
        self._connect()

    def _connect(self):
        """
        Test connection to browser
        """
        try:
            requests.get(self.url)
        except ConnectionError:
            raise ConnectionError(self._errmsg)

    def _get_tabs(self):
        """
        Get all open browser tabs that are pages tabs
        """
        res = requests.get(self.url + "/json")
        for tab in res.json():
            if tab["type"] == "page":
                yield Tab(
                    tab["id"], tab["title"], tab["url"], tab["webSocketDebuggerUrl"]
                )

    @property
    def host(self):
        return self._host

    @property
    def port(self):
        return self._port

    @property
    def url(self):
        return self._url

    @property
    def tabs(self):
        return tuple(self._get_tabs())

    def __len__(self):
        return len(self.tabs)

    def __str__(self):
        return "[Chrome(tabs=%d)]" % len(self)

    def __repr__(self):
        return 'Chrome(host="%s", port=%s)' % (self.host, self.port)

    def __getitem__(self, i):
        return self.tabs[i]

    def __iter__(self):
        return iter(self.tabs)

