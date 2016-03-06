# Vincent Rideout CS 398

A project using Python and Django to experiment with Distributed Systems

#Error messages from web server:

[05/Mar/2016 22:12:47] "GET /favicon.ico HTTP/1.1" 404 2045
Internal Server Error: /tweeter/
Traceback (most recent call last):
  File "C:\Users\Vincent\Anaconda\lib\site-packages\django\core\handlers\base.py
", line 149, in get_response
    response = self.process_exception_by_middleware(e, request)
  File "C:\Users\Vincent\Anaconda\lib\site-packages\django\core\handlers\base.py
", line 147, in get_response
    response = wrapped_callback(request, *callback_args, **callback_kwargs)
  File "C:\Users\Vincent\Documents\GitHub\cs398\mysite\tweeter\views.py", line 1
4, in index
    z = requests.post('http://localhost:7000/', data = {'tweet':form.cleaned_dat
a})
  File "C:\Users\Vincent\Anaconda\lib\site-packages\requests\api.py", line 109,
in post
    return request('post', url, data=data, json=json, **kwargs)
  File "C:\Users\Vincent\Anaconda\lib\site-packages\requests\api.py", line 50, i
n request
    response = session.request(method=method, url=url, **kwargs)
  File "C:\Users\Vincent\Anaconda\lib\site-packages\requests\sessions.py", line
465, in request
    resp = self.send(prep, **send_kwargs)
  File "C:\Users\Vincent\Anaconda\lib\site-packages\requests\sessions.py", line
573, in send
    r = adapter.send(request, **kwargs)
  File "C:\Users\Vincent\Anaconda\lib\site-packages\requests\adapters.py", line
415, in send
    raise ConnectionError(err, request=request)
ConnectionError: ('Connection aborted.', error(10054, 'An existing connection wa
s forcibly closed by the remote host'))
[05/Mar/2016 22:15:32] "POST /tweeter/ HTTP/1.1" 500 88218
Traceback (most recent call last):
  File "C:\Users\Vincent\Anaconda\lib\wsgiref\handlers.py", line 86, in run
    self.finish_response()
  File "C:\Users\Vincent\Anaconda\lib\wsgiref\handlers.py", line 128, in finish_
response
    self.write(data)
  File "C:\Users\Vincent\Anaconda\lib\wsgiref\handlers.py", line 212, in write
    self.send_headers()
  File "C:\Users\Vincent\Anaconda\lib\wsgiref\handlers.py", line 270, in send_he
aders
    self.send_preamble()
  File "C:\Users\Vincent\Anaconda\lib\wsgiref\handlers.py", line 194, in send_pr
eamble
    'Date: %s\r\n' % format_date_time(time.time())
  File "C:\Users\Vincent\Anaconda\lib\socket.py", line 328, in write
    self.flush()
  File "C:\Users\Vincent\Anaconda\lib\socket.py", line 307, in flush
    self._sock.sendall(view[write_offset:write_offset+buffer_size])
error: [Errno 10053] An established connection was aborted by the software in yo
ur host machine
[05/Mar/2016 22:15:32] "POST /tweeter/ HTTP/1.1" 500 59
----------------------------------------
Exception happened during processing of request from ('127.0.0.1', 49478)
Traceback (most recent call last):
  File "C:\Users\Vincent\Anaconda\lib\SocketServer.py", line 599, in process_req
uest_thread
    self.finish_request(request, client_address)
  File "C:\Users\Vincent\Anaconda\lib\SocketServer.py", line 334, in finish_requ
est
    self.RequestHandlerClass(request, client_address, self)
  File "C:\Users\Vincent\Anaconda\lib\site-packages\django\core\servers\basehttp
.py", line 99, in __init__
    super(WSGIRequestHandler, self).__init__(*args, **kwargs)
  File "C:\Users\Vincent\Anaconda\lib\SocketServer.py", line 657, in __init__
    self.finish()
  File "C:\Users\Vincent\Anaconda\lib\SocketServer.py", line 716, in finish
    self.wfile.close()
  File "C:\Users\Vincent\Anaconda\lib\socket.py", line 283, in close
    self.flush()
  File "C:\Users\Vincent\Anaconda\lib\socket.py", line 307, in flush
    self._sock.sendall(view[write_offset:write_offset+buffer_size])
error: [Errno 10053] An established connection was aborted by the software in yo
ur host machine

#Error messages from data server:

[05/Mar/2016 22:12:47] "GET /favicon.ico HTTP/1.1" 404 2045
Internal Server Error: /tweeter/
Traceback (most recent call last):
  File "C:\Users\Vincent\Anaconda\lib\site-packages\django\core\handlers\base.py
", line 149, in get_response
    response = self.process_exception_by_middleware(e, request)
  File "C:\Users\Vincent\Anaconda\lib\site-packages\django\core\handlers\base.py
", line 147, in get_response
    response = wrapped_callback(request, *callback_args, **callback_kwargs)
  File "C:\Users\Vincent\Documents\GitHub\cs398\mysite\tweeter\views.py", line 1
4, in index
    z = requests.post('http://localhost:7000/', data = {'tweet':form.cleaned_dat
a})
  File "C:\Users\Vincent\Anaconda\lib\site-packages\requests\api.py", line 109,
in post
    return request('post', url, data=data, json=json, **kwargs)
  File "C:\Users\Vincent\Anaconda\lib\site-packages\requests\api.py", line 50, i
n request
    response = session.request(method=method, url=url, **kwargs)
  File "C:\Users\Vincent\Anaconda\lib\site-packages\requests\sessions.py", line
465, in request
    resp = self.send(prep, **send_kwargs)
  File "C:\Users\Vincent\Anaconda\lib\site-packages\requests\sessions.py", line
573, in send
    r = adapter.send(request, **kwargs)
  File "C:\Users\Vincent\Anaconda\lib\site-packages\requests\adapters.py", line
415, in send
    raise ConnectionError(err, request=request)
ConnectionError: ('Connection aborted.', error(10054, 'An existing connection wa
s forcibly closed by the remote host'))
[05/Mar/2016 22:15:32] "POST /tweeter/ HTTP/1.1" 500 88218
Traceback (most recent call last):
  File "C:\Users\Vincent\Anaconda\lib\wsgiref\handlers.py", line 86, in run
    self.finish_response()
  File "C:\Users\Vincent\Anaconda\lib\wsgiref\handlers.py", line 128, in finish_
response
    self.write(data)
  File "C:\Users\Vincent\Anaconda\lib\wsgiref\handlers.py", line 212, in write
    self.send_headers()
  File "C:\Users\Vincent\Anaconda\lib\wsgiref\handlers.py", line 270, in send_he
aders
    self.send_preamble()
  File "C:\Users\Vincent\Anaconda\lib\wsgiref\handlers.py", line 194, in send_pr
eamble
    'Date: %s\r\n' % format_date_time(time.time())
  File "C:\Users\Vincent\Anaconda\lib\socket.py", line 328, in write
    self.flush()
  File "C:\Users\Vincent\Anaconda\lib\socket.py", line 307, in flush
    self._sock.sendall(view[write_offset:write_offset+buffer_size])
error: [Errno 10053] An established connection was aborted by the software in yo
ur host machine
[05/Mar/2016 22:15:32] "POST /tweeter/ HTTP/1.1" 500 59
----------------------------------------
Exception happened during processing of request from ('127.0.0.1', 49478)
Traceback (most recent call last):
  File "C:\Users\Vincent\Anaconda\lib\SocketServer.py", line 599, in process_req
uest_thread
    self.finish_request(request, client_address)
  File "C:\Users\Vincent\Anaconda\lib\SocketServer.py", line 334, in finish_requ
est
    self.RequestHandlerClass(request, client_address, self)
  File "C:\Users\Vincent\Anaconda\lib\site-packages\django\core\servers\basehttp
.py", line 99, in __init__
    super(WSGIRequestHandler, self).__init__(*args, **kwargs)
  File "C:\Users\Vincent\Anaconda\lib\SocketServer.py", line 657, in __init__
    self.finish()
  File "C:\Users\Vincent\Anaconda\lib\SocketServer.py", line 716, in finish
    self.wfile.close()
  File "C:\Users\Vincent\Anaconda\lib\socket.py", line 283, in close
    self.flush()
  File "C:\Users\Vincent\Anaconda\lib\socket.py", line 307, in flush
    self._sock.sendall(view[write_offset:write_offset+buffer_size])
error: [Errno 10053] An established connection was aborted by the software in yo
ur host machine