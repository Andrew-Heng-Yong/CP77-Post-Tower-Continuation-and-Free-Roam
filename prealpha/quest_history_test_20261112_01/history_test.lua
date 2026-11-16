-- Opt-in test command. The engine compares these exact rows to the history
-- already retained by the loaded save before changing its session baseline.
function api.UsePreEndingForTest(token)
  local ok, result = pcall(function()
    assert(tokenOK(token), "Invalid snapshot token")
    local s = assert(system(), "Load the post-Tower test save first")
    local data = assert(read(prefix .. token .. ".json"), "Snapshot file is missing")
    local parsed = json.decode(data)
    assert(parsed.schema == 1 and parsed.origin == "pre_ending" and #parsed.rows == s:Count(),
      "Expected a complete pre-ending snapshot")
    local rowStart = assert(data:find(',"rows":[', 1, true), "Invalid export header") + 9
    local rowEnd = #data - 3
    assert(data:sub(-3) == "]}\n", "Invalid export ending")
    local rows = {}
    while rowStart <= rowEnd do
      local boundary = data:find('},{"definition":', rowStart, true)
      local stop = boundary or rowEnd
      rows[#rows + 1] = data:sub(rowStart, stop)
      rowStart = stop + 2
    end
    assert(#rows == s:Count(), "Could not read all original row strings")
    s:UsePreEndingForTest(parsed.revision, rows)
    return "History check queued. Use TestHistoryStatus() after closing the console briefly."
  end)
  return ok and result or tostring(result)
end

function api.TestHistoryStatus()
  local s = system()
  return s and s:TestHistoryStatus() or "Load the post-Tower test save first."
end

