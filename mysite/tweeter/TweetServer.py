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
import time

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
        print "\nGET REQUEST START:\n"
        print self.path
        print self.headers
        print "\nGET REQUEST END\n"
        self.send_response(200)
        self.send_header('Content-type','text/html')
        self.end_headers()
        self.wfile.write("This server works!")
        return   
        
    def do_POST(self):
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD':'POST',
                     'CONTENT_TYPE':self.headers['Content-Type'],
            })
        for field in form.keys():
            self.server.index.add(str(form.getvalue(str(field))))  
            if self.server.system.rank == 'Primary':
                self.server.system.lock.acquire()
                for node in self.server.system.nodes:
                    post = requests.post("http://localhost:" + str(node.port) + "/", data = {str(field): str(form.getvalue(str(field)))}, headers={'Connection':'close'})
                    print "POST Response:\n"
                    print post.text
                self.server.system.lock.release()

        temp = "the post works!"
        self.send_response(200)
        self.send_header('Content-type','text/html')
        self.send_header('Content-length',str(len(temp)))
        self.end_headers()
        self.wfile.write(temp)
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
            if t in self.index:
                print "-------------TWEETINDEX----------------\nAdding " + tweet + " to tag: " + t
                self.index[t].append(tweet)
            else:
                print "-------------TWEETINDEX----------------\nAdding " + tweet + " to tag: " + t
                self.index[t] = [tweet]   
                
class TweetSystem:
    
    def __init__(self, port, rank):
        self.running = True
        self.finished = False
        self.lock = threading.Lock()
        self.port = port
        self.rank = rank
        self.nodes = [TweetNode(7000, 'Primary', 0), TweetNode(7001, 'Secondary', 0), TweetNode(7002, 'Secondary', 0)]
        for i in range(0, len(self.nodes)):
            if self.nodes[i].port == self.port:
                self.nodes.pop(i)
                break
        thread.start_new_thread(self.run())
        
    def run(self):
        while True:
            time.sleep(30)
            self.lock.acquire()
            if not self.running:
                self.finished = True
                self.lock.release()
                return
            for i in range(0, len(self.nodes)):
                try:
                    r = requests.get("http://localhost:" + str(self.nodes[i].port) + "/", params={'clientport':str(self.port)}, headers={'Connection':'close'}, timeout=6.5)
                    print "Received heartbeat response from port " + str(self.nodes[i].port)
                except requests.exceptions.Timeout:
                    self.nodes[i].status += 1
                    print "NO HEARTBEAT RESPONSE FROM PORT " + str(self.nodes[i].port) + ", Status:" + str(self.nodes[i].status)
                    if self.nodes[i].status > 3:
                        print "NODE AT PORT " + str(self.nodes[i].port) + " HAS FAILED. REMOVING."
                        self.nodes.pop(i)
                except requests.exceptions.ConnectionError:
                    print "CONNECTION ERROR ON HEARTBEAT TO PORT " + str(self.nodes[i].port)
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
        self.status = 0

    def toString(self):
        return "Port:" + str(self.port) + " Rank:" + self.rank + " Status:" + str(self.status) 
    
if __name__ == "__main__":
    primary = raw_input("Primary server? (Y/N):")
    if primary == 'Y':
        TweetServer(7000,"localhost",'Primary')
    else:
        port = raw_input("Please enter port number:")
        TweetServer(int(port),"localhost",'Secondary')