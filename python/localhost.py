from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from base64 import decode as bs4decode
from typing import Union

MAX_DATA_LENGTH = 1e5
HOST_IP = "localhost"

def _str_to_byte(str) -> bytes:
	return bytes(str, "utf-8")

def new_thread_for_function(function, args : tuple) -> Thread:
	print(f"Handling incoming data asynchronously with {len(list(args))} arguments")
	thread = Thread(target=function, args=args)
	thread.start()
	return thread

class ThreadedServerResponder(BaseHTTPRequestHandler):
	certificateLock = None
	onGET = None
	onGETAsync = None
	onPOST = None
	onPOSTAsync = None
	onServerExit = None

	# Write strings to the request wfile (output to client)
	def _write_wfile(self, message : str) -> None:
		self.wfile.write( _str_to_byte(message) )

	# Send the status-code and content-type back to the connectee of the server.
	def _send_response_info(self, status_code=200) -> None:
		# send response status code
		self.send_response(status_code)
		# send header information
		self.send_header("Content-Type", "application/json")
		# end headers and close response
		self.end_headers()
	
	# If the header contains the access ceritficate, return the base64 decode of it, othewise 'None'.
	def _get_certificate_from_header(self) -> Union[str, None]:
		try:
			# access the certificate in the header
			header_cert = self.headers['certificate']
			# try base64 decode it
			return bs4decode(header_cert)
		except:
			# not in the header or cannot bs64decode
			pass
		# couldnt find or decode the certificate
		return None
	
	def _get_request_data(self) -> Union[str, int]:
		# try get the content length from the headers
		content_length = None
		try:
			content_length = int(self.headers['Content-Length'])
		except:
			pass
		# if there is no content-length value, ignore the request
		if content_length == None:
			return None, -1,
		# if the content-length is larger than the max data length, ignore the request.
		if content_length > MAX_DATA_LENGTH:
			return None, content_length
		# get the request data if the content length is larger than 0
		data = None
		if content_length > 0:
			post_data = self.rfile.read(content_length)
			data = post_data.decode('utf-8')
		# return the data and content length in a tuple
		return data, content_length

	def _get_request_essentials(self) -> bool:
		# try get the access certificate from the request headers
		certificate = self._get_certificate_from_header()
		# If the server is certificate locked, and the connectee did not pass the correct certificate, report it is incorrect.
		if (self.certificateLock != None) and (self.certificateLock != certificate):
			self._send_response_info(status_code=401) # 401 = not authorized
			self._write_wfile("{'message': 'Not Authorized!'}")
			return False, None, -1
		# get data from the post request
		data, content_length = self._get_request_data()
		# if the content-length is larger than the max data length, ignore the request.
		if content_length > MAX_DATA_LENGTH:
			self._send_response_info()
			message = f"Data exceeds maximum of {MAX_DATA_LENGTH} length. Got {content_length} length."
			self._write_wfile("{'message' : " + message + "}")
			return False, None, -1
		return True, data, content_length

	def do_REQUEST(self, callback, callback_async) -> None:
		valid_request, content, content_length = self._get_request_essentials()
		# print(valid_request, content_length)
		if not valid_request:
			return

		status_code = 200
		if callback != None:
			status_code, response_data = callback( content_length, content )
		else:
			self._write_wfile("{'message': 'Recieved data of length" + str(content_length) + "'}")

		if callback_async != None:
			Thread(target=callback_async, args=(content_length, content)).start()
		self._send_response_info(status_code=status_code)
		if response_data != None:
			print(response_data)
			self._write_wfile(response_data)

	def do_GET(self):
		self.do_REQUEST(self.onGET, self.onGETAsync)

	def do_POST(self):
		self.do_REQUEST(self.onPOST, self.onPOSTAsync)

	# prevent console logs
	def log_message(self, format, *args):
		return

class ServerThreadWrapper:
	webserver : HTTPServer = None

	server_thread : Thread = None
	shutdown_callback_thread : Thread = None

	has_ran = False

	def shutdown(self) -> None:
		self.webserver.shutdown()

	def join_thread_callback(self, thread : Thread, callback):
		thread.join()
		callback(self)

	def thread_ended_callback(self, main_thread : Thread, callback) -> Thread:
		callback_thread = Thread(target=self.join_thread_callback, args=(main_thread, callback))
		callback_thread.start()
		return callback_thread

	def start(self, webserver=None, server_closed_callback=None):
		self.webserver = webserver
		if webserver == None:
			return

		server_thread : Thread = Thread(target=webserver.serve_forever)
		self.server_thread = server_thread
		
		print(f"Server Starting @ {self.webserver.server_address}")
		server_thread.start()

		if server_closed_callback != None:
			self.shutdown_callback_thread = self.thread_ended_callback(server_thread, server_closed_callback)

	def __init__(self, webserver=None, server_closed_callback=None):
		self.start(webserver=webserver, server_closed_callback=server_closed_callback)

def SetupLocalHost(port=500, onGET=None, onPOST=None, onGETAsync=None, onPOSTAsync=None, onServerExit=None) -> ServerThreadWrapper:
	customThreadedResponder = ThreadedServerResponder
	customThreadedResponder.webserver = None
	customThreadedResponder.onGET = onGET
	customThreadedResponder.onGETAsync = onGETAsync
	customThreadedResponder.onPOST = onPOST
	customThreadedResponder.onPOSTAsync = onPOSTAsync
	customThreadedResponder.onServerExit = onServerExit

	webServer = HTTPServer((HOST_IP, port), customThreadedResponder)

	def ThreadExitCallback(self):
		print("Server Closed")
		nonlocal webServer
		if webServer.RequestHandlerClass.onServerExit != None:
			webServer.RequestHandlerClass.onServerExit()
		webServer.server_close()

	return ServerThreadWrapper(webserver=webServer, server_closed_callback=ThreadExitCallback)
