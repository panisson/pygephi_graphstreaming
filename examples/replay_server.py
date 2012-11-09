#!/usr/bin/python
# coding: utf-8
#
# Copyright (C) 2012 André Panisson
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

'''
This script starts an HTTP server in order to replay a stream of json data
collected from the Twitter Streaming API.
It shows the Twitter data in Graph Streaming format,
with the users as nodes and retweets as edges.

You have to install the tweepy client (http://joshthecoder.github.com/tweepy/)
in order to run this script.

To connect to the server with Gephi, you must install Gephi with 
the Graph Streaming plugin.

1. Start Gephi
3. Go to the tab Streaming,right-click on Client and click on "Connect to Stream"
2. Start this script in order to start the server
4. Go to Gephi and enter the Source URL http://localhost:8181/?q=twitter (or other keywords 
    used during the data collection) and click OK

The nodes and edges start to appear in the graph visualization. You can run
the Force Atlas layout in order to get a better layout.

Usage: server.py [options]

Options:
  -h, --help            show this help message and exit
  -l LOG, --log=LOG     Log file of collected streaming data
  -t tw, --timewarp=tw  Time warping factor, used to accelerate or slow down the replay
  -d s, --delay=s       Starting delay in seconds

@author: Andre Panisson
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

active_queues = []

class StreamingListener(tweepy.StreamListener):
    
    def __init__(self, timewarp, *args, **kwargs):
        tweepy.StreamListener.__init__(self, *args, **kwargs)
        self.known_users = {}
        self.before = None
        self.timewarp = timewarp
    
    def on_status(self, status):
        print status.text
        
        date = status.created_at
        if not self.before:
            self.before = date
            
        if date > self.before:
            diff = date - self.before
            
            sleeptime = diff.seconds + diff.microseconds*10e-6
            if sleeptime > 0:
                time.sleep(sleeptime*self.timewarp)
            self.before = date
        
        m = re.search('(?<=RT\s@)\w+', status.text)
        if m:
            source_user = m.group(0).lower()
            target_user = status.user.screen_name
            id = status.id
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
        
class Player(threading.Thread):
    def __init__(self, options, server):
        self.options = options
        self.server = server
        threading.Thread.__init__(self)
        
    def run(self):
        print "Waiting %s seconds before start streaming" % self.options.delay
        time.sleep(self.options.delay)
        
        print "Streaming retweets for file '%s'"%self.options.log
        listener = StreamingListener(self.options.timewarp)
        f = open(self.options.log)
        
        line = f.readline()
        while line != '':
            listener.on_data(line)
            line = f.readline()
            
        print "Stream finished"
        dispatch_event((None, None, None, None, None))
        self.server.shutdown()
        
class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""
    
    def start(self):
        self.serve_forever()
        
    def stop(self):
        self.socket.close()
        
def parseOptions():
    parser = optparse.OptionParser()
    parser.add_option("-l", "--log", type="string", dest="log", help="Log file of collected streaming data", default='undefined')
    parser.add_option("-t", "--timewarp", type="float", dest="timewarp", help="Time warping factor, used to accelerate or slow down the replay", default='1.0')
    parser.add_option("-d", "--delay", type="int", dest="delay", help="Starting delay in seconds", default='0')
    parser.add_option("-s", "--serverport", type="int", dest="serverport", help="HTTP server port", default=8181)
    (options, _) = parser.parse_args()
    if options.log == 'undefined':
        parser.error("Log file is mandatory")
    return options
        
def main():
    options = parseOptions()

    try:
        server = ThreadedHTTPServer(('', options.serverport), RequestHandler)
        
        player = Player(options, server)
        player.setDaemon(True)
        player.start()
        
        print 'Test server running...'
        server.start()
    except KeyboardInterrupt:
        print 'Stopping server...'
        server.stop()
        dispatch_event((None, None, None, None, None))
        sys.exit(0)

if __name__ == '__main__':
    main()