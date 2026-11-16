-- Local test selection. The chosen export is accepted only when its complete
-- row payload matches the loaded save's retained history.
local retainedTestToken = "20261111T224622Z_159_1"

local function retainedComparison(s, w)
  if not s:CanCompareRetainedHistory() then return nil end
  local ok, result = pcall(function()
    local data = assert(read(prefix .. retainedTestToken .. ".json"), "pre-ending export missing")
    local parsed = json.decode(data)
    local canonical = json.decode(w.parts[1] .. "]}")
    assert(parsed.schema == 1 and parsed.origin == "pre_ending" and
      parsed.catalogue == canonical.catalogue and #parsed.rows == w.count and
      parsed.revision > 0 and parsed.revision < w.revision and parsed.revision % 1 == 0,
      "pre-ending export does not match this catalogue or revision")
    local marker = ',"rows":['
    local start = assert(data:find(marker, 1, true), "invalid pre-ending export header")
    return {data = data, revision = parsed.revision, parts = {data:sub(1, start + #marker - 1)}}
  end)
  if not ok then
    print("[PTFR] Retained history test skipped: " .. tostring(result))
    return nil
  end
  return result
end

local function acknowledge(s, w, token)
  local retained = w.retained
  if retained and retained.data == table.concat(retained.parts) .. "]}\n" then
    assert(s:AckFileWithRetainedHistory(w.epoch, w.revision, token, retained.revision),
      "Snapshot changed before retained history acknowledgement")
    print("[PTFR] Using verified pre-ending revision " .. tostring(retained.revision) .. " for this session.")
  else
    assert(s:AckFile(w.epoch, w.revision, token), "Snapshot changed before acknowledgement")
    if retained then print("[PTFR] Retained history test skipped: loaded save rows differ from the export.") end
  end
end

