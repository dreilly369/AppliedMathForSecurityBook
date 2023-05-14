#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar  8 10:42:12 2021

@author: dreilly
"""
import multiprocessing as mp

def solver(p, q):
    gallery_vertices = None
    done = False
    while not done:
        while gallery_vertices == None:
            gallery_vertices = p.get()
            print("got %d" % gallery_vertices)
        solution = "hello"    
        q.put(solution)
        print("put solution")
        done = True

ctx = mp.get_context('fork')
q = ctx.Queue()
p = ctx.Queue()
procs = []
for i in range(0,4):
    proc = ctx.Process(target=solver, args=(p,q))
    proc.start()
    procs.append(proc)
results = []
floors = [1,2,3,4]

for f in floors:
    p.put(f)
while True:
    r = q.get()
    print(r)
    results.append(r)
for proc in procs:
    proc.join()