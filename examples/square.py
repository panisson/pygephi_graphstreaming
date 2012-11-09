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
Use this script with Gephi and Graph Streaming plugin.
1. Open Gephi, create a new project
2. Go to the tab Streaming, right-click on "Master Server", click on "Start"
3. Go to the tab Layout, select "Force Atlas" and click "Run"
4. Run this script
'''

import pygephi
import time

g = pygephi.GephiClient('http://localhost:8080/workspace0', autoflush=True)
g.clean()

n = 20

node_attributes = {"size":10, 'r':0.0, 'g':0.0, 'b':1.0, 'x':1}

def idx(i,j,n):
    return i*n + j;

# Plane
for i in range(0,n):
    for j in range(0,n):
        # put the nodes in a position that is not (0,0)
        node_attributes['x'] = (i%2)+1
        node_attributes['y'] = (j%2)+1
        g.add_node(str(idx(i,j,n)), **node_attributes)
        
        if i != 0:
            src = str(idx(i,j,n))
            tgt = str(idx(i-1,j,n))
            g.add_edge(src+tgt, src, tgt, directed=False)
        if j != 0:
            src = str(idx(i,j,n))
            tgt = str(idx(i,j-1,n))
            g.add_edge(src+tgt, src, tgt, directed=False)
        time.sleep(0.05)

# Change size and colors
node_attributes = {"size":15, 'r':1.0, 'g':0.0, 'b':0.0}
for i in range(0,n):
    for j in range(0,n):
        g.change_node(str(idx(i,j,n)), **node_attributes)

#g.flush()
time.sleep(30)

# Cylinder
for i in range(0,n):
    src = str(idx(i,n-1,n))
    tgt = str(idx(i,0,n))
    g.add_edge(src+tgt, src, tgt, directed=False)

#g.flush()
time.sleep(10)

# Torus
for j in range(0,n):
    src = str(idx(n-1,j,n))
    tgt = str(idx(0,j,n))
    g.add_edge(src+tgt, src, tgt, directed=False)

#g.flush()
time.sleep(10)

# Delete it
for i in range(0,n):
    for j in range(0,n):
        g.delete_node(str(idx(i,j,n)))

