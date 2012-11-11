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
Convert a graph in Json Graph Streaming format to a dynamic GEXF graph. 
Usage: json2gexf.py json_file gexf_file 
'''

try:
    import json
except ImportError:
    try:
        import simplejson as json
    except:
        raise "Requires either simplejson or Python 2.6!"

import gexf
import sys

xml = gexf.Gexf("pygephi - Graph Streaming","https://github.com/panisson/pygephi_graphstreaming")
graph = xml.addGraph("undirected","dynamic","a Json generated graph")

json_file_name = sys.argv[-2]
json_file = open(json_file_name)
file_content = json_file.read()

event_types = set(['an','cn', 'dn', 'ae', 'ce', 'de'])

node_properties = set(['label', 'r', 'g', 'b'])
edge_properties = set(['source', 'target', 'directed', 'label', 'r', 'g', 'b'])

def inject_node_property(node, attr_id, value):
    if attr_id in ['r', 'g', 'b']:
        color = int(value*255)
        setattr(node, attr_id, str(color))
    else:
        setattr(node, attr_id, str(value))

def add_node_attribute(node, attr_id, value):
    if attr_id not in node_properties:
        if attr_id not in graph._attributes['node']:
            graph.addNodeAttribute(title=attr_id, type='string', mode='dinamic', force_id=attr_id)
        node.addAttribute(attr_id, value=str(value))
    else:
        inject_node_property(node, attr_id, value)

def inject_edge_property(edge, attr_id, value):
    setattr(edge, attr_id, str(value))

def add_edge_attribute(edge, attr_id, value):
    if attr_id not in edge_properties:
        if attr_id not in graph._attributes['edge']:
            graph.addEdgeAttribute(title=attr_id, type='string', mode='dinamic', force_id=attr_id)
        edge.addAttribute(attr_id, value=str(value))
    else:
        inject_edge_property(edge, attr_id, str(value))

def add_node(id, t, node_data):
    if id in graph.nodes:
        node = graph.nodes[id]
    else:
        node = graph.addNode(id,id)
    
    node.spells.append({'start':str(t)})
    for attr_id, value in node_data.items():
        add_node_attribute(node, attr_id, value)
    
def change_node(id, t, node_data):
    pass

def delete_node(id, t):
    node = graph.nodes[id]
    node.spells[-1]['end'] = str(t)

def add_edge(id, source, target, directed, t, edge_data):
    if id in graph.edges:
        edge = graph.edges[id]
    else:
        edge = graph.addEdge(id, source, target)
    
    edge.spells.append({'start':str(t)})
    for attr_id, value in edge_data.items():
        add_edge_attribute(edge, attr_id, value)
    
def change_edge(id, t, edge_data):
    pass

def delete_edge(id, t):
    edge = graph.edges[id]
    edge.spells[-1]['end'] = str(t)
    
for line in file_content.split('\r'):
    line = line.strip()
    if len(line) == 0: continue
    event = json.loads(line)
    
    event_type = event_types.intersection(event.keys()).pop()
    t = event['t']
    
    if event_type == 'an':
        for k, v in event['an'].iteritems():
            add_node(k, t, v)
    elif event_type == 'cn':
        for k, v in event['cn'].iteritems():
            change_node(k, t, v)
    elif event_type == 'dn':
        for k, v in event['dn'].iteritems():
            delete_node(k, t)
            
    elif event_type == 'ae':
        for k, v in event['ae'].iteritems():
            source = v.pop('source')
            target = v.pop('target')
            directed = v.pop('directed') if 'directed' in v else False 
            add_edge(k, source, target, directed, t, v)
    elif event_type == 'ce':
        for k, v in event['ce'].iteritems():
            change_edge(k, t, v)
    elif event_type == 'de':
        for k, v in event['de'].iteritems():
            delete_edge(k, t)

gexf_file_name = json_file_name = sys.argv[-1]
gexf_file = file(gexf_file_name, 'w')
xml.write(gexf_file)
gexf_file.close()
