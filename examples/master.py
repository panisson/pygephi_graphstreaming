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
This script starts an HTTP server that generates random graph data in Graph Streaming format.

To connect to the server with Gephi, you must install Gephi with 
the Graph Streaming plugin.
1. Start Gephi
2. Go to the tab Streaming,right-click on Client and click on "Connect to Stream"
3. Enter the Source URL http://localhost:8181 and click OK

The nodes and edges start to appear in the graph visualization. You can run
the Force Atlas layout in order to get a better layout.

Usage: server.py -n 50 -p 8181

Options:
  -n NR_NODES, --nr_nodes        maximum number of nodes
  -p PORT, --serverport=PORT     HTTP server port to listen

Created on March 4, 2014

@author: panisson
'''
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SocketServer import ThreadingMixIn
from pygephi import GephiFileHandler
import threading
import Queue
import socket
import optparse
import sys
import time
import random

active_queues = []
graph = {}
            
def dispatch_event(e):
    # print e
    for q in active_queues:
        q.put(e)
        
class RequestProcessor():
    
    def __init__(self, out):
        self.known_nodes = {}
        self.handler = GephiFileHandler(out)
    
    def process(self, event):
    
        etype = event['type']
        source = event['source']
        target = event['target']
            
        default_node_attr = {'size':5, 'r':84./255., 'g':148./255., 'b':183./255.}
            
        if source not in self.known_nodes:
            self.known_nodes[source] = source
            attributes = default_node_attr.copy()
            attributes['label'] = source
            self.handler.add_node(source, **attributes)
            
        if target not in self.known_nodes:
            self.known_nodes[target] = target
            attributes = default_node_attr.copy()
            attributes['label'] = target
            self.handler.add_node(target, **attributes)
        
        eid = source + '_' + target
        if etype == 'ae':
            attributes = {'directed':True, 'weight':2.0}
            self.handler.add_edge(eid, source, target, **attributes)
        if etype == 'de':
            self.handler.delete_edge(eid)

class RequestHandler(BaseHTTPRequestHandler):
        
    def do_POST(self):
        pass

    def do_GET(self):
        
        self.queue = Queue.Queue()
        active_queues.append(self.queue)
        
        self.wfile.write("HTTP/1.1 200 OK\nContent-Type: application/json\n\n")
        
        request_processor = RequestProcessor(self.wfile)
        
        for source, target in graph:
            event = {'type':'ae',
                     'source':str(source),
                     'target':str(target)}
            request_processor.process(event)
        
        while True:
            
            e = self.queue.get()
            if e is None: break
            
            try:
                request_processor.process(e)
            except socket.error:
                print "Connection closed"
                active_queues.remove(self.queue)
                return
        
class Producer(threading.Thread):

    def __init__(self, options):
        self.options = options
        threading.Thread.__init__(self)
        
    def run(self):
        nr_nodes = self.options.nr_nodes
        nr_edges = nr_nodes
        
        while len(graph) < nr_edges:
            source, target = random.sample(xrange(nr_nodes), 2)
            if (source, target) in graph:
                continue
            else:
                graph[(source, target)] = {}
                event = {'type':'ae',
                         'source':str(source),
                         'target':str(target)}
                dispatch_event(event)
        
        while (True):
            source, target = random.choice(graph.keys())
            del graph[(source, target)]
            event = {'type':'de',
                     'source':str(source),
                     'target':str(target)}
            dispatch_event(event)
            
            while (True):
                source, target = random.sample(xrange(nr_nodes), 2)
                if (source, target) in graph:
                    continue
                else:
                    graph[(source, target)] = {}
                    event = {'type':'ae',
                             'source':str(source),
                             'target':str(target)}
                    dispatch_event(event)
                    break
            
            time.sleep(1)
        
class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""
    
    def start(self):
        self.serve_forever()
        
    def stop(self):
        self.socket.close()
        
def parseOptions():
    parser = optparse.OptionParser()
    parser.add_option("-n", "--nr_nodes", type="int", dest="nr_nodes", help="Number of nodes", default=50)
    parser.add_option("-p", "--serverport", type="int", dest="serverport", help="HTTP server port", default=8181)
    (options, _) = parser.parse_args()
    return options
        
def main():
    options = parseOptions()
    producer = Producer(options)
    producer.setDaemon(True)
    producer.start()
    try:
        server = ThreadedHTTPServer(('', options.serverport), RequestHandler)
        print 'Test server running...'
        server.start()
    except KeyboardInterrupt:
        print 'Stopping server...'
        server.stop()
        dispatch_event(None)
        sys.exit(0)

if __name__ == '__main__':
    main()
