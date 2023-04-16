print("Loading the Internal Roblox lua API")
if _G.HasLuaAPI and _G.LuaAPIDisconnect then
	warn("API has already loaded - disconnecting current.")
	_G.LuaAPIDisconnect()
end
_G.HasLuaAPI = true

print("Setting up Socket Connection.")

local PY_API_URL = "http://localhost:8000"
local HEADERS = { ['Content-Type'] = 'application/json' }

local HttpService = game:GetService('HttpService')

local JOB_TO_FUNC = {
	['is_available'] = function(json_data)
		return { true }
	end
}

local function SynRequest( URL, METHOD, BODY, HEADER )
	return syn.request({ Url = URL, Method = METHOD, BODY = BODY, HEADER = HEADER})
end

local function HandleOnMessage(bulkdata)
	print(HttpService:JSONEncode(bulkdata))
	local json_data = HttpService:JSONDecode(bulkdata['Body'])
	print(#json_data)
	for _, data in ipairs( json_data ) do
		local id = data['id']
		local job = data['job']

		print(id, job)

		local response_data = 'UNKNOWN_JOB'
		if JOB_TO_FUNC[ job ] then
			print('found job')
			response_data = JOB_TO_FUNC[ job ](data)
		end

		local response = HttpService:JSONEncode({id=id, job=job, data=response_data})
		print(response)
		task.defer(function()
			local server_response = SynRequest( PY_API_URL, "POST", response, HEADERS )
			print(HttpService:JSONEncode(server_response))
		end)
	end
end

_G.LuaAPIDisconnect = function()
	_G.LuaAPIDisconnect = nil
	warn("Closing the current Internal Lua API.")
end

task.spawn(function()
	while _G.LuaAPIDisconnect do
		print("Requesting Server - ", PY_API_URL, HttpService:JSONEncode(HEADERS))
		local next_requests = SynRequest( PY_API_URL, "GET", nil, nil )
		print(HttpService:JSONEncode(next_requests))
		if next_requests ~= "NO_REQUESTS" then
			HandleOnMessage(next_requests)
		end
		task.wait(1)
	end
end)

print("lua_api_started")
