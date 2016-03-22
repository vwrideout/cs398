# -*- coding: utf-8 -*-
"""
Created on Sat Mar 05 14:53:57 2016

@author: Vincent Rideout
"""
import BaseHTTPServer
import time
import cgi


class DataServer:
    
    def __init__(self,port,name):
        self.index = TweetIndex()
        self.name = name
        self.port = port
        
    def run(self):
        server_class = BaseHTTPServer.HTTPServer
        httpd = server_class((self.name,self.port), self.DataHandler)
        httpd.message = "Hello, world!"
        print time.asctime(), "Server Starts - %s:%s" % (self.name,self.port)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        httpd.server_close()
        print time.asctime(), "Server Stops - %s:%s" % (self.name,self.port)
        
    class DataHandler(BaseHTTPServer.BaseHTTPRequestHandler):
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
                print field
                print form[field]
                
                
            print "\nPOST REQUEST START:\n"
            print self.server.message
        
            print self.path
            requestheaders = self.headers
            print requestheaders
            """
            contentlength = requestheaders.getheaders('content-length')
            length = int(contentlength[0]) if contentlength else 0
            print requestheaders
            print self.rfile.read(length)
            """
            print "\nPOST REQUEST END\n"
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
                self.index[t].append(tweet)
            else:
                self.index[t] = [tweet]   
            
if __name__ == "__main__":
    DS = DataServer(7000,"localhost")
    DS.run()          

                
        
        
    