import random
from lib.Exceptions import *
import thread


class Node(object):
    
    def __init__(self, element):
        self.element = element
        self.id = element.GetId()
        self.object = element.GetObject()
        self.previous = self.object.GetValue('previous')
        self.shortest = float(self.object.GetValue('shortest'))
        self.final = 'True' == self.object.GetValue('final')
        self.current = 'True' == self.object.GetValue('current')
        self.connections = []
    
    def AddConnection(self, connection):
        self.connections.append(connection)
    
    def Save(self):
        self.object.SetValue('previous', str(self.previous))
        self.object.SetValue('shortest', str(self.shortest))
        self.object.SetValue('final', str(self.final))
        self.object.SetValue('current', str(self.current))

class Edge(object):
    
    def __init__(self, connection):
        self.connection = connection
        self.id = connection.GetId()
        self.object = connection.GetObject()
        self.value = float(self.object.GetValue('value'))
        self.directed = self.object.GetValue('directed')
        self.reversed = self.object.GetValue('reversed')
        self.edges = []
    
    def Save(self):
        self.object.SetValue('value', str(self.value))
        self.object.SetValue('directed', str(self.directed))
        self.object.SetValue('reversed', str(self.reversed))
    
    def AddEdge(self, edge):
        self.edges.append(edge)
    
    def Next(self, edge):
        if self.edges[0].id == edge.id:
            return self.edges[1]
        else:
            return self.edges[0]
    
    def Directions(self):
        if self.edges[0].previous == self.edges[1].id:
            self.directed = True
            self.reversed = True
        elif self.edges[1].previous == self.edges[0].id:
            self.directed = True
            self.reversed = False
        else:
            self.directed = False
        

class Plugin(object):
    
    def __init__(self, interface):
        self.interface = interface
        self.interface.SetGtkMainloop()
        adapter = self.interface.GetAdapter()
        bar = adapter.GetButtonBar()
        bar.AddStockButton('cmdDijkstraReset', self.onReset, -1, 'gtk-refresh', 'Reset')
        bar.AddStockButton('cmdDijkstraForward', self.onStep, -1, 'gtk-go-forward', 'Step')
        
    def onReset(self, *args):
        try:
            with self.interface.GetTransaction():
                project = self.interface.GetAdapter().GetProject()
                if project is None:
                    self.interface.DisplayWarning('No project loaded')
                    return
                
                metamodel = project.GetMetamodel()
                if metamodel.GetUri() != 'urn:umlfri.org:metamodel:graphTheory':
                    self.interface.DisplayWarning('Not supported metamodel')
                    return
                
                diagram = self.interface.GetAdapter().GetCurrentDiagram()
                if diagram is None or diagram.GetType() != 'Graph':
                    self.interface.DisplayWarning('This is not a Graph')
                    return
                
                s = [i.GetId() for i in diagram.GetSelected()]
                if len(s) > 1:
                    self.interface.DisplayWarning('Too many nodes selected')
                    return
                for e in diagram.GetElements():
                    n = Node(e)
                    if n.id in s:
                        n.shortest = 0.0
                        n.previous = ''
                        n.final = True
                        n.current = True
                    else:
                        n.shortest = float('inf')
                        n.previous = ''
                        n.final = False
                        n.current = False
                    n.Save()
                
                for c in diagram.GetConnections():
                    e = Edge(c)
                    e.directed = False
                    e.reversed = False
                    e.Save()
            
        
        except PluginProjectNotLoaded:
            self.interface.DisplayWarning('Project is not loaded')
        
    
    def onStep(self, *args):
        try:
            with self.interface.GetTransaction():
                
                project = self.interface.GetAdapter().GetProject()
                if project is None:
                    self.interface.DisplayWarning('No project loaded')
                    return
                
                metamodel = project.GetMetamodel()
                if metamodel.GetUri() != 'urn:umlfri.org:metamodel:graphTheory':
                    self.interface.DisplayWarning('Not supported metamodel')
                    return
                
                diagram = self.interface.GetAdapter().GetCurrentDiagram()
                if diagram is None or diagram.GetType() != 'Graph':
                    self.interface.DisplayWarning('This is not a Graph')
                    return
                
                nodes = {}
                edges = {}
                cur = None
                
                for e in diagram.GetElements():
                    n = Node(e)
                    nodes[n.id] = n
                    if n.current:
                        cur = n
                
                for c in diagram.GetConnections():
                    e = Edge(c)
                    s = nodes[c.GetSource().id]
                    d = nodes[c.GetDestination().id]
                    edges[c.id] = e
                    s.AddConnection(e)
                    d.AddConnection(e)
                    e.AddEdge(s)
                    e.AddEdge(d)
                
                for e in cur.connections:
                    n = e.Next(cur)
                    if n.shortest > cur.shortest + e.value:
                        n.shortest = cur.shortest + e.value
                        n.previous = cur.id
                
                m = None
                for n in nodes.values():
                    if not n.final:
                        if m is None:
                            m = n
                        elif m.shortest > n.shortest:
                            m = n
                if m is not None:
                    m.final = True
                    cur.current = False
                    m.current = True
                    
                for n in nodes.values():
                    n.Save()
                
                for e in edges.values():
                    e.Directions()
                    e.Save()
        
        except PluginProjectNotLoaded:
            self.interface.DisplayWarning('Project is not loaded')

# select plugin main object
pluginMain = Plugin
