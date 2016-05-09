# -*- coding: utf-8 -*-
"""
Created on Mon Mar 21 18:28:12 2016

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

class TweetServer:
    
    def __init__(self, port, name, rank):
        server_class = BaseHTTPServer.HTTPServer
        httpd = server_class((name,port), TweetHandler)
        httpd.index = TweetIndex()
        httpd.system = TweetSystem(port, rank)
        print httpd.system.toString()
        print time.asctime(), "Server Starts - %s:%s" % (name,port)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        httpd.server_close()
        httpd.system.lock.acquire()
        httpd.system.running = False
        httpd.system.lock.release()
        httpd.system.waitForShutdown()
        print time.asctime(), "Server Stops - %s:%s" % (name,port)
        
class TweetHandler(BaseHTTPServer.BaseHTTPRequestHandler):  
        
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type','text/html')
        self.end_headers()
        self.wfile.write("This server works!")
        self.wfile.close()
        clientPort = str(urlparse.parse_qs(urlparse.urlparse(self.path).query).get('clientPort', None)[0])
        clientRank = urlparse.parse_qs(urlparse.urlparse(self.path).query).get('clientRank', None)[0]
        election = int(urlparse.parse_qs(urlparse.urlparse(self.path).query).get('election', None)[0])
        self.server.system.lock.acquire()
        if election == -1:
            print "Received PRIMARY notification from port " + str(clientPort)
            self.server.system.setPrimary(int(clientPort))
            print "Current Nodes:"
            print self.server.system.toString()
            self.server.system.lock.release()
            return
        if election != 0:
            print "Received election notification from port " + str(clientPort)
            if not self.server.system.electing and self.server.system.rank != "Primary":
                thread.start_new_thread(self.server.system.election,(election,))
            else:
                print "Ignoring election notification"
                if self.server.system.electing:
                    print "Already in election process"
                else:
                    print "This server is a primary already"
                print self.server.system.toString()
            self.server.system.lock.release()
            return
        known = False
        for node in self.server.system.nodes:
            if str(node.port) == clientPort:
                known = True
                node.status = 0
        if not known:
            print "New server found at port " + str(clientPort)
            self.server.system.nodes.append(TweetNode(clientPort,clientRank,0))
        if self.server.system.rank == 'Primary' and clientRank == 'Secondary':
            clientVersion = int(urlparse.parse_qs(urlparse.urlparse(self.path).query).get('version', None)[0])
            if clientVersion < self.server.system.version:
                print "Secondary version at " + str(clientPort) + "is out of date, updating from " + str(clientVersion) + " to " + str(self.server.system.version)
                for i in range(clientVersion+1,self.server.system.version+1):
                    try:
                        requests.post("http://localhost:" + clientPort + "/", data = {'tweet': self.server.system.log[i],'version':i}, headers={'Connection':'close'})
                    except requests.exceptions.Timeout:
                        print "Timeout when posting to Secondary at port " + clientPort + ". Removing."
                        self.server.system.removeNode(clientPort)
                        break
                    except requests.exceptions.ConnectionError:
                        print "Connection error when posting to Secondary at port " + clientPort + ". Removing."
                        self.server.system.removeNode(clientPort)
                        break
        self.server.system.lock.release()
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
        tweet = str(form.getvalue('tweet'))
        self.server.system.lock.acquire()
        if self.server.system.rank == 'Primary':
            if self.server.index.add(tweet):
                self.server.system.version += 1
                self.server.system.log[self.server.system.version] = tweet
                for node in copy.deepcopy(self.server.system.nodes):
                    try:
                        requests.post("http://localhost:" + str(node.port) + "/", data = {'tweet':tweet, 'version':self.server.system.version}, headers={'Connection':'close'})
                    except requests.exceptions.Timeout:
                        print "Timeout when posting to Secondary at port " + str(node.port) + ". Removing."
                        self.server.system.removeNode(node.port)
                    except requests.exceptions.ConnectionError:
                        print "Connection error when posting to Secondary at port " + str(node.port) + ". Removing."
                        self.server.system.removeNode(node.port)
        else:
            tweetversion = int(form.getvalue('version'))
            while tweetversion > self.server.system.version + 1:
                time.sleep(10)
                try:
                    requests.get("http://localhost:" + str(self.server.system.getPrimary) + "/", params={'clientPort':str(self.server.system.port),'clientRank':str(self.server.system.rank),'version':str(self.server.system.version),'election':'0'}, headers={'Connection':'close'})
                except requests.exceptions.Timeout:
                    print "Timeout while trying to catch up to version " + str(self.server.system.version+1) + ". We're in trouble."
                except requests.exceptions.ConnectionError:
                    print "Connection error while trying to catch up to version " + str(self.server.system.version+1) + ". We're in trouble."
            if tweetversion > self.server.system.version:
                self.server.index.add(tweet)
                self.server.system.version += 1
        self.server.system.lock.release()
        return
    

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
                
class TweetSystem:
    
    def __init__(self, port, rank):
        self.version = 0
        self.log = {}
        self.running = True
        self.finished = False
        self.lock = threading.Lock()
        self.port = port
        self.rank = rank
        self.nodes = [TweetNode(7000, 'Primary', 0), TweetNode(7001, 'Secondary', 0), TweetNode(7002, 'Secondary', 0)]
        self.failedPrimaries = []
        self.removeNode(port)
        self.electing = False
        print "Starting run thread"
        thread.start_new_thread(self.run,())
        
    def run(self):
        while True:
            time.sleep(10)
            self.lock.acquire()
            if not self.electing:
                if not self.running:
                    self.finished = True
                    self.lock.release()
                    return
                doElection = 0
                for node in copy.deepcopy(self.nodes):
                    time.sleep(7)
                    try:
                        print "Sending heartbeat request to port " + str(node.port)
                        requests.get("http://localhost:" + str(node.port) + "/", params={'clientPort':str(self.port),'clientRank':str(self.rank),'version':str(self.version),'election':'0'}, headers={'Connection':'close'}, timeout=6.5)
                        print "Received heartbeat response from port " + str(node.port)
                        self.setStatus(node.port, 0)
                    except requests.exceptions.Timeout:
                        self.setStatus(node.port, self.getStatus(node.port)+1)
                        print "NO HEARTBEAT RESPONSE FROM PORT " + str(node.port) + ", Status:" + str(node.status+1)
                        if self.getStatus(node.port) > 3:
                            print "NODE AT PORT " + str(node.port) + " HAS FAILED. REMOVING."   
                            if node.rank == "Primary":
                                doElection = node.port                    
                            self.removeNode(node.port)
                    except requests.exceptions.ConnectionError:
                        self.setStatus(node.port, self.getStatus(node.port)+1)
                        print "CONNECTION ERROR ON HEARTBEAT TO PORT " + str(node.port) + ", Status:" + str(node.status+1)
                        if self.getStatus(node.port) > 3:
                            print "NODE AT PORT " + str(node.port) + " HAS FAILED. REMOVING."
                            if node.rank == "Primary":
                                doElection = node.port
                            self.removeNode(node.port)
                if doElection != 0 and not self.electing:
                    thread.start_new_thread(self.election,(doElection,))
            self.lock.release()
            
    def election(self, failedPrimary):
        print "Initiating election"
        self.lock.acquire()
        if failedPrimary in self.failedPrimaries:
            print "We did this election already."
            return
        self.failedPrimaries.append(failedPrimary)
        self.electing = True
        higherPorts = [];
        for node in copy.deepcopy(self.nodes):
            if node.port == failedPrimary:
                self.removeNode(failedPrimary)
        for node in self.nodes:
            if int(node.port) > int(self.port):
                print str(node.port) + " is larger than " + str(self.port)
                higherPorts.append(node.port)
        failures = 0
        for port in higherPorts:
            time.sleep(7)
            try:
                print "Trying to reach higher port at " + str(port)
                requests.get("http://localhost:" + str(port) + "/", params={'clientPort':str(self.port),'clientRank':str(self.rank),'version':str(self.version),'election':str(failedPrimary)}, headers={'Connection':'close'}, timeout=6.5)
                print "Received response from higher port at " + str(port)
            except requests.exceptions.Timeout:
                failures += 1
                print "Failed to reach higher port " + str(port) + " in election (Timeout). Removing."
                self.removeNode(port)
            except requests.exceptions.ConnectionError:
                failures += 1
                print "Failed to reach higher port " + str(port) + " in election (Connection Error). Removing."
                self.removeNode(port)
        if failures >= len(higherPorts):
            self.becomePrimary()
        self.electing = False
        self.lock.release()
        print "Finished election thread"
        
    def becomePrimary(self):
        print "Won the election, sending primary notifications. Port " + str(self.port) + " is the new primary."        
        self.rank = "Primary"
        print self.toString()
        for node in copy.deepcopy(self.nodes):
            try:
                print "Sending primary notification to " + str(node.port)
                requests.get("http://localhost:" + str(node.port) + "/", params={'clientPort':str(self.port),'clientRank':str(self.rank),'version':str(self.version),'election':'-1'}, headers={'Connection':'close'}, timeout=6.5)
                print "Received response to primary notification from " + str(node.port)
            except requests.exceptions.Timeout:
                print "Failed to reach port " + str(node.port) + " in becomePrimary (Timeout). Removing."
                self.removeNode(node.port)
            except requests.exceptions.ConnectionError:
                print "Failed to reach port " + str(node.port) + " in becomePrimary (Connection Error). Removing."
                self.removeNode(node.port)
            
    def waitForShutdown(self):
        while True:
            self.lock.acquire()
            if self.finished:                
                print "Run process finished. Shutting down..."
                self.lock.release()
                return
            self.lock.release()
            time.sleep(10)
            
    def removeNode(self, port):
        for i in range(0,len(self.nodes)):
            if self.nodes[i].port == port:
                self.nodes.pop(i)
                return
                
    def findPrimary(self):
        for i in range(0,len(self.nodes)):
            if self.nodes[i].rank == 'Primary':
                return self.nodes[i].port
                
    def setPrimary(self, port):
        for i in range(0,len(self.nodes)):
            if self.nodes[i].rank == 'Primary' and self.nodes[i].port != port:
                self.nodes[i].rank = 'Secondary'
            if self.nodes[i].port == port:
                self.nodes[i].rank = 'Primary'
        for i in range(0,len(self.failedPrimaries)):
            if self.failedPrimaries[i] == port:
               self.failedPrimaries.pop(i)
               i -= 1
               
    def getStatus(self, port):
        for i in range(0,len(self.nodes)):
            if self.nodes[i].port == port:
                return self.nodes[i].status
                
    def setStatus(self, port, status):
        for i in range(0,len(self.nodes)):
            if self.nodes[i].port == port:
                self.nodes[i].status = status
        
    def toString(self):
        output = "System:\nPort: " + str(self.port) + "\nRank:" + self.rank + "\nNODES:"
        for node in self.nodes:
            output += "\n" + node.toString()
        return output
        
class TweetNode:
    
    def __init__(self, port, rank, status):
        self.port = port
        self.rank = rank
        self.status = status

    def toString(self):
        return "Port:" + str(self.port) + " Rank:" + self.rank + " Status:" + str(self.status) 
    
if __name__ == "__main__":
    primary = raw_input("Primary server? (Y/N):")
    if primary == 'Y':
        TweetServer(7000,"localhost",'Primary')
    else:
        port = raw_input("Please enter port number:")
        TweetServer(int(port),"localhost",'Secondary')