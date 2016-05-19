# -*- coding: utf-8 -*-
"""
Created on Wed May 18 16:42:42 2016

@author: Vincent Rideout
"""

import requests

if __name__ == "__main__":
    name = raw_input("Enter primary name:")
    port = int(raw_input("Enter primary port:"))
    tag = raw_input("Enter something:")
    for i in range(20):
        tweet = "Test tweet #" + tag + str(i)
        requests.post('http://' + name + ":" + str(port), data = {'tweet':tweet,'method':'storeTweet','version':0})