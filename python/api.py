
import numpy
import pygame
import asyncio
import time

from os import path as os_path
from json import loads as json_loads, dumps as json_dumps
from websockets.sync.client import connect
from localhost import SetupLocalHost

from synapse import SynapseAPI

DEFAULT_TIMEOUT_PERIOD = 5
FILE_DIRECTORY = os_path.dirname(os_path.realpath(__file__))

RECENT_CONNECTION_RESPONSES = { } # request responses from roblox
RECENT_CONNECTION_REQUESTS = [ ] # requests going out to roblox

def SETUP_LUA_API_LOCALHOST() -> None:
	def handle_get(self, content_length, content_data) -> int:
		global RECENT_CONNECTION_REQUESTS
		print("GET", content_length, content_data)
		response_data=None
		if len(RECENT_CONNECTION_REQUESTS) == 0:
			response_data = "NO_REQUESTS"
		else:
			values = RECENT_CONNECTION_REQUESTS
			RECENT_CONNECTION_REQUESTS = [ ]
			response_data = json_dumps(values)
		return 200, response_data

	def handle_post(self, content_length, content_data) -> int:
		global RECENT_CONNECTION_RESPONSES
		print("POST", content_length, content_data)
		response_data = "Got POST Message"
		#RECENT_CONNECTION_RESPONSES[ content_data['id'] ] = content_data['data']
		return 200,response_data

	server = SetupLocalHost(port=8000, onGET=handle_get, onPOST=handle_post)
	server.start()

def EXECUTE_LUA_API() -> bool:
	print("Executing the Internal Roblox API WebSocket.")
	global FILE_DIRECTORY

	LUA_API_CODE = None
	LUA_API_FILEPATH = os_path.join(FILE_DIRECTORY, "resources/lua_api.lua")
	try:
		with open( LUA_API_FILEPATH, "r" ) as file:
			LUA_API_CODE = file.read()
	except:
		print("Could not read the Roblox API Code as the file was not found at: ", LUA_API_FILEPATH)
		return False

	print(len(LUA_API_CODE))
	print("Asking Synapse API to execute the code.")
	successful = SynapseAPI.execute(LUA_API_CODE)
	print(successful)
	if not successful:
		print("Could not execute Roblox API code needed for this module.")
		return False

	print("Successfully launched the Roblox Internal API")
	return True

# start the internal roblox lua api
SETUP_LUA_API_LOCALHOST()
EXECUTE_LUA_API()

class DataAPI:

	@staticmethod
	def _JobRequestClient(job : str) -> tuple[bool, dict]:
		global RECENT_CONNECTION_REQUESTS
		new_id = str(time.time_ns())
		RECENT_CONNECTION_REQUESTS.append( {"id" : new_id, "job" : job} )

		print("Appended Connection Request Data: ")
		print(json_dumps({"id" : new_id, "job" : job}, indent=4))
		startTime = time.time()
		response=None
		while time.time() - startTime < DEFAULT_TIMEOUT_PERIOD:
			response = RECENT_CONNECTION_RESPONSES.get( new_id )
			time.sleep(0.25)
		print("Response: ", response or "NO-RESPONSE")
		return (response != None), response

	@staticmethod
	def IsAPIAvailable() -> bool:
		message_sent, response = DataAPI._JobRequestClient("is_available")
		if not message_sent:
			return False
		response = json_loads(response)
		print(response)
		return response[0]

	@staticmethod
	def GetGameInfo() -> dict:
		pass

	@staticmethod
	def CanExecuteCodeInDevConsole() -> bool:
		pass

	@staticmethod
	def ExecuteCodeInDevConsole() -> None:
		pass

for _ in range(10):
	print( DataAPI.IsAPIAvailable() )
	time.sleep(2)
