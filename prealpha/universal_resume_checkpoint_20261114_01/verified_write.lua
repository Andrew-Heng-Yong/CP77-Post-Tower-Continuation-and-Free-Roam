local function writeVerified(path,temp,data,isCurrent)
  local file=assert(io.open(temp,"wb"),"Cannot create snapshot temporary file")
  local wrote,flushed
  local ok,err=pcall(function() wrote=file:write(data);flushed=file:flush() end)
  local closed=file:close()
  assert(ok and wrote and flushed and closed,tostring(err or "Snapshot write/flush/close failed"))
  assert(read(temp)==data,"Snapshot temporary readback mismatch")
  if not isCurrent() then return false end
  assert(not read(path),"Snapshot destination appeared")
  assert(os.rename(temp,path),"Snapshot rename failed")
  assert(read(path)==data,"Snapshot committed readback mismatch")
  return true
end

