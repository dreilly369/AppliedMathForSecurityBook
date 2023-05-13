# -*- coding: utf-8 -*-
import networkx as nx
from random import random


def _ra(G, u, v, resource=1):
    
    if not nx.has_path(G, u, v):
        return (u, v, 0.0, [])
    disjoint_paths = nx.node_disjoint_paths(G, u, v)
    results = []
    for djp in disjoint_paths:
        pairs = []
        remaining = resource
        for i in range(0, len(djp) - 1):
            pairs.append((djp[i], djp[i+1]))
            neighs = len(list(G.neighbors(djp[i])))
            passes = 1 / neighs
            #print(djp[i], djp[i+1], passes)
            remaining = remaining*passes
        results.append(remaining)
    return (u,v,sum(results))
    
    
def weighted_choice(scores):
    """Input a dictionary of key: weight
    Output a key selected with probability
    equal to it's relative weight.
    Weights do not need to sum to 1"""
    totals = []
    running_total = 0

    for w in scores.values():
        running_total += w
        totals.append(running_total)

    rnd = random() * running_total
    for i in range(len(totals)):
        if rnd <= totals[i]:
            key = list(scores.keys())[i]
            return key
            
            
def directed_resource_allocation_index(G, ebunch, resource=1):
    """Implements RA alg for directed graphs"""
    if not nx.is_directed(G):
        raise("Use nx.resource_allocation for undirected graphs")
    if isinstance(ebunch, tuple):
        u,v = ebunch
        return _ra(G, *ebunch, resource=resource)
    res = []
    for pair in ebunch:
        #print("processing other", ebunch)
        res.append(_ra(G, *pair, resource=resource))
    return res
    
    
def scored_neighbor_select(G, on, scores):
    neighbors = nx.neighbors(G, on)
    n_scores = {k: scores[k] for k in neighbors}
    return weighted_choice(n_scores)
   
def hub_send(hub_score):
    pass_val = 1 - hub_score
    keys = {"send": hub_score, "pass": pass_val}
    if weighted_choice(keys) == "send":
        return True
    else:
        return False
        
def term_subgraph(term, df):
    dat_rows = df[df["text"].str.contains(term)]
    dat_replies = df[df["in_reply_to_tweet_id"].isin(dat_rows["id"].values)]
    hG = nx.DiGraph()
    for idx in dat_replies.index:
        row = dat_replies.loc[idx]
        hG.add_edge(row["in_reply_to_screen_name"], row["user_screen_name"])    
    return hG
