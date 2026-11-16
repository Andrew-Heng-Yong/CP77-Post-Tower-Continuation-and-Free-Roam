-- Global newest valid pre-ending capture, explicitly requested by the user.
-- Existing exports are immutable; load JSON as data, never executable Lua.
local latest, latestCounter, latestRetry = nil, 0, 0
local fp1,fp3="__FP1__","__FP3__"
local count3=__COUNT3__
local function integer(v,min,max)
  return type(v)=="number" and v==math.floor(v) and v>=min and v<=max
end
local function equal(a,b)
  if type(a)~=type(b) then return false end
  if type(a)~="table" then return a==b end
  for k,v in pairs(a) do if not equal(v,b[k]) then return false end end
  for k in pairs(b) do if a[k]==nil then return false end end
  return true
end
local function listSnapshots(channel)
  local result={}
  for _,entry in pairs(dir(".")) do
    local name=entry.name
    if type(name)=="string" then
      local stamp,rev,serial=name:match("^snapshot_hs"..channel.."_(%d%d%d%d%d%d%d%dT%d%d%d%d%d%dZ)_(%d+)_(%d+)%.json$")
      rev,serial=tonumber(rev),tonumber(serial)
      if stamp and integer(rev,1,2147483647) and integer(serial,1,2147483647) then
        result[#result+1]={name=name,stamp=stamp,revision=rev,serial=serial,
          token=name:sub(#("snapshot_hs"..channel.."_")+1,-6)}
      end
    end
  end
  table.sort(result,function(a,b)
    if a.stamp~=b.stamp then return a.stamp>b.stamp end
    if a.serial~=b.serial then return a.serial>b.serial end
    return a.revision>b.revision
  end)
  return result
end
local function basic(raw,entry,channel)
  assert(type(raw)=="string","Snapshot disappeared")
  local d=json.decode(raw)
  assert(type(d)=="table" and d.schema==channel and d.revision==entry.revision and
    integer(d.revision,1,2147483647) and type(d.rows)=="table","Invalid snapshot header")
  if channel==1 then
    assert(d.catalogue==fp1 and d.origin=="pre_ending" and #d.rows==158,"Not a complete pre-ending HS1 capture")
  else
    assert(d.catalogue==fp3 and d.origin=="pre_native_cleanup" and #d.rows==count3 and
      integer(d.ticket,1,2147483647) and (d.route==1 or d.route==2),"Not a complete pre-cleanup HS3 capture")
  end
  return d
end
local function numericArray(a,n,min,max)
  assert(type(a)=="table" and #a==n,"Snapshot array length")
  for i=1,n do assert(integer(a[i],min,max),"Snapshot numeric field") end
  for k in pairs(a) do assert(integer(k,1,n),"Snapshot array key") end
end
local function validateRow(s,row,channel,index)
  assert(type(row)=="table" and type(row.stable)=="boolean","Snapshot row/stability")
  local expected=json.decode(s:DefinitionHS4(channel,index))
  assert(equal(row.definition,expected),"Snapshot definition mismatch")
  if channel==1 then
    local n,f=#expected.journals,#expected.fact_names
    numericArray(row.states,n,-1,4);numericArray(row.counters,n,-1,2147483647)
    numericArray(row.optional,n,-1,1);numericArray(row.tracked,n,-1,1)
    numericArray(row.facts,f,-2147483648,2147483647)
    assert(type(row.legacy_pre_ending_certificate)=="boolean","Snapshot certificate type")
  elseif expected.kind=="journal" then
    assert(integer(row.state,-1,4) and integer(row.counter,-1,2147483647) and
      integer(row.optional,-1,1) and integer(row.tracked,-1,1),"Journal field bounds")
  else
    assert(integer(row.value,expected.kind=="item_quantity" and -1 or -2147483648,2147483647),"Value field bounds")
  end
end
local function compatible(h1,h3)
  local journals,facts={},{}
  for _,r in ipairs(h3.rows) do
    local d=r.definition
    if d.kind=="journal" then journals[d.path.."\0"..d.class]=r
    elseif d.kind=="fact" then facts[d.name]=r end
  end
  for _,r in ipairs(h1.rows) do
    for i,d in ipairs(r.definition.journals) do
      local q=journals[d[1].."\0"..d[2]];assert(q,"Missing extended journal")
      if q.stable then
        assert(r.states[i]==q.state and r.counters[i]==q.counter and r.optional[i]==q.optional and
          r.tracked[i]==q.tracked,"Different captures: journal")
      end
    end
    for i,name in ipairs(r.definition.fact_names) do
      local q=facts[name];assert(q,"Missing extended fact")
      if q.stable then assert(r.facts[i]==q.value,"Different captures: fact") end
    end
  end
end
local function connected(s,w)
  return s and s:Epoch()==w.epoch and s:ClientLeaseHS4()==w.lease
end
local function nextExtended(w)
  w.i3=w.i3+1;w.doc3=nil;w.doc1=nil;w.phase="select3";w.cursor=0;w.i1=0
end
local function nextLegacy(w)
  w.i1=w.i1+1;w.doc1=nil;w.phase="select1";w.cursor=0
end
local function packet(w,channel,start,n)
  local data={}
  local function add(v) data[#data+1]=v end
  if channel==1 then
    local r=w.doc1.rows[start+1];add(r.stable and 1 or 0);add(r.legacy_pre_ending_certificate and 1 or 0)
    for _,key in ipairs({"states","counters","optional","tracked","facts"}) do
      for _,v in ipairs(r[key]) do add(v) end
    end
  else
    for i=start+1,start+n do
      local r=w.doc3.rows[i]
      if r.definition.kind=="journal" then add(r.state);add(r.counter);add(r.optional);add(r.tracked)
      else add(r.value) end
      add(r.stable and 1 or 0)
    end
  end
  return data
end
local function loadStep(s,w)
  if w.phase=="select3" then
    local e=w.files3[w.i3]
    if not e then error("No complete compatible pre-ending snapshot pair") end
    local ok,d=pcall(function() w.raw3=read(e.name);return basic(w.raw3,e,3) end)
    if not ok then nextExtended(w);return end
    w.doc3=d;w.cursor=0;w.phase="validate3"
  elseif w.phase=="validate3" then
    local ok=pcall(function()
      local stop=math.min(w.cursor+128,count3)
      while w.cursor<stop do validateRow(s,w.doc3.rows[w.cursor+1],3,w.cursor);w.cursor=w.cursor+1 end
    end)
    if not ok then nextExtended(w);return end
    if w.cursor==count3 then w.i1=0;nextLegacy(w) end
  elseif w.phase=="select1" then
    local e=w.files1[w.i1]
    if not e then nextExtended(w);return end
    if e.stamp>w.files3[w.i3].stamp then nextLegacy(w);return end
    local ok,d=pcall(function() w.raw1=read(e.name);return basic(w.raw1,e,1) end)
    if not ok then nextLegacy(w);return end
    w.doc1=d;w.cursor=0;w.phase="validate1"
  elseif w.phase=="validate1" then
    local ok=pcall(function()
      local stop=math.min(w.cursor+16,158)
      while w.cursor<stop do validateRow(s,w.doc1.rows[w.cursor+1],1,w.cursor);w.cursor=w.cursor+1 end
      if w.cursor==158 then compatible(w.doc1,w.doc3) end
    end)
    if not ok then nextLegacy(w);return end
    if w.cursor==158 then w.phase="begin" end
  elseif w.phase=="begin" then
    assert(read(w.files1[w.i1].name)==w.raw1 and read(w.files3[w.i3].name)==w.raw3,"Snapshot changed during validation")
    assert(connected(s,w),"Save switched during validation")
    latestCounter=latestCounter+1;w.transaction="latest_"..latestCounter
    s:BeginFileHS4(w.epoch,w.lease,w.transaction,w.doc3.ticket,w.doc3.route,w.doc3.revision,w.doc1.revision,
      w.files1[w.i1].token,w.files3[w.i3].token)
    w.phase="wait_begin"
  elseif w.phase=="wait_begin" then
    if s:ImportTransactionHS4()==w.transaction then w.channel=1;w.phase="transfer" end
  elseif w.phase=="transfer" then
    assert(not s:ImportFaultHS4(),"Snapshot packet rejected")
    local cursor=s:ImportCursorHS4(w.channel)
    if w.waitCursor then
      if cursor~=w.waitCursor then return end
      w.waitCursor=nil
    end
    local total=w.channel==1 and 158 or count3
    if cursor==total then
      if w.channel==1 then w.channel=3;return end
      assert(read(w.files1[w.i1].name)==w.raw1 and read(w.files3[w.i3].name)==w.raw3,"Snapshot changed during transfer")
      s:FinishFileHS4(w.epoch,w.lease,w.transaction);w.phase="wait_finish";return
    end
    local n=w.channel==1 and 1 or math.min(128,total-cursor)
    s:SendPacketHS4(w.epoch,w.lease,w.transaction,w.channel,cursor,n,packet(w,w.channel,cursor,n))
    w.waitCursor=cursor+n
  elseif w.phase=="wait_finish" then
    assert(not s:ImportFaultHS4(),"Snapshot publication rejected")
    if s:GlobalFileReadyHS4() then
      print("[PTFR] Global latest snapshot loaded: "..w.files3[w.i3].name.."; legacy: "..w.files1[w.i1].name)
      w.phase="done";w.doc1=nil;w.doc3=nil;w.raw1=nil;w.raw3=nil
    end
  end
end
local function latestUpdate()
  local s=system(channels[2].name)
  if not s then latest=nil;return true end
  -- Finish exporting an actual new native capture before any older file can
  -- replace its historical cache. A global import never releases a native gate.
  if not s:MayLoadLatestHS4() then latest=nil;return false end
  if latest and not connected(s,latest) then latest=nil end
  if time<latestRetry then return true end
  local ok,err=pcall(function()
    if not latest then
      local files3=listSnapshots(3)
      if #files3==0 then return end
      latestCounter=latestCounter+1
      local w={epoch=s:Epoch(),lease="global_client_"..latestCounter,files3=files3,files1=listSnapshots(1),i3=1,phase="select3"}
      assert(s:OpenClientHS4(w.lease),"Snapshot loader unavailable")
      s:RequireLatestHS4(w.epoch,w.lease);latest=w
    end
    if latest then loadStep(s,latest) end
  end)
  if not ok then
    latest=nil;latestRetry=time+5
    print("[PTFR] Global latest history waiting: "..tostring(err));return true
  end
  return latest~=nil
end
