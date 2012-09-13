import urllib2
import json

class JSONClient(object):
    
    def __init__(self, autoflush=False):
        self.data = ""
        self.autoflush = autoflush
        
    def flush(self):
        if len(self.data) > 0:
            self._send(self.data)
            self.data = ""
        
    def _send(self, data):
        print 'passing'
        pass
        
    def add_node(self, id, flush=True, **attributes):
        self.data += json.dumps({"an":{id:attributes}}) + '\r\n'
        if(self.autoflush): self.flush()
        
    def change_node(self, id, flush=True, **attributes):
        self.data += json.dumps({"cn":{id:attributes}}) + '\r\n'
        if(self.autoflush): self.flush()
    
    def delete_node(self, id):
        self._send(json.dumps({"dn":{id:{}}}))
    
    def add_edge(self, id, source, target, directed=True, **attributes):
        attributes['source'] = source
        attributes['target'] = target
        attributes['directed'] = directed
        self.data += json.dumps({"ae":{id:attributes}}) + '\r\n'
        if(self.autoflush): self.flush()
    
    def delete_edge(self, id):
        self._send(json.dumps({"de":{id:{}}}))
        
    def clean(self):
        self._send(json.dumps({"dn":{"filter":"ALL"}}))


class GephiClient(JSONClient):
    
    def __init__(self, url='http://127.0.0.1:8080/workspace0', autoflush=False):
        JSONClient.__init__(self, autoflush)
        self.url = url
        
    def _send(self, data):
        conn = urllib2.urlopen(self.url+ '?operation=updateGraph', data)
        return conn.read()
    
class GephiFileHandler(JSONClient):
    
    def __init__(self, out):
        JSONClient.__init__(self, autoflush=True)
        self.out = out
        
    def _send(self, data):
        self.out.write(data)
