do
  local p = Game.GetPlayer()
  if not p or not p:IsAttached() then print("[JF01-F] LOAD_SAVE_FIRST") return end
  print("[JF01-F] BEGIN")
  local q = Game.GetQuestsSystem()
  for _, n in ipairs({"sts_ep1_03_start_community", "sa_ep1_114_toggledoff_force", "sa_ep1_114_toggledoff", "sa_ep1_courier_allow_unrestricted_cleanup", "sa_ep1_courier_spot_force_toggled_off", "PTFRU9_sts_ep1_03_ParentEntered", "PTFRU9_sts_ep1_03_Started", "q307_ep1_killed"}) do
    local ok, v = pcall(function() return q:GetFactStr(n) end)
    print("[JF01-F] " .. n .. "=" .. (ok and tostring(v) or ("ERROR:" .. tostring(v))))
  end
  print("[JF01-F] END")
end
