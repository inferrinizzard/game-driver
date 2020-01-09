from websocket import create_connection, WebSocketTimeoutException
from json import dumps, loads

class ChromeDevToolsProtocolError(Exception):
    def __init__(self, error):
        self.error = error
    
    def __repr__(self):
        return 'ChromeDevToolsProtocolError: ', dumps(self.error)

class ChromeDevToolsProtocol():
    def __init__(self, url):
        self.ws = create_connection(url, timeout=1)
        self.nonce = 0
        self.sessionId = None
        self.handlers = {}
        self.on('Target.attachedToTarget', self.attachedToTarget)
        self.on('Target.detachedFromTarget', self.detatchedFromTarget)
    
    def attachedToTarget(self, **params):
        self.sessionId = params['sessionId']
    
    def detatchedFromTarget(self, **params):
        self.sessionId = None
        
    def on(self, method, handler):
        self.handlers[method] = handler
        
    def send(self, method, **params):
        
        self.nonce += 1
        
        msg = dict(id=self.nonce, method=method, params=params)
        if self.sessionId is not None:
            msg['sessionId'] = self.sessionId
            
        self.ws.send(dumps(msg))
        
        while True:
            raw = self.ws.recv()
            reply = loads(raw)

            if 'method' in reply:
                self._handleEvent(reply['method'], **reply['params'])
            else:  
                assert reply['id'] == self.nonce
                if 'error' in reply:
                    raise ChromeDevToolsProtocolError(reply['error'])
                else:
                    return reply['result']
    
    
    def pump(self):
        try:
            raw = self.ws.recv()
            reply = loads(raw)
            
            if 'method' in reply:
                self._handleEvent(reply['method'], **reply['params'])
        except WebSocketTimeoutException:
            pass
    
    def _handleEvent(self, method, **params):
        print('event:', method, params)
        if method in self.handlers:
            self.handlers[method](**params)
    
    def close(self):
        self.ws.close()
        print("chrome devtools closed")
        
    def __del__(self):
        self.close()