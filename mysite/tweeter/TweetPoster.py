# -*- coding: utf-8 -*-
"""
Created on Mon May 09 16:09:06 2016

@author: Vincent Rideout
"""
import requests

if __name__ == "__main__":
    name = raw_input("Enter primary name:")
    port = int(raw_input("Enter primary port:"))
    while(True):
        tweet = raw_input("Enter a tweet here:")
        if tweet == 'exit':
            break
        requests.post('http://' + name + ":" + str(port), data = {'tweet':tweet,'method':'storeTweet','version':0})