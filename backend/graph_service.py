import networkx as nx
from .database import DatabaseManager

class GraphService:
    def __init__(self):
        self.db = DatabaseManager()
        self.graph = nx.DiGraph()
        self.refresh()

    def refresh(self):
        self.graph.clear()
        nodes = self.db.get_all_nodes()
        edges = self.db.get_edges()
        for n in nodes: self.graph.add_node(n['id'], **dict(n))
        for e in edges: self.graph.add_edge(e['source_id'], e['target_id'], type=e['type'])

    def get_context_for_function(self, node_id):
        if node_id not in self.graph: return None
        dependencies = []
        if self.graph.has_node(node_id):
            for neighbor in self.graph.successors(node_id):
                if self.graph.get_edge_data(node_id, neighbor).get('type') == 'calls':
                    n = self.graph.nodes[neighbor]
                    dependencies.append({"name": n.get('name'), "summary": n.get('summary', 'No summary.'), "file": n.get('file_path')})
            usages = []
            for pred in self.graph.predecessors(node_id):
                if self.graph.get_edge_data(pred, node_id).get('type') == 'calls':
                    usages.append(self.graph.nodes[pred].get('name'))
            return {"target": self.graph.nodes[node_id], "dependencies": dependencies, "usages": usages}
        return None
    
    def get_full_graph_data(self):
        nodes = []
        edges = []
        
        valid_nodes = {n for n, attr in self.graph.nodes(data=True) if attr.get('type') == 'function'}
        
        for n_id in valid_nodes:
            attr = self.graph.nodes[n_id]
            degree = self.graph.degree(n_id)
            color = "#ff4b4b" if degree > 5 else "#00C851" if degree < 2 else "#33b5e5"
            
            nodes.append({
                "id": n_id,
                "label": attr.get('name'),
                "color": color,
                "title": attr.get('file_path')
            })
            
        for u, v, attr in self.graph.edges(data=True):
            if u in valid_nodes and v in valid_nodes and attr.get('type') == 'calls':
                edges.append({"source": u, "target": v})
                
        return nodes, edges

