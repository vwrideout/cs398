# -*- coding: utf-8 -*-
"""
Created on Wed May 18 13:23:21 2016

@author: Vincent Rideout
"""

import requests

if __name__ == "__main__":
    primary = int(raw_input("Enter primary port to simulate failure on:"))
    name = raw_input("Enter first name (Type 'Done' to finish):")
    port = raw_input("Enter first port:")
    nodes = []
    while(name != 'Done'):
        nodes.append((name,port))
        name = raw_input("Enter next name (Type 'Done' to finish):")
        port = raw_input("Enter first port:")
    
    for name, port in nodes:    
        requests.get("http://" + name + ":" + port + "/", params={'clientAddress':'poster','clientPort':0,'clientRank':'Secondary','method':'election','version':0,'ID':primary}, headers={'Connection':'close'}, timeout=6.5)
