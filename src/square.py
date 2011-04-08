'''
Use this script with Gephi and Graph Streaming plugin.
1. Open Gephi, create a new project
2. Go to the tab Streaming, right-click on "Master Server", click on "Start"
3. Go to the tab Layout, select "Force Atlas" and click "Run"
4. Run this script
'''

import pygephi
import time

g = pygephi.JSONClient('http://localhost:8080/workspace0', autoflush=True)
g.clean()

n = 20

node_attributes = {"size":10, 'r':0.0, 'g':0.0, 'b':1.0, 'x':1}

def idx(i,j,n):
    return i*n + j;

# Plane
for i in range(0,n):
    for j in range(0,n):
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

