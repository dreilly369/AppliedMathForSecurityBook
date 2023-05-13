# -*- coding: utf-8 -*-
import os
import networkx as nx
from optparse import OptionParser
from scapy.all import sniff
from matplotlib import pyplot as plt
import graph_funcs as ext

network_graph = nx.MultiDiGraph()  # global network graph
PACKETS = 10  # Default number of packets to capture before exiting
save_raw = None

if __name__ == '__main__':
    parser = OptionParser()
    # opts for configuring packet capture and processing
    parser.add_option("-i", "--iface", dest="iface", default=None,
        help="The network interface to bind to (required -i all for all)")
    parser.add_option("-c", "--count", dest="count", default=PACKETS,
        help="Number of packets to capture (default %d)" % PACKETS)
    parser.add_option("-r", "--raw-out", dest="raw_file", default=None,
        help="File to save the captured packets to (default None)")
    parser.add_option("-s", "--graph-out", dest="graph_file", default=None,
        help="File to save the created graph to (required)")
    parser.add_option("-l", "--load", dest="load_file", default=None,
        help="Pcap file to load packets from")
    
    (opts, args) = parser.parse_args()
    if opts.graph_file is None:
        print("-s required to save graph")
        exit()
    elif opts.iface is None and opts.load_file is None:
        print("-i or -l option required")
        exit()
    if opts.load_file is not None:
        if os.path.exists(opts.load_file):
            # Load existing pcap file, supercedes live capture
            print("Loading Pcap file")
            if opts.raw_file is not None:
                print("Packet saving turned off during file loading.")
            network_graph = ext.file_to_graph(opts.load_file)
            ext.save_graph(network_graph, opts.graph_file)
            nx.draw_shell(network_graph, node_size=25)   
            plt.show()
        else:
            print("Could not locate file for parsing")
            exit()
    else:
        c = int(opts.count)
        # setup global raw save file if one is defined
        if opts.raw_file is not None:
            save_raw = opts.raw_file
        packets = sniff(filter="ip", count=c)
        network_graph = ext.pcap_graph(packets)
        ext.save_graph(network_graph, opts.graph_file)
        nx.draw_shell(network_graph, node_size=100)   
        plt.show()