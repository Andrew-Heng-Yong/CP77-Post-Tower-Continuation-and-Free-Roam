-- Temporary development diagnostic. No callbacks, quest changes, polls or spam.
-- Capture() only reads native APIs and writes a new report inside this CET mod.
local M = {}
local sequence = 0

local function loadData()
  local f = assert(io.open('data.json', 'r'), 'capture catalogue missing')
  local text = f:read('*a'); f:close()
  local d = json.decode(text)
  assert(type(d) == 'table' and d.schema == 1 and d.kind == 'S23_READ_ONLY_WHITELIST_CAPTURE', 'wrong catalogue')
  assert(type(d.jobs) == 'table' and #d.jobs == 58, 'wrong whitelist count')
  local seen = {}
  for _, row in ipairs(d.jobs) do
    assert(type(row.id) == 'string' and not seen[row.id], 'duplicate or invalid job')
    seen[row.id] = true
    assert(type(row.root) == 'string' and type(row.journals) == 'table' and #row.journals > 0 and type(row.facts) == 'table', 'invalid job data')
    local rootFound = false
    for _, j in ipairs(row.journals) do
      assert(type(j.path) == 'string' and type(j.class) == 'string', 'invalid journal data')
      if j.path == row.root and j.class == 'gameJournalQuest' then rootFound = true end
    end
    assert(rootFound, 'root missing from job data')
    for _, n in ipairs(row.facts) do assert(type(n) == 'string' and n:match('^[A-Za-z0-9_]+$'), 'invalid fact name') end
  end
  return d
end

local function journalState(jm, path, class)
  local e = jm:GetEntryByString(path, class)
  if not e then return 'Missing' end
  local s = jm:GetEntryState(e)
  for _, name in ipairs({'Inactive', 'Active', 'Succeeded', 'Failed'}) do
    if s == gameJournalEntryState[name] then return name end
  end
  return 'Unknown:' .. tostring(s)
end

local function sample(d, jm, qs)
  local result = {jobs = {}, context = {}, settledBefore = not jm:HasAnyDelayedStateChanges()}
  local signature = {}
  local cacheJ, cacheF = {}, {}
  local unknown = 0
  for _, n in ipairs(d.context_facts) do
    local v = qs:GetFactStr(n)
    assert(type(v) == 'number', 'fact API unavailable: ' .. n)
    result.context[n] = v; signature[#signature + 1] = n .. '=' .. tostring(v)
  end
  for _, row in ipairs(d.jobs) do
    local job = {id = row.id, title = row.title, root = row.root, coverage = row.coverage, journals = {}, facts = {}}
    for _, entry in ipairs(row.journals) do
      local key = entry.class .. ':' .. entry.path
      if cacheJ[key] == nil then cacheJ[key] = journalState(jm, entry.path, entry.class) end
      local state = cacheJ[key]
      job.journals[#job.journals + 1] = {path = entry.path, class = entry.class, state = state}
      if entry.path == row.root then job.rootState = state end
      if state == 'Missing' or state:sub(1, 7) == 'Unknown' then unknown = unknown + 1 end
      signature[#signature + 1] = key .. '=' .. state
    end
    for _, n in ipairs(row.facts) do
      if cacheF[n] == nil then
        cacheF[n] = qs:GetFactStr(n)
        assert(type(cacheF[n]) == 'number', 'fact API unavailable: ' .. n)
      end
      job.facts[n] = cacheF[n]; signature[#signature + 1] = n .. '=' .. tostring(cacheF[n])
    end
    result.jobs[#result.jobs + 1] = job
  end
  result.settledAfter = not jm:HasAnyDelayedStateChanges()
  result.unknownJournalRows = unknown
  return result, table.concat(signature, '\n')
end

function M.Capture()
  local ok, answer = pcall(function()
    local jm, qs = Game.GetJournalManager(), Game.GetQuestsSystem()
    assert(jm and qs and Game.GetPlayer(), 'load the same working post-Tower save first')
    local d = loadData()
    local first, a = sample(d, jm, qs)
    local second, b = sample(d, jm, qs)
    local stable = a == b and first.settledBefore and first.settledAfter and second.settledBefore and second.settledAfter
    local report = {schema = 1, kind = d.kind, status = stable and 'STABLE_READ_ONLY_CAPTURE' or 'UNSETTLED_DO_NOT_USE_FOR_ADMISSION',
      capturedAt = os.date('!%Y-%m-%dT%H:%M:%SZ'), nativeWrites = 0, saveWrites = 0,
      repeatedReadMatched = a == b, first = first, second = second,
      limits = 'Catalogue is not complete execution history. Missing/unknown entries remain unknown. No restoration is authorized by this report alone.'}
    local counts = {Inactive = 0, Active = 0, Succeeded = 0, Failed = 0, Unknown = 0}
    for _, row in ipairs(first.jobs) do local name = counts[row.rootState] and row.rootState or 'Unknown'; counts[name] = counts[name] + 1 end
    report.rootCounts = counts
    local filename
    repeat
      sequence = sequence + 1
      filename = 'capture_s23_' .. os.date('!%Y%m%dT%H%M%SZ') .. '_' .. tostring(sequence) .. '.json'
      local existing = io.open(filename, 'r')
      if existing then existing:close() else break end
    until false
    local encoded = json.encode(report)
    local f = assert(io.open(filename, 'w'), 'cannot create report')
    local wrote, err = f:write(encoded); local closed, closeErr = f:close()
    assert(wrote and closed, err or closeErr or 'report write failed')
    return 'S23 read-only capture: ' .. filename .. ' | stable=' .. tostring(stable) .. ' roots I/A/S/F/?=' .. counts.Inactive .. '/' .. counts.Active .. '/' .. counts.Succeeded .. '/' .. counts.Failed .. '/' .. counts.Unknown .. ' | no quest/fact/save changes.'
  end)
  if ok then return answer end
  return 'S23 capture unavailable; no quest/fact/save changes: ' .. tostring(answer)
end

return M
