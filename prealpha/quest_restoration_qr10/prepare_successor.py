"""Reproduce the two-file diagnostic successor from immutable QR9B04 bytes.
Only writes a fresh QR10 candidate; never installs or compiles anything.
"""
from pathlib import Path
import hashlib, json
from preflight import fresh_output
H=Path(__file__).resolve().parent
W=H.parents[1]
REL=Path('bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_QR9_Diagnostics')
OLD=W/'prealpha/quest_restoration_qr9/worker_b/addon'/REL

def sha(b):return hashlib.sha256(b).hexdigest().upper()
def main():
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--candidate',required=True);ap.add_argument('--manifest',required=True);a=ap.parse_args()
    candidate=fresh_output(a.candidate); manifest_path=fresh_output(a.manifest)
    dest=candidate/REL
    assert not dest.exists(),'Fresh output only'
    assert not (H/a.manifest).exists(),'Fresh manifest only'
    old=(OLD/'init.lua').read_bytes()
    assert sha(old)=='ACCE8B7E4E1E355BBC6D6F4752FDBCC7BB3034F594B13AB055EC35742D333718'
    s=old.decode('utf-8')
    def replace(a,b):
        nonlocal s
        assert s.count(a)==1,(a,s.count(a))
        s=s.replace(a,b)
    replace('-- QR9 read-only diagnostics. No engine setters, quest starts, journal writes or save APIs.',
        '-- QR10D01 read-only sampled diagnostics. NativeProxy quest listeners are unsupported.\n-- No engine setters, quest starts, journal writes, save APIs or scripted receiver bridge.')
    replace('local active, attached, stopping, blocked = false, false, false, false','local active, attached, stopping = false, false, false')
    replace('local started, deadline, lastState, known = 0, 0, nil, {}',
        'local started, deadline, lastState, sampled = 0, 0, nil, {}\nlocal sampleAt, sampleErrors, sampleRounds, factReads, sampleChanges = {}, {}, 0, 0, 0\nlocal CALLBACK_MODE = "UNSUPPORTED_NATIVE_PROXY_RECEIVER"\nlocal MAX_SAMPLE_ROUNDS = 450')
    replace('local regs, orphaned, hookState = {}, {}, "NOT_REQUESTED"','local hookState = "NOT_REQUESTED"')
    s=s.replace('[PTFR QR9]','[PTFR QR10]')
    replace('c.schema == 1','c.schema == 2')
    replace('row={schema=1','row={schema=2')
    start=s.index('local function cleanup()')
    end=s.index('function M.stop(reason)',start)
    s=s[:start]+'''local function sampleFacts()
  if not active or stopping then return end
  if sampleRounds >= MAX_SAMPLE_ROUNDS then M.stop("SAMPLE_ROUND_LIMIT"); return end
  sampleRounds=sampleRounds+1
  for _, name in ipairs(cfg.profiles[profile].facts) do
    if not active or stopping then return end
    factReads=factReads+1
    local value,err=read(function() return quests:GetFactStr(name) end)
    local now=os.time()-started
    if not err and (type(value)~="number" or value%1~=0 or value < -2147483648 or value > 2147483647) then
      err="GetFactStr returned non-Int32";value=N
    end
    if err then
      local text=tostring(err):sub(1,160)
      if sampleErrors[name]~=text then emit("FACT_SAMPLE_ERROR",{fact=name,error=text,last_success_elapsed_s=sampleAt[name]}) end
      sampleErrors[name]=text
    else
      local hadError=sampleErrors[name]~=nil
      if hadError then emit("FACT_SAMPLE_RECOVERED",{fact=name,current_sample=value,interpretation="successful getter after error; no native event inferred"}) end
      sampleErrors[name]=nil
      if sampled[name]~=value then
        sampleChanges=sampleChanges+1
        emit("FACT_SAMPLE_CHANGE",{fact=name,previous_sample=sampled[name],current_sample=value,
          previous_success_elapsed_s=sampleAt[name],detected_elapsed_s=now,gap_contained_read_error=hadError,
          evidence="read-only getter difference; not a native callback, write timestamp, write count, graph execution or exact native-write order; intermediate values may be missed"})
      end
      sampled[name],sampleAt[name]=value,now
    end
  end
end
''' +s[end:]
    replace('emit("STOP",{reason=tostring(reason or "USER_STOP"), attached=attached},true)\n  cleanup()',
        'emit("STOP",{reason=tostring(reason or "USER_STOP"), attached=attached, sample_rounds=sampleRounds,\n    fact_getter_calls=factReads,sampled_changes=sampleChanges,native_callback_delivery=CALLBACK_MODE},true)\n  quests=nil\n  emit("CAPTURE_CLEANUP",{native_subscriptions_created=0, sampling_disabled=true,\n    interpretation="no quest listeners were registered; generation invalidated; detach hook remains inert while stopped"},true)')
    replace('say("Stopped: "..tostring(result)..(blocked and "; cleanup failed, further capture blocked in this Lua environment" or ""))',
        'say("Stopped: "..tostring(result))')
    replace('local v,e=read(function() return q:GetFactStr(name) end)\n    facts[name]=v; known[name]=v',
        'factReads=factReads+1\n    local v,e=read(function() return q:GetFactStr(name) end)\n    if not e and (type(v)~="number" or v%1~=0 or v < -2147483648 or v > 2147483647) then e="GetFactStr returned non-Int32" end\n    facts[name]=v; sampled[name]=v; sampleAt[name]=os.time()-started')
    start=s.index('  local gen=generation\n')
    end=s.index('  observeState("ATTACHED_STATE")',start)
    s=s[:start]+'''  emit("NATIVE_CALLBACK_UNAVAILABLE",{mode=CALLBACK_MODE,
    registration_attempts=0,native_subscriptions_created=0,
    reason="Pinned installed QuestsSystem requires scripted-class flag4; installed CET NativeProxy initializes flags2. No supported native fact receiver in this Lua-only successor.",
    evidence="QR10/evidence + independent review; capture makes no live binary/type-hash verification or callback-delivery claim"})
  emit("FACT_SAMPLING_STARTED",{interval_s=CHECK_SECONDS,max_rounds=MAX_SAMPLE_ROUNDS,
    facts_per_round=#cfg.profiles[profile].facts,max_fact_getter_calls=#cfg.profiles[profile].facts*(MAX_SAMPLE_ROUNDS+1),
    interpretation="one pass per observed update interval, no catch-up loop; transitions between reads can be missed"})
''' +s[end:]
    replace('"QR9_capture_%s_%04d.jsonl"','"QR10_capture_%s_%04d.jsonl"')
    replace('  if blocked then say("NOT_RUNNING: prior listener cleanup failed; do not start more captures in this Lua environment"); return nil end\n','')
    replace('  for _,n in ipairs(names) do if type(n)~="string" or #n>128 or not n:match("^[A-Za-z0-9_]+$") then say("NOT_RUNNING: invalid fact"); return nil end end',
        '  local seen={}\n  for _,n in ipairs(names) do if type(n)~="string" or #n>128 or not n:match("^[A-Za-z0-9_]+$") or seen[n] then say("NOT_RUNNING: invalid or duplicate fact"); return nil end; seen[n]=true end')
    replace('generation=generation+1; seq,rows,bytes=0,0,0; known={}; regs={}; attached=false; quests=nil',
        'generation=generation+1; seq,rows,bytes=0,0,0; sampled={}; sampleAt={}; sampleErrors={}\n  sampleRounds,factReads,sampleChanges=0,0,0; attached=false; quests=nil')
    replace('duration_seconds=seconds,max_rows=MAX_ROWS,max_bytes=MAX_BYTES,',
        'duration_seconds=seconds,max_rows=MAX_ROWS,max_bytes=MAX_BYTES,\n      native_callback_delivery=CALLBACK_MODE,fact_sampling_interval_s=CHECK_SECONDS,')
    replace('note="Fact events, bounded journal/phone reads and user labels only; no gameplay test PASS is inferred"',
        'note="Sampled getter differences, bounded journal/phone reads and user labels only; no native callback or gameplay test PASS is inferred"')
    replace('cleanup_failed=blocked,last_wait_reason=waitReason or N,actual_graph_activation=N, ArchiveXL_engine_receipt=N}',
        'sample_rounds=sampleRounds,fact_getter_calls=factReads,sampled_changes=sampleChanges,\n    native_callback_delivery=CALLBACK_MODE,last_wait_reason=waitReason or N,actual_graph_activation=N, ArchiveXL_engine_receipt=N}')
    replace('  observeState()\nend)', '  sampleFacts()\n  if active then observeState() end\nend)')
    c=json.loads((OLD/'watch.json').read_text(encoding='utf-8'))
    c['schema']=2;c['version']='QR10D01'
    c['declared_build']['source_lua_sha256']=sha(s.encode())
    c['declared_build']['callback_contract']='installed EXE class.flags&4 guard vs installed CET NativeProxy flags2; no native subscriptions attempted'
    c['profiles']['D00']={'facts':['phonecall_player_with_regina_jones'],
        'journals':[], 'description':'Conditional diagnostic-only manual outgoing Regina Jones call. Native contact binding contacts/regina_jones + MessengerUtils.contactId + PhoneSystem.GetPhoneCallFactName. Requires existing Call option; no quest admission, no eligibility fabrication. Sampling is not callback delivery.'}
    dest.mkdir(parents=True)
    (dest/'init.lua').write_bytes(s.encode())
    (dest/'watch.json').write_text(json.dumps(c,indent=2)+'\n',encoding='utf-8')
    files=[]
    for name in ('init.lua','watch.json'):
        b=(dest/name).read_bytes(); before=(OLD/name).read_bytes()
        files.append({'path':(REL/name).as_posix(),'source':str(dest/name),'before_sha256':sha(before),'after_sha256':sha(b),'bytes':len(b)})
    manifest={'schema':1,'version':'QR10D01','status':'PREPARED_NOT_INSTALLED','files':files,
        'scope':'Two diagnostic leaves only. Stable GetMod name; preserve all existing logs/unknown files. No Core/REDscript/save writes.',
        'native_callback_delivery':'UNSUPPORTED_NATIVE_PROXY_RECEIVER; no bridge installed or claimed',
        'live_getter_difference_validation':'NOT_RUN','core_rebuild':'NOT_REQUIRED_LUA_ONLY'}
    (H/a.manifest).write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print({'candidate':str(dest),'files':len(files),'version':manifest['version'],'installed':False})

if __name__=='__main__':main()
