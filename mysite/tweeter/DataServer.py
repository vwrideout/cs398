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
        
        """I believe this @property tag will allow this nested class to access the TweetIndex in DataServer"""
        @property
        def do_POST(self):
            """This code is intended to parse the data sent from the requests.post in line 14 of views,
                omitted because it does not run with it included.
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={'REQUEST_METHOD':'POST',
                         'CONTENT_TYPE':self.headers['Content-Type'],
                })
            for field in form.keys():
                print field
                print form[field]
                """
                
            print "\nPOST REQUEST START:\n"
            """
            print self.path
            requestheaders = self.headers
            print requestheaders
            contentlength = requestheaders.getheaders('content-length')
            length = int(contentlength[0]) if contentlength else 0
            print requestheaders
            print self.rfile.read(length)
            """
            print "\nPOST REQUEST END\n"
            self.send_response(200)
            self.send_header('Content-type','text/html')
            self.end_headers()
            self.wfile.write("The post works!")
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

                
        
        
    