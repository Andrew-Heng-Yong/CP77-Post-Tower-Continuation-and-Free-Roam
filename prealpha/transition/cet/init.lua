-- One read-only console surface. Restoration is coordinated by REDscript PA2.
local api = {}
local function call(name, method, ...)
  local args, count = {...}, select("#", ...)
  local ok, result = pcall(function()
    if not Game or type(Game.GetScriptableSystemsContainer) ~= "function" then
      return "Load a save first; game systems unavailable."
    end
    local c = Game.GetScriptableSystemsContainer()
    local s = c and c:Get(name)
    if not s then return "Load a save first; PA2 system unavailable: " .. name end
    local fn = s[method]
    if type(fn) ~= "function" then return "PA2 diagnostic method unavailable: " .. name .. "." .. method end
    return fn(s, unpack(args, 1, count))
  end)
  if not ok then return "PA2 diagnostic unavailable: " .. tostring(result) end
  return result
end
function api.Status()
  return call("PTFR.ActivityStateR3.PreAlphaEntry", "Status")
end
function api.Arrival()
  return call("PTFR.ActivityStateR3.PreAlphaArrivalPA1", "Status")
end
function api.Gigs()
  return call("PTFR.ActivityStateR3.NativeGigsU9", "InspectAll")
end
function api.Gig(id)
  if type(id) ~= "string" or id == "" then return "Pass a gig ID, for example Gig(\"sts_hey_rey_06\")." end
  return call("PTFR.ActivityStateR3.NativeGigsU9", "Inspect", id)
end
function api.Entry()
  return call("PTFR.ActivityStateR3.PreAlphaEntry", "InspectAll")
end
function api.Phone()
  return call("PTFR.ActivityStateR3.GigPhoneU9", "Inspect")
end
function api.Profile()
  return call("PTFR.RestrictionsR3.ProfilePolicy", "GetStatus")
end
-- Read-only, bounded transition trace in PTFR_PreAlpha.log. No gameplay writes.
local clock, sample, traceStart, rows, previous = 0, 0, nil, 0, nil
registerForEvent("onUpdate", function(dt)
  clock = clock + dt
  if clock - sample < 1 then return end
  sample = clock
  local ok, active = pcall(function()
    local q = Game.GetQuestsSystem()
    return q and q:GetFactStr("PTFRPA2_Started") == 1
  end)
  if not ok or not active then
    traceStart, rows, previous = nil, 0, nil
    return
  end
  if not traceStart then traceStart = clock end
  if rows >= 180 or clock - traceStart > 180 then return end
  local state = api.Arrival() .. " | " .. api.Status()
  if state ~= previous or rows % 5 == 0 then
    print("[PA2 transition] " .. state)
  end
  previous, rows = state, rows + 1
end)
return api
