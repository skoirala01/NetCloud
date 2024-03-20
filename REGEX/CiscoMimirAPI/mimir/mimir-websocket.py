import json
from base64 import b64encode
from ws4py.client.threadedclient import WebSocketClient

# websocket_url = 'ws://{}:{}/ws'.format('mimir-prd-001.cisco.com', str(4000))
websocket_url = 'ws://mimir-socket.cisco.com/ws'
userid = 'foo'
password = 'bar'


class MimirClient(WebSocketClient):
    def opened(self):
        def data_provider():
            yield json.dumps({'scope': 'np', 'request': 'interfaces', 'input': {'cpyKey': 1500}})

        self.send(data_provider())

    def closed(self, code, reason=None):
        print("Closed down. Code: {0} Reason: {1}".format(code, reason))

    def received_message(self, m):
        msg = json.loads(str(m))
        print(msg)
        if msg['meta']['status']['status'] == 1:
            self.close(reason='bye bye')


if __name__ == '__main__':
    try:
        auth = b64encode(userid, password)
        ws = MimirClient(
            websocket_url,
            protocols=['http-only', 'chat'],
            headers=[('Authorization', 'Basic ' + auth)])
        ws.connect()
        ws.run_forever()
    except KeyboardInterrupt:
        ws.close()
