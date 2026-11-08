# Ronald future-news fixture qualification

Ronald enrollment/reload are closed. Candidate: **The Man Who Killed Jason Foreman** (`sts_ep1_03`). Use current working ManualSave-25; remain in ordinary gameplay and do not start the gig for this check.

```lua
do
  local s = Game.GetScriptableSystemsContainer():Get("PTFR.ActivityStateR3.NativeGigsU9")
  if s and IsDefined(s) then
    print(s:Inspect("sts_ep1_03"))
  else
    print("U9 diagnostic system unavailable")
  end
  local q = Game.GetQuestsSystem()
  print("Ronald armed = " .. tostring(q:GetFactStr("PTFRQR7_RonaldNews_Armed_sts_ep1_03")))
  print("Ronald sent = " .. tostring(q:GetFactStr("q302_msg_ronald_sts_ep1_03")))
end
```

Return the printed status. This reads existing source-defined diagnostics and facts. It does not call Start, request a controller or set a fact. These statuses do not enumerate actual executing owners. Source method/readiness prerequisites must be reviewed before any later manual test. Do not replay completed/failed jobs or reset history.
