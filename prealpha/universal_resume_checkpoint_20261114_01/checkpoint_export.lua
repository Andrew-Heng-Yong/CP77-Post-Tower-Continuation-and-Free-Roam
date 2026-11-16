local checkpointExport, checkpointRetry = nil, 0
local function checkpointUpdate()
  if time<checkpointRetry then return end
  local ok,err=pcall(function()
    local s=system(channels[2].name)
    if not s then checkpointExport=nil;return end
    local epoch,id=s:Epoch(),s:ExecutionCheckpointId()
    if id=="" then checkpointExport=nil;return end
    if checkpointExport and checkpointExport.epoch==epoch and checkpointExport.id==id then return end
    assert(type(id)=="string" and #id==32 and id:match("^[0-9a-f]+$"),"Invalid execution checkpoint ID")
    local data=s:ExecutionCheckpointJSON()
    assert(type(data)=="string" and #data>0 and #data<=2097152,"Execution checkpoint size limit")
    local parsed=json.decode(data)
    assert(parsed.schema==1 and parsed.id==id and parsed.origin=="pre_native_cleanup" and
      (parsed.route==1 or parsed.route==2) and integer(parsed.ticket,1,2147483647) and
      integer(parsed.history_revision,1,2147483647) and parsed.history_catalogue==fp3,
      "Invalid execution checkpoint envelope")
    local function isCurrent()
      local current=system(channels[2].name)
      return current and current:Epoch()==epoch and current:MatchesExecutionCheckpoint(id,data)
    end
    if not isCurrent() then return end
    local path="checkpoint_execution_"..id..".json"
    local previous=read(path)
    if previous then
      assert(previous==data,"Execution checkpoint path contains different bytes")
    else
      local temp
      for _=1,1000 do
        counter=counter+1
        local candidate="checkpoint_execution_"..id.."_"..tostring(counter)..".tmp"
        if not read(candidate) then temp=candidate;break end
      end
      assert(temp,"No unused execution checkpoint temporary file")
      if not writeVerified(path,temp,data,isCurrent) then return end
    end
    if not isCurrent() then return end
    checkpointExport={epoch=epoch,id=id}
    print("[PTFR] Save-local execution checkpoint verified: "..path)
  end)
  if not ok then
    checkpointRetry=time+5
    print("[PTFR] Execution checkpoint export waiting: "..tostring(err))
  end
end

