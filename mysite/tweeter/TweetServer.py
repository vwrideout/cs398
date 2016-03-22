# -*- coding: utf-8 -*-
"""
Created on Mon Mar 21 18:28:12 2016

@author: Vincent Rideout
"""
import BaseHTTPServer
import time
import cgi
import requests

class TweetServer:
    
    def __init__(self, port, name, primary):
        server_class = BaseHTTPServer.HTTPServer
        httpd = server_class((name,port), TweetHandler)
        httpd.index = TweetIndex()
        httpd.primary = primary
        httpd.primaryAddress = 7000
        httpd.secondaryAddresses = [7001,7002]
        print time.asctime(), "Server Starts - %s:%s" % (name,port)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        httpd.server_close()
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
            if self.server.primary:
                for address in self.server.secondaryAddresses:
                    post = requests.post("http://localhost:" + str(address) + "/", data = {str(field): str(form.getvalue(str(field)))}, headers={'Connection':'close'})
                    print "POST Response:\n"
                    print post.text

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
                
if __name__ == "__main__":
    primary = raw_input("Primary server? (Y/N):")
    if primary == 'Y':
        TweetServer(7000,"localhost",True)
    else:
        port = raw_input("Please enter port number:")
        TweetServer(int(port),"localhost",False)