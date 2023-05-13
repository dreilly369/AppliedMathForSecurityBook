# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, "/home/dreilly/anaconda3/pkgs")
sys.path.insert(0, "/usr/local/lib/python3.5/dist-packages")
from scapy.all import traceroute

a,u=traceroute(["www.python.org", "google.com","slashdot.org"])
a.trace3D()