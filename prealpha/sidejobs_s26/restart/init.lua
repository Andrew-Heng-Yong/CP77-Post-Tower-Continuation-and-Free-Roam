-- Manual S26 diagnostic only. Loading this file performs no native calls.
local M, sequence = {}, 0
local cassius = createCassiusProbe()
function M.ArmCassius() return cassius.Arm() end
function M.StopCassius() return cassius.Stop() end
local function finite(v) return type(v) == 'number' and v == v and v ~= math.huge and v ~= -math.huge end
local function observation(fn, expected)
  local ok, v = pcall(fn)
  if not ok then return {status='Unknown', reason=tostring(v)} end
  if expected == 'number' and not finite(v) then return {status='Unknown', reason='non-finite or unavailable number'} end
  if expected and type(v) ~= expected then return {status='Unknown', reason='wrong result type'} end
  return {status='Observed', value=v}
end
local function signature(v)
  if type(v) ~= 'table' then return type(v) .. ':' .. tostring(v) end
  local keys, out = {}, {}
  for k in pairs(v) do keys[#keys+1] = k end
  table.sort(keys, function(a,b) return tostring(a)<tostring(b) end)
  for _,k in ipairs(keys) do out[#out+1] = tostring(k) .. '=' .. signature(v[k]) end
  return '{' .. table.concat(out,';') .. '}'
end
local function playerIdentity(player)
  local id=player:GetEntityID()
  assert(id and id.hash~=nil,'player entity hash missing')
  return tostring(id.hash)
end
local function loadData()
  local f=assert(io.open('data.json','r'),'capture catalogue missing')
  local text=f:read('*a'); f:close()
  local d=json.decode(text)
  assert(type(d)=='table' and d.schema==2 and d.kind=='S26_READ_ONLY_RESTART_AND_SERVICE_CAPTURE','wrong catalogue')
  assert(type(d.jobs)=='table' and #d.jobs==58 and type(d.items)=='table','wrong catalogue size')
  local ids={}
  for _,r in ipairs(d.jobs) do
    assert(type(r.id)=='string' and not ids[r.id] and type(r.root)=='string','invalid/duplicate job'); ids[r.id]=true
    assert(type(r.journals)=='table' and #r.journals>0 and type(r.facts)=='table' and type(r.owners)=='table','invalid job data')
    local found=false
    for _,j in ipairs(r.journals) do
      assert(type(j.path)=='string' and type(j.class)=='string','invalid journal')
      if j.path==r.root and j.class=='gameJournalQuest' then found=true end
    end
    assert(found,'missing root')
    for _,n in ipairs(r.facts) do assert(type(n)=='string' and n:match('^[A-Za-z0-9_]+$'),'invalid fact') end
    for _,o in ipairs(r.owners) do
      assert(type(o.tag)=='string' and o.tag:match('^PTFR[A-Za-z0-9_]+$') and type(o.facts)=='table','invalid owner')
      for _,n in ipairs(o.facts) do assert(type(n)=='string' and n:match('^PTFR[A-Za-z0-9_]+$'),'invalid owner fact') end
    end
  end
  for _,i in ipairs(d.items) do assert(type(i.id)=='string' and i.id:match('^Items%.[A-Za-z0-9_]+$'),'invalid item') end
  return d
end
local function readJournal(jm,path,class)
  local ok,e=pcall(function() return jm:GetEntryByString(path,class) end)
  if not ok then return {path=path,class=class,state='Unknown',error=tostring(e)} end
  if not e then return {path=path,class=class,state='Missing'} end
  local result={path=path,class=class,state='Unknown'}
  local got,s=pcall(function() return jm:GetEntryState(e) end)
  if got then
    for _,name in ipairs({'Inactive','Active','Succeeded','Failed'}) do
      if s==gameJournalEntryState[name] then result.state=name end
    end
  else result.error=tostring(s) end
  result.visited=observation(function() return jm:IsEntryVisited(e) end,'boolean')
  result.tracked=observation(function() return jm:IsEntryTracked(e) end,'boolean')
  if class=='gameJournalQuestObjective' then
    result.optional=observation(function() return jm:GetIsObjectiveOptional(e) end,'boolean')
    result.hasCounter=observation(function() return e:HasCounter() end,'boolean')
    if result.hasCounter.status=='Observed' and result.hasCounter.value then
      result.currentCounter=observation(function() return jm:GetObjectiveCurrentCounter(e) end,'number')
      result.totalCounter=observation(function() return jm:GetObjectiveTotalCounter(e) end,'number')
    end
  end
  return result
end
local function sample(d,jm,qs,player)
  local r={jobs={},context={},items={},settledBefore=observation(function() return not jm:HasAnyDelayedStateChanges() end,'boolean')}
  r.player=observation(function() return playerIdentity(player) end,'string')
  local cacheJ,cacheF={},{}
  local function fact(n)
    if not cacheF[n] then cacheF[n]=observation(function() return qs:GetFactStr(n) end,'number') end
    return cacheF[n]
  end
  for _,n in ipairs(d.context_facts) do r.context[n]=fact(n) end
  for _,row in ipairs(d.jobs) do
    local job={id=row.id,title=row.title,root=row.root,journals={},facts={},owners={},rootState='Unknown',graphLiveness='NOT_OBSERVED',rewardHistory='UNKNOWN'}
    for _,j in ipairs(row.journals) do
      local k=j.class..':'..j.path
      if not cacheJ[k] then cacheJ[k]=readJournal(jm,j.path,j.class) end
      local v=cacheJ[k]; job.journals[#job.journals+1]=v
      if j.path==row.root and j.class=='gameJournalQuest' then job.rootState=v.state end
    end
    for _,n in ipairs(row.facts) do job.facts[n]=fact(n) end
    for _,o in ipairs(row.owners) do
      local observed={tag=o.tag,facts={},graphLiveness='NOT_OBSERVED: facts are not node state'}
      for _,n in ipairs(o.facts) do observed.facts[n]=fact(n) end
      job.owners[#job.owners+1]=observed
    end
    job.policyDisposition=job.rootState=='Succeeded' and 'PRESERVE_COMPLETED' or
      ((job.rootState=='Active' or job.rootState=='Failed' or job.rootState=='Inactive') and 'RESTART_CANDIDATE_NOT_AUTHORIZED' or 'DEFER_UNKNOWN')
    r.jobs[#r.jobs+1]=job
  end
  for _,item in ipairs(d.items) do
    local q=observation(function()
      local ts=assert(Game.GetTransactionSystem(),'transaction getter unavailable')
      return ts:GetItemQuantity(player,ItemID.CreateQuery(TweakDBID.new(item.id)))
    end,'number')
    if q.status=='Observed' and (q.value<0 or q.value%1~=0) then q={status='Unknown',reason='invalid inventory quantity'} end
    r.items[#r.items+1]={id=item.id,quantity=q,scope='current player inventory only; not stash/vendor/equipment/reward history'}
  end
  r.settledAfter=observation(function() return not jm:HasAnyDelayedStateChanges() end,'boolean')
  r.playerAfter=observation(function() local p=assert(Game.GetPlayer(),'player unavailable'); return playerIdentity(p) end,'string')
  return r
end
local function settled(s)
  return s.settledBefore.status=='Observed' and s.settledBefore.value and s.settledAfter.status=='Observed' and s.settledAfter.value and
    s.player.status=='Observed' and s.playerAfter.status=='Observed' and s.player.value==s.playerAfter.value
end
function M.Capture()
  cassius.Stop()
  local ok,answer=pcall(function()
    local player,jm,qs=Game.GetPlayer(),Game.GetJournalManager(),Game.GetQuestsSystem()
    assert(player and jm and qs,'load the current working post-Tower save first')
    local d=loadData()
    local a,b=sample(d,jm,qs,player),sample(d,jm,qs,player)
    local matched=signature(a)==signature(b)
    local stable=matched and settled(a) and settled(b)
    local counts={Inactive=0,Active=0,Succeeded=0,Failed=0,Unknown=0}
    for _,row in ipairs(a.jobs) do local k=counts[row.rootState] and row.rootState or 'Unknown'; counts[k]=counts[k]+1 end
    local report={schema=2,kind=d.kind,status=stable and 'STABLE_READ_ONLY_CAPTURE' or 'UNSETTLED_DO_NOT_USE_FOR_ADMISSION',
      capturedAt=os.date('!%Y-%m-%dT%H:%M:%SZ'),nativeWrites=0,saveWrites=0,restartAuthorized=false,repeatedReadMatched=matched,
      donorCatalogueSha256=d.donor_catalogue_sha256,coverageSha256=d.coverage_sha256,first=a,second=b,rootCounts=counts,
      cassius=cassius.Snapshot(),
      limits='Read-only observations, not an atomic transaction. Unknown getters remain Unknown. Current inventory is not historical reward proof. Owner facts do not prove node liveness or retirement. No vendor-stock query or restart.'}
    local filename
    repeat
      sequence=sequence+1
      filename='capture_s26_'..os.date('!%Y%m%dT%H%M%SZ')..'_'..tostring(sequence)..'.json'
      local old=io.open(filename,'r'); if old then old:close() else break end
    until false
    local text=json.encode(report)
    local f=assert(io.open(filename,'w'),'cannot create report')
    local wrote,err=f:write(text); local closed,closeErr=f:close(); assert(wrote and closed,err or closeErr or 'report write failed')
    return 'S26 read-only capture: '..filename..' | stable='..tostring(stable)..' roots I/A/S/F/?='..counts.Inactive..'/'..counts.Active..'/'..counts.Succeeded..'/'..counts.Failed..'/'..counts.Unknown..' | no restart or quest/fact/save changes.'
  end)
  if ok then return answer end
  return 'S26 capture unavailable; no quest/fact/save changes: '..tostring(answer)
end
return M
