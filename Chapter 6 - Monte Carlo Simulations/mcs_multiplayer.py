# -*- coding: utf-8 -*-
import json
import networkx as nx
from random import choice, random
import pandas as pd
import graph_funcs as ext
import scipy.stats as stats
import numpy as np
from matplotlib import pyplot as plt

def user_to_series(dict_obj):
    """Convert a nested JSON user to a flat pandas series"""
    renamed = {}
    for k in dict_obj.keys():
        nk = "user_%s" % k
        v = dict_obj[k]
        renamed[nk] = v
    ret = pd.Series(renamed)
    return ret

def ncap_weights(G, u):
    u_in = list(G.in_edges(u, data=True))
    if len(u_in) < 1:
        #print("%s no in-degree" % u)
        return (None, None)
    n_capacity = {}
    for v,u,d in u_in:
        n_capacity[v] = d["capacity"]
    #print("ncap", n_capacity.items())
    Q = 1 + max([itm[1] for itm in list(n_capacity.items())])
    n_weight = {k: (Q - n_capacity[k]) for k in n_capacity.keys()}
    return (n_capacity, n_weight)

def wrs_connect(G, u):
    scores = {}
    for i in range(len(G.nodes.keys())):
        v = list(G.nodes.keys())[i]
        if v == u:
            continue
        dpa_score = G.out_degree(u) * G.in_degree(v)      
        scores[v] = dpa_score
    return ext.weighted_choice(scores)

def wrs_disconnect(G, u):
    u_in = list(G.in_edges(u))
    if len(u_in) < 1:
        #print("%s has noone to disconnect" % u)
        return None
    caps, scores = ncap_weights(G, u)
    if scores is not None:
        return ext.weighted_choice(scores)

def player_one_turn(G, uq, omega):
    if G.has_edge(uq, omega):
        #print("goal node in edges")
        return (omega, G)
    caps = [d["capacity"] for u,v,d in G.edges(data=True)]
    avg_cap = sum(caps) / len(caps)
    
    for u in list(G.nodes.keys()):
        if u == uq:
            try:
                paths = list(nx.all_shortest_paths(G, u, omega))                
            except nx.exception.NetworkXNoPath:
                #print("No path between %s and %s" % (uq, omega))
                return (uq, G)
            path = choice(paths)
            #print("path to goal", path)
            pass_to = path[1]
        else:
            act = ext.weighted_choice(XI)
            if act == "pass":
                continue
            elif act == "connect":
                v_conn = wrs_connect(G, u)
                #print("connecting %s to %s" % (u, v_conn))
                G.add_edge(u, v_conn, capacity=avg_cap)
            else:
                v_disconn = wrs_disconnect(G, u)
                if v_disconn is None:
                    continue
                #print("%s disconnecting from" % u, v_disconn)
                G.remove_edge(v_disconn, u)
    return (pass_to, G)

def player_two_random(G):
    e = choice(list(G.edges()))
    G.remove_edge(*e)
    return G
    
def player_two_turn(G, uq, omega):
    cut_value, partition = nx.minimum_cut(G, uq, omega)
    reachable, unreachable = partition
    cutset = set()
    for u, nbrs in ((n, G[n]) for n in reachable):
        cutset.update((u, v) for v in nbrs if v in unreachable)
    caps, scores = ncap_weights(G, omega)
    if len(cutset) >= 2:
        cut = choice(list(cutset))
        G.remove_edge(*cut)
    elif len(cutset) == 1:
        #print("Single cut to disconnect %s from %s" % (uq, omega))
        cut = list(cutset)[0]
        G.remove_edge(*cut)
    return G

def shortest_path_scores(G):
    pairs = []
    for u, v in nx.non_edges(G):
        if u == v:
            continue
        if not nx.has_path(G, u, v):
            continue
        uv_paths = list(nx.all_shortest_paths(G, u, v))
        avg_len = sum([len(p) for p in uv_paths]) / len(uv_paths)
        pairs.append(((u, v), len(uv_paths), avg_len))
        #print(((u, v), len(uv_paths), avg_len))
    sorted_scores = sorted(
        pairs,
        key=lambda kv: (kv[2], kv[1], kv[0]),
        reverse=True
    )
    return sorted_scores
 
def check_win(G, uq, omega):
    if uq != omega and nx.has_path(G, uq, omega):
        return None
    elif uq == omega:
        #print("\t\tplayer ONE Wins")
        return 1
    elif not nx.has_path(G, uq, omega):
        #print("\t\tplayer TWO Wins")
        return -1

def simulate(G,num_samples=25,num_sims=25,num_steps=10, rand_player=True):
    path_scores = shortest_path_scores(G)
    path_weights = {(p[0][0], p[0][1]): p[2] for p in path_scores}
    played = []
    pop_avgs = []
    for r in range(num_samples):
        selected = ext.weighted_choice(path_weights)
        while selected in played:
            # pick a different pair of nodes
            selected = ext.weighted_choice(path_weights)
        played.append(selected)
        #print(selected, path_weights[selected])
        alpha = selected[0] # Starting Node
        omega = selected[1] # Goal Node
        game_res = [] # Holds the result of each simulation
        for i in range(num_sims):
            newG = G.copy() # Copy the base graph for a new game
            now_at = alpha
            for j in range(num_steps):
                w = check_win(newG, now_at, omega)
                if w is not None:
                    game_res.append(w)
                    break
                now_at, newG = player_one_turn(newG, now_at, omega)
                if not check_win(newG, now_at, omega):
                    if rand_player:
                        newG = player_two_random(newG)
                    else:
                        newG = player_two_turn(newG, now_at, omega)
        tally = sum(game_res)
        avg = tally / len(game_res)
        pop_avgs.append(float(avg))
        print(f"Sample {r}: Average {avg}")
    return pop_avgs


XI = {
    "connect": 2,
    "disconnect": 1,
    "pass": 2
}

############### These are the variables you may want to play with ###############
retests = 250 # number of times to resample the simulation to create the test population
k = 25 # number of simulations per game
n = 50 # number of steps per simulation
confidence_in_mean = 0.95 # Confidence to use when predicting the population mean
confidence_in_conclusion = 0.99 # Confidence level used to reject the null hypothesis
################################################

############### Begin Running the simulations ###############
G = nx.DiGraph()

# process the tweet data to create the network
series_data = [] # 1 JSON object per tweet object
with open("fake_tweets.json") as data:
    text = data.read().strip()
    rows = text.split("\n")  # JSON objects stored as list of strings
for row in rows:
    obj = json.loads(row) # Converted row string to JSON object
    series_data.append(obj) # Add to JSON list

tweet_df = pd.DataFrame(series_data) # 1 row per JSON obj
tweet_df = pd.concat([tweet_df, tweet_df['user'].apply(user_to_series)], axis=1)
# Now the data is flattened. We remove the field containing the JSON object
tweet_df.drop("user", axis=1, inplace=True)
tweet_df.dropna(axis=0, inplace=True)
tweet_df["in_reply_to_tweet_id"] = tweet_df["in_reply_to_tweet_id"].astype(int)
tweet_df["in_reply_to_user_id"] = tweet_df["in_reply_to_user_id"].astype(int)
tweet_df["user_id"] = tweet_df["user_id"].astype(int)


for idx in tweet_df.index:
    row = tweet_df.loc[idx]
    u = row["in_reply_to_screen_name"]
    v = row["user_screen_name"]
    w = len(row["text"])
    if G.has_edge(u,v):
        G[u][v]["capacity"] += w
    else:
        G.add_edge(u, v, capacity=w)
        
# Create the base line with the random player
print("Testing Random Player 2 strategy:")
rand_p2_avgs = simulate(G,num_samples=retests,num_sims=k,num_steps=n, rand_player=True)
rand_p2_pop_avg = np.mean(rand_p2_avgs)
print(f"Random Player 2 Population Average {rand_p2_pop_avg}")
#create confidence interval for random player 2 population mean
rand_p2_pop_interval = stats.t.interval(
    alpha=confidence_in_mean,
    df=len(rand_p2_avgs)-1,
    loc=np.mean(rand_p2_avgs),
    scale=stats.sem(rand_p2_avgs)
)
print(f"Random Player 2 Interval {rand_p2_pop_interval}")
print("")

# Create the improved player's data
print("Testing Smarter Player 2 strategy:")
smart_p2_avgs = simulate(G,num_samples=retests,num_sims=k,num_steps=n, rand_player=False)
smart_p2_pop_avg = np.mean(smart_p2_avgs)
print(f"Smart Player 2 Population Average {smart_p2_pop_avg}")
#create confidence interval for smart player 2 population mean
smart_p2_pop_interval = stats.t.interval(
    alpha=confidence_in_mean,
    df=len(smart_p2_avgs)-1,
    loc=np.mean(smart_p2_avgs),
    scale=stats.sem(smart_p2_avgs)
)
print(f"Smart Player 2 Interval {smart_p2_pop_interval}")

# Run the one-tailed T-Test. We are asserting the random player's mean 
# will be strictly greater than the mean of the improved player's
ttest_score = abs(stats.ttest_ind(rand_p2_avgs, smart_p2_avgs, alternative='greater').pvalue)
thresh = 1-confidence_in_conclusion
if thresh < ttest_score:
    print("We cannot reject the null hypothesis. No significant difference detected.")
else:
    print("We can reject the null hypothesis. The two samples are significantly different")

xmin = -1 # no game can score lower than -1
xmax = 1 # no game can score higher than +1
X1 = stats.norm(np.mean(rand_p2_avgs), np.std(rand_p2_avgs)) # Random Player normal distribution
xs1 = np.linspace(xmin,xmax,50)  # create 100 x values in that range
plt.plot(xs1,X1.pdf(xs1), "--.", alpha=0.33) # plot the shape of the distribution

X2 = stats.norm(np.mean(smart_p2_avgs), np.std(smart_p2_avgs)) # Smart Player normal distribution
xs2 = np.linspace(xmin,xmax,100)  # create 100 x values in that range
plt.plot(xs2,X2.pdf(xs2)) # plot the shape of the distribution
plt.legend(["Random Player", "Smart Player"])
plt.yticks([])
plt.ylabel("Likelihood")
plt.xlabel("Population Result")
plt.title("Simulation Score Distribution")
#plt.savefig("Figure_6-4.png")
#plt.savefig("Figure_6-4.svg", format="svg")
plt.show()
