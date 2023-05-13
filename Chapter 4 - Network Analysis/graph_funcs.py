# -*- coding: utf-8 -*-
import networkx as nx
from scapy.all import rdpcap, IP, TCP, UDP, wrpcap
from datetime import datetime


def file_to_graph(pcap_file):
    packets = rdpcap(pcap_file)
    new_graph = pcap_graph(packets)
    return new_graph
    
    
def save_graph(G, out_file):
    """Save a weighted edge list of a graph
    Parameters:
        G: a weighted graph to save
        out_file: a path to save the file to"""
    now = datetime.now()
    dt_str = datetime.strftime(now, "%Y-%m-%d %H:%M")
    nx.write_weighted_edgelist(
        G,
        out_file,
        comments="# Created from packet data %s" % dt_str
    )
    
    
def save_packet(packet, out_file):
    """Append a packet to a Pcap file
    Parameters:
        packet: a Scapy packet to save
        out_file: The path to the output file"""
    wrpcap(out_file, packet, append=True)    


def exchange_ratios(G):
    """Calculate Information Exchange Ratio for every node"""
    res = []
    for u in G.nodes.keys():
        out_edges = G.out_edges(u, data=True)
        in_edges = G.in_edges(u, data=True)
        #print(u, len(in_edges), len(out_edges))
        if len(out_edges) > 0:
            out_w = 1 + sum([d["weight"] for u,v,d in out_edges])
        else:
            out_w = 1
        if len(in_edges) > 0:
            in_w = sum([d["weight"] for u,v,d in in_edges])
        else:
            in_w = 1
        ier = in_w / out_w
        res.append((u, ier))
    return sorted(res, key=lambda x: x[1])


def pcap_graph(packets):
    net_graph = nx.MultiDiGraph()
    for packet in packets:
        if not packet.haslayer(IP):
            # Not a packet we want to analyze.
            continue
        mac_src = packet.src # Sender MAC
        mac_dst = packet.dst # Receiver MAC
        ip_src = packet[IP].src # Sender I.P.
        ip_dst = packet[IP].dst # Receiver I.P.
        w = packet[IP].len # number of bytes in packet
        if packet.haslayer(TCP):
            sport=packet[TCP].sport # Sender port
            dport=packet[TCP].dport # Receiver port
        elif packet.haslayer(UDP):
            sport=packet[UDP].sport # Sender port
            dport=packet[UDP].dport # Receiver port
        else:
            # Not a packet we want to analyze.
            continue
        # Define an edge in the graph
        net_graph.add_edge(
            *(str(mac_src), str(mac_dst)),
            ip_src=ip_src,
            ip_dst=ip_dst,
            sport=sport,
            dport=dport,
            weight=w
        )
    return net_graph


def protocol_subgraph(G, port):
    """Return a subgraph of G, filtered by the destination port"""
    proto_edges = [(u,v,d) for u,v,d in G.edges(data=True) if d["dport"] == port]
    if len(proto_edges) < 1:
        return None
    sub_graph = nx.DiGraph()
    sub_graph.add_edges_from(proto_edges)
    return sub_graph
    
    
def label_set(G):
    """Create shortened label set (last 3 octets of MAC address)
    e.g. a1:b2:c3"""
    return {l:l[-8:] for l in G.nodes()}  # Dict Comprehension to create 