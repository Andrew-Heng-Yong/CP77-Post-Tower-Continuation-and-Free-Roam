do
  local ok, err = pcall(function()
    local p = Game.GetPlayer()
    if not p or not p:IsAttached() then print("[JF01-W] LOAD_SAVE_FIRST") return end
    local w = Game.GetWorldStateSystem()
    if not w or not w:IsReady() then print("[JF01-W] WORLD_NOT_READY") return end
    print("[JF01-W] BEGIN")
    for _, r in ipairs({"#sts_ep1_03_gunfight_crowd_com", "#sts_ep1_03_pre_gunfight_com"}) do
      local good, val = pcall(function()
        local c = w:GetCommunity(Game.CreateNodeRef(r))
        if not c then return "UNRESOLVED" end
        local entries = c:GetEntries()
        local count, active = 0, 0
        for i, e in ipairs(entries) do
          if i > 64 then return "TRUNCATED" end
          count = count + 1
          if e:IsActive() then active = active + 1 end
        end
        return "entries=" .. count .. " active=" .. active
      end)
      print("[JF01-W] " .. r .. " " .. (good and val or ("ERROR:" .. tostring(val))))
    end
    local good, val = pcall(function()
      local s = w:GetPopulationSpawner(Game.CreateNodeRef("#sts_ep1_03_gunfight_broken_car"))
      if not s then return "UNRESOLVED" end
      return "initialized=" .. tostring(s:IsInitialized()) .. " active=" .. tostring(s:IsActive())
    end)
    print("[JF01-W] broken_car " .. (good and val or ("ERROR:" .. tostring(val))))
    print("[JF01-W] END")
  end)
  if not ok then print("[JF01-W] ERROR:" .. tostring(err)) end
end
