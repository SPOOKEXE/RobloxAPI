
# https://github.com/pozm/Synapse/wiki/Synapse-UI-Websocket

from websockets.sync.client import connect
from os import path
from json import loads as json_loads, dumps as json_dumps

BASE_SOCKET_ADDRESS = "ws://localhost:24892/"
DEFAULT_TIMEOUT_PERIOD = 5

class SynapseAPI:

	# enable the websocket api
	@staticmethod
	def EnableSynapseWebSocket(synapse_directory : str) -> bool:
		filepath = path.join(synapse_directory, "bin", "theme-wpf.json")
		if not path.exists(filepath):
			print("Could not find the theme-wpf.json file at ", filepath)
			return False

		data=None
		try:
			with open(filepath, "r") as file:
				data = json_loads(file.read())
		except:
			print("Could not read the theme-wpf.json file.")
			return False

		json_data=None
		try:
			json_data = json_loads( data )
		except:
			print("Could not load the theme-wpf.json json data.")
			return False

		try:
			json_data['Main']['WebSocket']['Enabled'] = True
		except:
			print("Could not edit the WebSocket Enabled property in the theme-wpf.json file.")

		try:
			with open(filepath, "w") as file:
				data = file.write(json_dumps(json_data, indent=4))
		except:
			print("Could not write to the theme-wpf.json file.")
			return False

		print("Restart Synapse to apply changes to the WebSocket API configuration.")
		return True

	# attach to roblox if it has not already
	@staticmethod
	def attach() -> bool:
		try:
			websocket = connect(BASE_SOCKET_ADDRESS + 'attach')
		except:
			print("Synapse's websocket is not currently available.")
			return False

		websocket.send("ATTACH") # ask synapse to attach

		success=False
		while not success:
			try:
				msg = websocket.recv(timeout=DEFAULT_TIMEOUT_PERIOD)
				if msg == "ALREADY_ATTACHED" or msg == "READY":
					success=True
			except TimeoutError:
				print("Synapse is not currently available.")
				break

		websocket.close()
		return success

	# execute code into roblox
	@staticmethod
	def execute(lua_code : str) -> bool:
		try:
			websocket = connect(BASE_SOCKET_ADDRESS + 'execute')
		except:
			print("Synapse's websocket is not currently available.")
			return False
		
		websocket.send(lua_code)

		success=False
		while not success:
			try:
				msg = websocket.recv(timeout=DEFAULT_TIMEOUT_PERIOD)
				if msg == "OK":
					success=True
			except TimeoutError:
				print("Synapse is not currently available.")
				break

		return success

def RunSynapseTest() -> bool:
	api = SynapseAPI()

	print("Attaching to Roblox.")
	success = api.attach() # make sure to attach
	if not success:
		print("Synapse could not attach to Roblox.")
		return False

	print("Attached to Roblox.")
	
	print("Synapse is attached and ready to execute.")
	# test the execute code
	success = api.execute("print('Synapse successfully executed!')")
	if not success:
		print("Synapse could not execute the given code.")
		return False
	print("Synapse has successfully executed.")

	print("Synapse has passed all checks.")
	return True

if __name__ == '__main__':
	RunSynapseTest()
