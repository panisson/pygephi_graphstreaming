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

import time
import pygephi

g = pygephi.GephiClient('http://localhost:8080/workspace0', autoflush=True)
g.clean()
n = 10000
node_attributes = {"size":10, 'r':1.0, 'g':0.0, 'b':0.0, 'x':1}

# Create the snake!
for i in range(0,n):
    node_attributes['y'] = (i%2)+1
    g.add_node(str(i), **node_attributes)
    if (i > 0):
        g.add_edge(str(i), str(i),str(i-1))
    if (i >= 100):
        g.delete_node(str(i-100))
    time.sleep(0.01)
    if ((i%100) == 0):
        # give me a time to rest!
        time.sleep(0.5)
