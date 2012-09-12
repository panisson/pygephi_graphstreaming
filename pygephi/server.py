'''
This script starts an HTTP server that connects to the Twitter Streaming API and 
shows the Twitter data in Graph Streaming format,
with the users as nodes and retweets as edges.

You have to install the tweepy client (http://joshthecoder.github.com/tweepy/)
in order to run this script.

To connect to the server with Gephi, you must install Gephi with 
the Graph Streaming plugin.
1. Start Gephi
2. Go to the tab Streaming,right-click on Client and click on "Connect to Stream"
3. Enter the Source URL http://localhost:8181/?q=twitter (or other keywords if the 
    server is filtering other keywords) and click OK

The nodes and edges start to appear in the graph visualization. You can run
the Force Atlas layout in order to get a better layout.

Usage: server.py [options]

Options:
  -h, --help            show this help message and exit
  -u USER, --user=USER  Twitter username to connect
  -p PASSWORD, --password=PASSWORD
                        Twitter password to connect
  -q QUERY, --query=QUERY
                        Comma-separated list of keywords
  -l LOG, --log=LOG     Output log of streaming data


Created on Nov 10, 2010

@author: panisson
'''
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import urlparse
import tweepy
import re
try:
    import simplejson
except ImportError:
    try:
        import json as simplejson
    except:
        raise "Requires either simplejson or Python 2.6!"
import threading
import Queue
import socket
from SocketServer import ThreadingMixIn
import optparse
import sys
import time

api = tweepy.API()
active_queues = []

class StreamingListener(tweepy.StreamListener):
    
    def __init__(self, *args, **kwargs):
        tweepy.StreamListener.__init__(self, *args, **kwargs)
        self.known_users = {}
        self.stream_log = None
    
    def on_data(self, data):
        self.stream_log.write(data)
        self.stream_log.flush()
        super(StreamingListener, self).on_data(data)
    
    def on_status(self, status):
        print status.text
        
        m = re.search('(?<=RT\s@)\w+', status.text)
        if m:
            source_user = m.group(0).lower()
            target_user = status.user.screen_name
            id = status.id
            date = status.created_at
            text = status.text
            
            dispatch_event((id, source_user, target_user, text, date))
            
def dispatch_event(e):
    for q in active_queues:
        q.put(e)

class RequestHandler(BaseHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        BaseHTTPRequestHandler.__init__(self, *args, **kwargs)
        
    def do_POST(self):
        pass

    def do_GET(self):
        
        param_str = urlparse.urlparse(self.path).query
        parameters = urlparse.parse_qs(param_str, keep_blank_values=False)
        if "q" not in parameters:
            return
        
        q = parameters["q"][0]
        terms = q.split(",")
        
        print "Request for retweets, query '%s'"%q
        
        self.queue = Queue.Queue()
        self.known_users = {}
        active_queues.append(self.queue)
        
        self.wfile.write('\r\n')
        
        while True:
                        
            (id, source, target, text, date) = self.queue.get()
            if id == None:
                break
            
            found = False
            for term in terms:
                if re.search(term, text.lower()):
                    found = True
            if not found:
                continue
            
            try:
                
                if source not in self.known_users:
                    self.known_users[source] = source
                    event = simplejson.dumps({'an':{source:{'label':source, 'size':5, 'r':84./255., 'g':148./255., 'b':183./255.}}})
                    self.wfile.write(event)
                    self.wfile.write('\r\n\r\n')
                    
                if target not in self.known_users:
                    self.known_users[target] = target
                    event = simplejson.dumps({'an':{target:{'label':target, 'size':5, 'r':84./255., 'g':148./255., 'b':183./255.}}})
                    self.wfile.write(event)
                    self.wfile.write('\r\n')
                
                event = simplejson.dumps({'ae':{id:{'source':source, 'target':target, 'directed':True, 'weight':2.0, 'date':str(date)}}})
                self.wfile.write(event)
                self.wfile.write('\r\n')
                
            except socket.error:
                print "Connection closed"
                active_queues.remove(self.queue)
                return
        
class Collector(threading.Thread):
    def __init__(self, options):
        self.options = options
        threading.Thread.__init__(self)
        
    def run(self):
        q = self.options.query.split(",")
#        q = [e+ ' rt' for e in q]
        
        print "Streaming retweets for query '%s'"%q
        listener = StreamingListener()
        listener.stream_log = file(self.options.log, 'a')
        auth = tweepy.BasicAuthHandler(self.options.user, self.options.password)
        stream = tweepy.streaming.Stream(auth, listener, timeout=60.0)
        while (True):
            try:
                stream.filter(track=q)
            except socket.gaierror:
                print "Stream closed"
                time.sleep(60)
            except Exception, e:
                print str(e)
                time.sleep(60)
        
class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""
    
    def start(self):
        self.serve_forever()
        
    def stop(self):
        self.socket.close()
        
def parseOptions():
    parser = optparse.OptionParser()
    parser.add_option("-u", "--user", type="string", dest="user", help="Twitter username to connect", default='undefined')
    parser.add_option("-p", "--password", type="string", dest="password", help="Twitter password to connect", default='undefined')
    parser.add_option("-q", "--query", type="string", dest="query", help="Comma-separated list of keywords", default="twitter")
    parser.add_option("-l", "--log", type="string", dest="log", help="Output log of streaming data", default="/tmp/stream.log")
    parser.add_option("-s", "--serverport", type="int", dest="serverport", help="HTTP server port", default=8181)
    (options, _) = parser.parse_args()
    if options.user == 'undefined':
        parser.error("Twitter username is mandatory")
    if options.password == 'undefined':
        options.password = raw_input("Password for Twitter user '%s': "%options.user)
    return options
        
def main():
    options = parseOptions()
    collector = Collector(options)
    collector.setDaemon(True)
    collector.start()
    try:
        server = ThreadedHTTPServer(('', options.serverport), RequestHandler)
        print 'Test server running...'
        server.start()
    except KeyboardInterrupt:
        print 'Stopping server...'
        server.stop()
        dispatch_event((None, None, None, None, None))
        sys.exit(0)

if __name__ == '__main__':
    main()