# -*- coding: utf-8 -*-
"""
Created on Mon Feb 29 19:10:14 2016

@author: Vincent
"""

class TweetIndex:  
    
    def __init__(self):
        self.index = {}
        
    def get(self, tag):
        if tag in self.index:
            return self.index[tag]
        else:
            return []
    
    def add(self, tweet):
        tags = []
        for i in range(0,len(tweet)):
            if tweet[i] == '#':
                j = i + 1
                tag = ''
                while(j < len(tweet) and tweet[j] != ' '):
                    tag = tag + tweet[j]
                    j = j + 1
                tags.append(tag)
        for t in tags:
            if t in self.index:
                self.index[t].append(tweet)
            else:
                self.index[t] = [tweet]        