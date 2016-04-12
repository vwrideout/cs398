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
        clientPort = str(urlparse.parse_qs(urlparse.urlparse(self.path).query).get('clientPort', None)[0])
        clientRank = urlparse.parse_qs(urlparse.urlparse(self.path).query).get('clientRank', None)[0]
        known = False
        self.server.system.lock.acquire()
        for node in self.server.system.nodes:
            if str(node.port) == clientPort:
                known = True
                node.status = 0
        if not known:
            print "New server found at port " + str(clientPort)
            self.server.system.nodes.append(TweetNode(clientPort,clientRank,0))
            newversion = int(urlparse.parse_qs(urlparse.urlparse(self.path).query).get('version', None)[0])
            if newversion < self.server.system.version and self.server.system.rank == 'Primary' and clientRank == 'Secondary':
                print "New secondary version is out of date, updating from " + str(newversion) + " to " + str(self.server.system.version)
                for i in range(newversion+1,self.server.system.version+1):
                    try:
                        requests.post("http://localhost:" + clientPort + "/", data = {'tweet': self.server.system.log[i]}, headers={'Connection':'close'})
                    except requests.exceptions.Timeout:
                        print "Timeout when posting to Secondary at port " + clientPort + ". Removing."
                        self.server.system.removeNode(clientPort)
                    except requests.exceptions.ConnectionError:
                        print "Connection error when posting to Secondary at port " + clientPort + ". Removing."
                        self.server.system.removeNode(clientPort)
        self.server.system.lock.release()
        return   
        
    def do_POST(self):       
        temp = "the post works!"
        self.send_response(200)
        self.send_header('Content-type','text/html')
        self.send_header('Content-length',str(len(temp)))
        self.end_headers()
        self.wfile.write(temp)
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD':'POST',
                     'CONTENT_TYPE':self.headers['Content-Type'],
            })
        for field in form.keys():
            if(self.server.index.add(str(form.getvalue(str(field))))):                
                self.server.system.lock.acquire()
                self.server.system.version += 1
                if self.server.system.rank == 'Primary':     
                    self.server.system.log[self.server.system.version] = str(form.getvalue(str(field)))
                    for node in self.server.system.nodes:
                        if node.rank == "Secondary":
                            try:
                                requests.post("http://localhost:" + str(node.port) + "/", data = {str(field): str(form.getvalue(str(field)))}, headers={'Connection':'close'})
                            except requests.exceptions.Timeout:
                                print "Timeout when posting to Secondary at port " + str(node.port) + ". Removing."
                                self.server.system.removeNode(node.port)
                            except requests.exceptions.ConnectionError:
                                print "Connection error when posting to Secondary at port " + str(node.port) + ". Removing."
                                self.server.system.removeNode(node.port)
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
        self.removeNode(port)
        print "Starting run thread"
        thread.start_new_thread(self.run,())
        
    def run(self):
        while True:
            time.sleep(30)
            self.lock.acquire()
            if not self.running:
                self.finished = True
                self.lock.release()
                return
            for node in self.nodes:
                try:
                    requests.get("http://localhost:" + str(node.port) + "/", params={'clientPort':str(self.port),'clientRank':str(self.rank),'version':str(self.version)}, headers={'Connection':'close'}, timeout=6.5)
                    print "Received heartbeat response from port " + str(node.port)
                    node.status = 0
                except requests.exceptions.Timeout:
                    node.status += 1
                    print "NO HEARTBEAT RESPONSE FROM PORT " + str(node.port) + ", Status:" + str(node.status)
                    if node.status > 3:
                        print "NODE AT PORT " + str(node.port) + " HAS FAILED. REMOVING."
                        self.removeNode(node.port)
                except requests.exceptions.ConnectionError:
                    node.status += 1
                    print "CONNECTION ERROR ON HEARTBEAT TO PORT " + str(node.port) + ", Status:" + str(node.status)
                    if node.status > 3:
                        print "NODE AT PORT " + str(node.port) + " HAS FAILED. REMOVING."
                        self.removeNode(node.port)
            self.lock.release()
            
    def waitForShutdown(self):
        while True:
            self.lock.acquire()
            if self.finished:                
                print "Run process finished. Shutting down..."
                self.lock.release()
                return
            self.lock.release()
            time.sleep(5)
            
    def removeNode(self, port):
        for i in range(0,len(self.nodes)):
            if self.nodes[i].port == port:
                self.nodes.pop(i)
                return
        
    def toString(self):
        self.lock.acquire()
        output = "System:\nPort: " + str(self.port) + "\nRank:" + self.rank + "\nNODES:"
        for node in self.nodes:
            output += "\n" + node.toString()
        self.lock.release()
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