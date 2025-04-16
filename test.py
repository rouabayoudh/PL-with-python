import networkx as nx
import matplotlib.pyplot as plt
import io

import matplotlib
matplotlib.use('Agg')

def render_graph(edges, colors):
    G = nx.Graph()
    G.add_edges_from(edges)
    labels = {i: i for i in G.nodes}
    pos = nx.spring_layout(G) 
    plt.figure(figsize=(5, 5))

    nx.draw(G, pos, with_labels=True, labels=labels, node_color='lightblue', node_size=1000, font_size=12)

    nx.draw_networkx_nodes(G, pos, node_color=[colors[i] for i in G.nodes], cmap=plt.cm.rainbow, node_size=1000)     

    plt.savefig("./static/test.png", format='png')
    plt.close()

