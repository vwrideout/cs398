# -*- coding: utf-8 -*-
"""
Created on Wed Apr 27 20:54:49 2016

@author: Vincent Rideout
"""

import BaseHTTPServer
import time
import cgi
import requests
import thread
import threading
import urlparse
import copy

class TweetServer(BaseHTTPServer.HTTPServer,object):
    
    def __init__(self,(name,port),handler,rank,primaryAddress,primaryPort,test):
        super(TweetServer,self).__init__((name,port),handler)
        self.system = TweetSystem(name,port,rank,primaryAddress,primaryPort,test)
        self.lock = threading.Lock()
        self.running = True
        self.finished = False
        self.failedPrimaryPort = 0
        self.primaryNotificationReceived = 0
        self.electing = False
        if test == 'ElectionTest':
            self.ELECTIONTEST = True
        else:
            self.ELECTIONTEST = False
        if test == 'PNTest':
            self.PRIMARYNOTIFICATIONTEST = True
        else:
            self.PRIMARYNOTIFICATIONTEST = False
        thread.start_new_thread(self.heartbeat,())

    def storeTweet(self,tweet,version):
        if self.system.getRank() == 'Primary':
            if self.system.storeTweet(tweet):
                self.replicateTweet(tweet,self.system.getVersion())
        elif version == self.system.getVersion() + 1:
            self.system.storeTweet(tweet)
            
    def replicateTweet(self,tweet,version):
        secondaries = self.system.getSecondaryAddresses()
        for name,port in secondaries:
            try:
                "Replicating tweet to " + name+str(port)
                requests.post("http://" + name + ":" + str(port) + "/", data = {'tweet':tweet,'method':'storeTweet','version':version}, headers={'Connection':'close'},timeout=6.5)
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                print e
                self.nodeFailure(port,'Normal')
                
    def heartbeat(self):
        time.sleep(15)
        while(self.running):
            addresses = self.system.getAllAddresses()
            for address in addresses:
                if not self.electing:
                    print "Sending heartbeat to  " + address[0]+str(address[1])
                    if not self.ping(address[0],address[1],'heartbeat',0):
                        print "Heartbeat to  " + address[0]+str(address[1]) + " failed."
                        self.nodeFailure(address[1],'Normal')   
                    else:
                        print "Heartbeat to " + address[0]+str(address[1]) + " successful."
                        self.system.resetStatus(address[1])
            time.sleep(15)
        self.lock.acquire()
        self.finished = True
        self.lock.release()
                
    def ping(self,name,port,method,ID):
        try:
            requests.get("http://" + name + ":" + str(port) + "/", params={'clientAddress':str(self.system.getName()),'clientPort':str(self.system.getPort()),'clientRank':self.system.getRank(),'method':method,'version':str(self.system.getVersion()),'ID':ID}, headers={'Connection':'close'}, timeout=6.5)
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            print e
            return False
        return True      
        
    def nodeFailure(self,port,level):
        if level == 'Normal':
            status = self.system.incrementNodeStatus(port)
            print "Failure at node " + str(port) + " Status:" + str(status)
            if status > 3:
                level = 'Severe'
        if level == 'Severe':
            print "SEVERE FAILURE AT " + str(port) + ". REMOVING."
            primaryName, primaryPort = self.system.getPrimaryAddress()
            self.system.removeNode(port)
            if port == primaryPort:
                print "PRIMARY HAS FAILED! INITIATING ELECTION."
                thread.start_new_thread(self.election,(port,))
                
    def checkNode(self,name,port,rank,version):
        if not self.system.nodeExists(name,port):
            print "NEW NODE FOUND AT " + name+str(port)
            self.system.addNode(name,port,rank)
            if self.system.getRank() == 'Primary':
                self.sendAddresses(name,port)
        if self.system.getRank() == 'Primary' and self.system.getVersion() > version:
            print name + str(port) + " is behind. Updating..."
            self.catchup(name,port,version)
            
    def sendAddresses(self,name,port):
        print "Sending addresses to " + name+str(port)
        for nodename,nodeport in self.system.getAllAddresses():
            if port != nodeport:
                try:
                    requests.post("http://" + name + ":" + str(port) + "/", data = {'name':nodename,'port':nodeport,'method':'storeAddress','version':0}, headers={'Connection':'close'},timeout=6.5)
                except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                    print e
                    print "Failed to reach " + name+str(port) + " in sendAddresses."
                    self.nodeFailure(name,port,'Severe')
                    
    def storeAddress(self,name,port):
        print "New node discovered from primary! Address: " + name+str(port)
        self.system.addNode(name,port,'Secondary')
           
    def catchup(self,name,port,version):
        oldTweets = self.system.dumpLog(version)
        for oldTweet,oldVersion in oldTweets:
            try:
                print "Sending backup tweet #" + str(oldVersion) + " to " + name+str(port)
                requests.post("http://" + name + ":" + str(port) + "/", data = {'tweet':oldTweet,'method':'storeTweet','version':oldVersion}, headers={'Connection':'close'},timeout=6.5)
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                print e
                self.nodeFailure(name,port,'Normal')
        
    def election(self,ID):
        self.lock.acquire()
        if ID == self.failedPrimaryPort:
            print "This node has already run this election. Exiting election thread."
            return
        self.failedPrimaryPort = ID
        self.electing = True
        self.lock.release()
        failures = 0
        higherPorts = self.system.getHigherAddresses()
        for name,higherPort in higherPorts:
            if self.PRIMARYNOTIFICATIONTEST:
                time.sleep(10)
            self.lock.acquire()
            if self.primaryNotificationReceived == ID:
                self.electing = False
                self.lock.release()
                return
            self.lock.release()
            print "Sending election notification to " + str(name)+str(higherPort)
            if not self.ping(name,higherPort,'election',ID):
                print "Name" + name + "Port " + str(higherPort) + " failed in election thread."
                failures += 1
        if failures >= len(higherPorts):
            self.becomePrimary(ID)
        self.lock.acquire()
        self.electing = False
        self.lock.release()
            
    def becomePrimary(self,ID):
        print "WON ELECTION, SENDING PRIMARY NOTIFICATIONS."
        self.system.setRank('Primary')
        for name,port in self.system.getAllAddresses():
            if not self.ping(name,port,'newPrimary',ID):
                print "Port " + str(port) + " failed during primary notification."
                self.nodeFailure(port,'Severe')
                
    def newPrimary(self,port,ID):
        self.lock.acquire()
        self.failedPrimaryPort = ID
        self.primaryNotificationReceived = ID
        self.lock.release()
        self.system.setPrimary(port)
    
    def shutdown(self):
        self.lock.acquire()
        self.running = False
        self.lock.release()
        
    def waitForShutdown(self):
        while True:
            self.lock.acquire()
            if self.finished:
                return
            self.lock.release()
            time.sleep(5)
    
    def toString(self):
        return self.system.toString()
                

class TweetHandler(BaseHTTPServer.BaseHTTPRequestHandler):  
        
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type','text/html')
        self.end_headers()
        self.wfile.write("This server works!")
        self.wfile.close()
        clientAddress = str(urlparse.parse_qs(urlparse.urlparse(self.path).query).get('clientAddress', None)[0])
        clientPort = int(urlparse.parse_qs(urlparse.urlparse(self.path).query).get('clientPort', None)[0])
        clientRank = str(urlparse.parse_qs(urlparse.urlparse(self.path).query).get('clientRank', None)[0])
        version = int(urlparse.parse_qs(urlparse.urlparse(self.path).query).get('version', None)[0])
        method = str(urlparse.parse_qs(urlparse.urlparse(self.path).query).get('method', None)[0])
        if not ((method == 'election' and self.server.ELECTIONTEST) or (method == 'newPrimary' and self.server.PRIMARYNOTIFICATIONTEST)):
            self.server.checkNode(clientAddress,clientPort,clientRank,version)
        if method == 'election':
            print "Received election notification from port " + str(clientPort)
            ID = float(urlparse.parse_qs(urlparse.urlparse(self.path).query).get('ID', None)[0])
            thread.start_new_thread(self.server.election,(ID,))
        if method == 'newPrimary':
            print "Received new primary notification from port " + str(clientPort)
            ID = float(urlparse.parse_qs(urlparse.urlparse(self.path).query).get('ID', None)[0])
            self.server.newPrimary(clientPort,ID)
        return
        
    def do_POST(self):
        temp = "the post works!"
        self.send_response(200)
        self.send_header('Content-type','text/html')
        self.send_header('Content-length',str(len(temp)))
        self.end_headers()
        self.wfile.write(temp)
        self.wfile.close()
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD':'POST',
                     'CONTENT_TYPE':self.headers['Content-Type'],
            })
        method = str(form.getvalue('method'))
        if method == 'storeTweet':
            tweet = str(form.getvalue('tweet'))
            tweetVersion = int(form.getvalue('version'))
            self.server.storeTweet(tweet,tweetVersion)
        elif method == 'storeAddress':
            name = str(form.getvalue('name'))
            port = int(form.getvalue('port'))
            self.server.storeAddress(name,port)
        return
           
                
class TweetSystem:
    
    def __init__(self, name, port, rank, primaryAddress, primaryPort, test):
        self.name = name
        self.port = port
        self.rank = rank
        self.index = TweetIndex()
        self.lock = threading.Lock()
        self.nodes = []
        if rank != 'Primary':
            self.addNode(primaryAddress,primaryPort,'Primary')
        self.version = 0
        self.log = {}
        if test == 'PrintIndex':
            self.PRINTINDEX = True
        else:
            self.PRINTINDEX = False
        
    def getName(self):
        return self.name
        
    def getPort(self):
        return self.port
        
    def getRank(self):
        return self.rank
        
    def setRank(self,rank):
        self.lock.acquire()
        self.rank = rank
        self.lock.release()
        
    def setPrimary(self,port):
        self.lock.acquire()
        for node in self.nodes:
            if node.port == port:
                node.rank = 'Primary'
            else:
                node.rank = 'Secondary'
        self.lock.release()
        
    def getVersion(self):
        return self.version
        
    def dumpLog(self,version):
        output = []
        self.lock.acquire()
        for i in range(version+1,self.version+1):
            output.append((self.log[i],i))
        self.lock.release()
        return output
    
    def getPrimaryAddress(self):
        if self.rank == 'Primary':
            return (self.name,self.port)
        output = ('nowhere',0)
        self.lock.acquire()
        for node in self.nodes:
            if node.rank == 'Primary':
                output = (node.name,node.port)
        self.lock.release()
        return output

    def getSecondaryAddresses(self):
        secondaries = []
        self.lock.acquire()
        for node in self.nodes:
            if node.rank == 'Secondary':
                secondaries.append((node.name,node.port))
        self.lock.release()
        return secondaries
        
    def getHigherAddresses(self):
        higherPorts = []
        self.lock.acquire()
        for node in self.nodes:
            if node.port > self.port:
                higherPorts.append((node.name,node.port))
        self.lock.release()
        return higherPorts
        
    def getAllAddresses(self):
        output = []
        self.lock.acquire()
        for node in self.nodes:
            output.append((node.name,node.port))
        self.lock.release()
        return output
        
    def getAllNodes(self):
        self.lock.acquire()
        output = copy.deepcopy(self.nodes)
        self.lock.release()
        return output
        
    def storeTweet(self,tweet):
        self.lock.acquire()
        added = self.index.add(tweet)
        if added:
            self.version += 1
            self.log[self.version] = tweet
            if self.PRINTINDEX:
                print self.index.toString()
        self.lock.release()
        return added
        
    def addNode(self,name,port,rank):
        self.lock.acquire()
        self.nodes.append(TweetNode(name,port,rank,0))
        self.lock.release()
        
    def nodeExists(self,name,port):
        for node in self.nodes:
            if name == node.name and port == node.port:
                return True
        return False
        
    def portExists(self,port):
        for node in self.nodes:
            if node.port == port:
                return True
        return False
        
    def removeNode(self,port):
        self.lock.acquire()
        for i in range(0,len(self.nodes)):
            if self.nodes[i].port == port:
                self.nodes.pop(i)
                self.lock.release()
                return      
        self.lock.release()
        
    def resetStatus(self,port):
        self.lock.acquire()
        self.getNode(port).status = 0
        self.lock.release()
        
    def incrementNodeStatus(self,port):
        self.lock.acquire()
        if not self.portExists(port):
            return 0
        node = self.getNode(port)
        node.status += 1
        status = node.status
        self.lock.release()
        return status
        
    def toString(self):
        self.lock.acquire()
        output = "System:\nName: " + str(self.name) + "\nPort: " + str(self.port) + "\nRank:" + self.rank + "\nNODES:"
        for node in self.nodes:
            output += "\n" + node.toString()
        self.lock.release()
        return output
        
    #local helper
    def getNode(self,port):
        for node in self.nodes:
            if node.port == port:
                return node
        

class TweetNode:
    
    def __init__(self, name, port, rank, status):
        self.name = name
        self.port = port
        self.rank = rank
        self.status = status

    def toString(self):
        return "Name:" + str(self.name) + "Port:" + str(self.port) + " Rank:" + self.rank + " Status:" + str(self.status) 
        

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
            print "-------------TWEETINDEX----------------\nAdding " + tweet + " to tag: " + t
            if t in self.index:              
                self.index[t].append(tweet)
            else:
                self.index[t] = [tweet]   
        return len(tags) > 0
        
    def toString(self):
        output = "INDEX CONTENTS:\n"
        for key in self.index.keys():
            output += "#" + key + ":\n"
            for tweet in self.index[key]:
                output = output + tweet + "\n"
        return output
        

if __name__ == "__main__":
    primary = raw_input("Primary server? (Y/N):")
    name = raw_input("Please enter name:")
    port = raw_input("Please enter port number:")
    test = raw_input("Enter test string:")
    if primary == 'Y':
        rank = 'Primary'
        primaryAddress = ""
        primaryPort = 0
    else:
        rank = 'Secondary'
        primaryAddress = raw_input("Please enter primary address:")
        primaryPort = raw_input("Please enter primary port:")
    httpd = TweetServer((name,int(port)), TweetHandler, rank, primaryAddress, int(primaryPort), test)
    print time.asctime(), "Server Starts - %s:%s" % (name,port)
    print httpd.toString()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.shutdown()
    httpd.waitForShutdown()
    httpd.server_close()
    print time.asctime(), "Server Stops - %s:%s" % (name,port)