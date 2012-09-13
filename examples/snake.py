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
