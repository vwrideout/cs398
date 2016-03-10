# -*- coding: utf-8 -*-
"""
Created on Wed Mar 09 18:53:19 2016

@author: Vincent Rideout
"""
import requests 

if __name__ == "__main__":
    get = requests.get("http://localhost:7000/")
    print "GET Response:\n"
    print get.text
    
    post = requests.post("http://localhost:7000/", data = {'tweet': 'this is a #message'})
    print "POST Response:\n"
    print post.text