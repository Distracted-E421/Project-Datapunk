import matplotlib.pyplot as plt
import networkx as nx

# Create a new graph object
G = nx.DiGraph()

# Adding nodes (VMs) with attributes such as IP address and running services
G.add_node("Windows VM", ip="192.168.56.10", services=["RDP (Remote Desktop)"])
G.add_node("Ubuntu VM", ip="192.168.56.20", services=["Apache Web Server (HTTP)"])
G.add_node("NixOS VM", ip="192.168.56.30", services=["SSH Server"])

# Adding edges (connections) to represent the network relationships and directions
# Windows VM to Ubuntu VM - Apache HTTP Service
G.add_edge("Windows VM", "Ubuntu VM", connection="HTTP (Port 80)")

# Windows VM to NixOS VM - SSH Service
G.add_edge("Windows VM", "NixOS VM", connection="SSH (Port 22)")

# Ubuntu VM to NixOS VM - SSH Service
G.add_edge("Ubuntu VM", "NixOS VM", connection="SSH (Port 22)")

# Ubuntu VM to Windows VM - Apache HTTP Service
G.add_edge("Ubuntu VM", "Windows VM", connection="HTTP (Port 80)")

# NixOS VM to Windows VM - RDP Service
G.add_edge("NixOS VM", "Windows VM", connection="RDP (Port 3389)")

# Positioning the nodes using spring layout for better visualization
pos = nx.spring_layout(G)

# Draw the nodes with specific attributes
node_labels = {node: f"{node}\nIP: {attrs['ip']}\nServices: {', '.join(attrs['services'])}" for node, attrs in G.nodes(data=True)}

# Draw nodes
nx.draw_networkx_nodes(G, pos, node_size=3000, node_color="skyblue")

# Draw edges with connection labels
nx.draw_networkx_edges(G, pos, arrowstyle='->', arrowsize=15, edge_color='black', width=2)

# Draw labels for nodes
nx.draw_networkx_labels(G, pos, labels=node_labels, font_size=9, font_weight="bold")

# Draw edge labels (connections and ports)
edge_labels = {(u, v): d['connection'] for u, v, d in G.edges(data=True)}
nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='red', font_size=8)

# Display the plot
plt.title("Network Diagram Lab 2")
plt.axis('off')
plt.show()

# Save the diagram as an image
plt.savefig("detailed_network_diagram.png", format="PNG")
