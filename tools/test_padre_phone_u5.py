"""Actual LuaJIT checks for the explicitly armed U5 getter-only phone trace.

Uses sealed mock game APIs; this is not native engine or Observe-delivery proof.
Writes only this new revision's workspace evidence, never game files or saves.
"""
import json
import re
import sys

from catalog_gig_rollout_r2 import ROOT, sha

sys.path.insert(0, str(ROOT / 'research/phase2b_p0/tooling/python'))
from lupa.luajit21 import LuaRuntime

OUT = ROOT / 'research/gig_restoration/padre_phone_u5'
SOURCE = ROOT / 'diagnostics/PTFR_PadrePhoneU5/init.lua'

MOCK = r'''
local ffi = require('ffi')
state = {
  epoch=7, epochReads=0, appendOpens=0, readOpens=0, writes=0,
  flushes=0, closes=0, clock=1000, hash=1234567, files={}, rows={},
  facts={q307_done=1,PTFRU4_Jeopardy_Ready=1,hey_sts_counter=3},
  journal=1, hooks={}, hookCalls=0, events={}, forbiddenCalls=0,
  phoneEnabled=true, callingEnabled=true, phoneAvailable=true, callActive=false
}
local function forbid(_, key)
  state.forbiddenCalls=state.forbiddenCalls+1
  error('Unapproved API: '..tostring(key))
end
local function sealed(t) return setmetatable(t, {__index=forbid}) end
local function clone(v)
  if type(v)~='table' then return v end
  local r={};for k,x in pairs(v) do r[k]=clone(x) end;return r
end
local player=sealed({GetEntityID=function()
  if state.nilHash then return {} end
  return {hash=ffi.new('uint64_t',state.hash)}
end})
local qs=sealed({GetFactStr=function(_,name)
  if state.badFact==name then error('fact unavailable') end
  return ffi.new('int32_t',state.facts[name] or 0)
end})
local jm=sealed({GetEntryByString=function(_,path,kind)
  assert(path=='quests/street_stories/heywood/vista_del_rey/sts_hey_rey_06')
  assert(kind=='gameJournalQuest')
  if state.missingEntry then return nil end
  return path
end,GetEntryState=function()
  if state.journalFail then error('journal unavailable') end
  return state.journal
end})
local history=sealed({BatchEpoch=function()
  state.epochReads=state.epochReads+1
  if state.epochFail then error('epoch unavailable') end
  if state.drift then return state.epochReads end
  return ffi.new('int32_t',state.epoch)
end})
local phone=sealed({
  IsPhoneEnabled=function()
    if state.badPhone=='IsPhoneEnabled' then error('phone unavailable') end
    return state.phoneEnabled
  end,
  IsCallingEnabled=function()
    if state.badPhone=='IsCallingEnabled' then error('calling unavailable') end
    return state.callingEnabled
  end,
  IsPhoneAvailable=function()
    if state.badPhone=='IsPhoneAvailable' then error('availability unavailable') end
    return state.phoneAvailable
  end
})
local manager=sealed({IsPhoneCallActive=function()
  if state.managerFail then error('manager unavailable') end
  return state.callActive
end})
local container=sealed({Get=function(_,name)
  if name=='PTFR.ActivityStateR3.ActivityState' then return history end
  if name=='PhoneSystem' then
    if state.noPhone then return nil end
    return phone
  end
  error('Unapproved system: '..tostring(name))
end})
Game=sealed({
  GetPlayer=function() if state.noPlayer then return nil end return player end,
  GetQuestsSystem=function() return qs end,
  GetJournalManager=function() return jm end,
  GetScriptableSystemsContainer=function() return container end,
  GetPhoneManager=function() return manager end
})
IsDefined=function(v) return v~=nil end
EnumInt=function(v) return v end
json={encode=function(r)
  if state.encodeFail then error('encode failure') end
  if state.encodeInvalid then return {} end
  state.encoded=clone(r)
  return 'mock JSON'
end}
io={open=function(name,mode)
  if mode=='r' then
    state.readOpens=state.readOpens+1
    if state.allNamesUsed or state.files[name] then return {close=function() return true end} end
    return nil
  end
  assert(mode=='a')
  state.appendOpens=state.appendOpens+1
  if state.openFail then return nil,'disk unavailable' end
  return {
    write=function(_,payload)
      assert(payload=='mock JSON\n')
      state.writes=state.writes+1
      if state.writeFail then return nil,'write failure' end
      state.files[name]=true
      local r=clone(state.encoded);r.file=name
      state.rows[#state.rows+1]=r
      return true
    end,
    flush=function()
      state.flushes=state.flushes+1
      if state.flushFail then return nil,'flush failure' end
      return true
    end,
    close=function()
      state.closes=state.closes+1
      if state.closeFail then return nil,'close failure' end
      return true
    end
  }
end}
os={date=function(pattern)
  if pattern=='!%Y%m%dT%H%M%SZ' then return '20261012T170000Z' end
  assert(pattern=='!%Y-%m-%dT%H:%M:%SZ')
  return '2026-10-12T17:00:00Z'
end,time=function() return state.clock end}
Observe=function(class,method,fn)
  state.hookCalls=state.hookCalls+1
  assert(class=='PhoneSystem')
  assert(method=='OnTriggerCall' or method=='OnPickupPhone' or method=='OnPhoneTimeoutRequest')
  if state.observeFail then error('observer unavailable') end
  state.hooks[method]=fn
end
registerForEvent=function(name,fn)
  assert(name=='onInit' or name=='onUpdate')
  assert(state.events[name]==nil)
  state.events[name]=fn
end
print=function() end
'''


def run():
    assert not (OUT / 'install_receipt.json').exists(), 'Installed U5 evidence is pinned'
    source = SOURCE.read_text(encoding='utf-8')
    allowed_colon_calls = {
        'GetEntityID', 'Get', 'BatchEpoch', 'GetFactStr', 'GetEntryByString',
        'GetEntryState', 'IsPhoneCallActive', 'write', 'flush', 'close',
    }
    assert set(re.findall(r':(\w+)\(', source)) <= allowed_colon_calls
    for forbidden in ('SetFact', 'AddFact', 'ChangeEntryState', 'GiveReward',
                      'Override(', 'Execute(', 'StartQuest', 'QueueRequest'):
        assert forbidden not in source, forbidden
    cases = []

    def env(init=True, observe_fail=False):
        lua = LuaRuntime(unpack_returned_tuples=True)
        lua.execute(MOCK)
        state = lua.globals().state
        state.observeFail = observe_fail
        mod = lua.execute(source)
        if init:
            state.events.onInit()
        return lua, state, mod

    def tick(state, dt):
        state.events.onUpdate(dt)

    def armed(mod):
        assert 'active=true' in mod.Arm()

    def stopped(mod):
        assert 'active=false' in mod.Status()

    def no_more_writes(state, mod):
        before = (state.appendOpens, state.writes)
        tick(state, 1)
        assert (state.appendOpens, state.writes) == before
        stopped(mod)

    # Merely loading, receiving a hook, sampling, or waiting cannot start a trace.
    lua, s, m = env()
    assert set(m.keys()) == {'Arm', 'Status', 'Sample', 'Stop'}
    assert s.hookCalls == 3
    tick(s, 10)
    s.hooks.OnPhoneTimeoutRequest()
    r = m.Sample()
    assert r.stable is True and r.facts.hey_sts_counter == 3
    assert '1234567' in r.session
    assert len(list(r.errors.keys())) == 0
    assert s.appendOpens == 0 and s.readOpens == 0
    assert s.forbiddenCalls == 0
    cases.append('unarmed init/hooks/sample/update use getters only and never write or start a quest')

    # Fresh boxed cdata identities are compared by stable value, not object identity.
    armed(m)
    assert s.writes == 1 and s.rows[1].kind == 'armed'
    assert s.rows[1].sequence == 1 and s.rows[1].frame == 0
    assert s.rows[1].facts.hey_sts_counter == 3
    assert all('delivery not proven' in v for v in s.rows[1].hooks.values())
    tick(s, .4)
    assert s.writes == 1
    tick(s, .6)
    assert s.writes == 2 and s.rows[2].kind == 'heartbeat'
    assert s.rows[2].sequence == 2 and s.rows[2].frame == 2
    assert 'already active' in m.Arm() and s.writes == 2
    cases.append('stable boxed hash/epoch and numeric cdata; explicit arm; one-second heartbeat')

    # Transient protocol flags lasting one rendered update are not lost to 1 Hz sampling.
    request = 'holo_padre_calls_v_start_activate'
    s.facts[request] = 1
    tick(s, .01)
    s.facts[request] = 0
    tick(s, .01)
    assert s.rows[3].kind == 'change' and s.rows[3].facts[request] == 1
    assert s.rows[4].kind == 'change' and s.rows[4].facts[request] == 0
    s.phoneEnabled = False
    tick(s, .01)
    assert s.rows[5].phone.IsPhoneEnabled is False
    assert s.forbiddenCalls == 0
    cases.append('request rising/falling and phone-state changes captured on consecutive updates')

    # Stop flushes one read-only terminal sample; rearm gets a new trace name.
    old_file = s.rows[1].file
    assert 'Stopped by user' in m.Stop()
    assert s.rows[len(s.rows)].kind == 'manual_stop'
    no_more_writes(s, m)
    before = s.writes
    armed(m)
    assert s.writes == before + 1 and s.rows[len(s.rows)].file != old_file
    assert s.rows[len(s.rows)].sequence == 1
    cases.append('manual stop and explicitly rearmed unique filename never replay a quest')

    # Admission remains a trace-only Tower/U4 check, not fake gameplay/history.
    for flag in ('noPlayer', 'nilHash', 'epochFail', 'drift', 'missingEntry', 'journalFail'):
        lua, s, m = env()
        s[flag] = True
        assert 'Not armed:' in m.Arm()
        assert s.appendOpens == 0 and s.readOpens == 0
        stopped(m)
        cases.append(flag + ' refuses initial arm before file output')
    for fact in ('q307_done', 'PTFRU4_Jeopardy_Ready'):
        lua, s, m = env()
        s.facts[fact] = 0
        assert 'Not armed:' in m.Arm() and s.appendOpens == 0
        s.badFact = fact
        assert 'Not armed:' in m.Arm() and s.appendOpens == 0
        cases.append(fact + ' must be confirmed for arm; unknown is not zero or certification')

    # Mid-recording loads/session changes abort without writing a wrong-session row.
    changes = {'epoch': 8, 'hash': 7654321, 'noPlayer': True,
               'nilHash': True, 'drift': True, 'missingEntry': True}
    for name, value in changes.items():
        lua, s, m = env()
        armed(m)
        s[name] = value
        no_more_writes(s, m)
        assert s.writes == 1
        cases.append('recording ' + name + ' change cancels without wrong-session output')

    # Recoverable optional getter errors remain explicit UNKNOWN diagnostics.
    lua, s, m = env()
    s.badFact = request
    s.badPhone = 'IsCallingEnabled'
    s.managerFail = True
    r = m.Sample()
    assert r.stable is True and r.facts[request] == 'UNKNOWN'
    assert r.phone.IsCallingEnabled == 'UNKNOWN' and r.phone.callActive == 'UNKNOWN'
    assert r.errors[request] and r.errors.IsCallingEnabled and r.errors.callActive
    armed(m)
    assert s.rows[1].facts[request] == 'UNKNOWN'
    cases.append('optional getter failures stay UNKNOWN in successful diagnostic rows')
    lua, s, m = env()
    s.phoneAvailable = 1
    assert m.Sample().phone.IsPhoneAvailable == 'UNKNOWN'
    cases.append('non-boolean availability getter is rejected as UNKNOWN')

    # Observe registration can fail; sampling still works and disclaims delivery proof.
    lua, s, m = env(observe_fail=True)
    assert s.hookCalls == 3 and len(list(s.hooks.keys())) == 0
    armed(m)
    assert all(v.startswith('UNAVAILABLE:') for v in s.rows[1].hooks.values())
    tick(s, 1)
    assert s.writes == 2
    cases.append('optional observer-registration failures do not block getter trace')

    # Callback fields are copied to scalar text, bounded, and not retained as handles.
    lua, s, m = env()
    armed(m)
    req = lua.table_from({'caller': 'padre', 'addressee': 'player',
                          'callPhase': 'Incoming', 'callMode': 'Video',
                          'visuals': 'Default', 'isRejectable': True})
    s.hooks.OnTriggerCall(None, req)
    req.caller = 'changed after callback'
    pickup = lua.table_from({'shouldBeRejected': False,
                             'CallInformation': lua.table_from({'contactName': 'padre'})})
    s.hooks.OnPickupPhone(None, pickup)
    s.hooks.OnPhoneTimeoutRequest()
    tick(s, .01)
    row = s.rows[2]
    assert row.kind == 'phone_event' and len(row.events) == 3
    assert row.events[1].data.caller == 'padre'
    assert row.events[1].data.rejectable == 'true'
    assert row.events[2].data.reject == 'false'
    assert row.events[3].kind == 'OnPhoneTimeoutRequest'
    s.hooks.OnTriggerCall(None, None)
    tick(s, .01)
    assert s.rows[3].events[1].data.error
    assert len(s.rows[3].events) == 1
    assert s.forbiddenCalls == 0
    cases.append('optional events are scalar snapshots; malformed callback captured as bounded error')

    lua, s, m = env()
    armed(m)
    s.epoch = 9
    s.hooks.OnPhoneTimeoutRequest()
    no_more_writes(s, m)
    assert s.writes == 1 and 'session changed' in m.Status()
    cases.append('observer callback on a changed loaded session stops instead of mixing sessions')

    lua, s, m = env()
    armed(m)
    for _ in range(129):
        s.hooks.OnPhoneTimeoutRequest()
    assert 'disabled=true' in m.Status() and 'buffer limit' in m.Status()
    no_more_writes(s, m)
    assert 'already active or disabled' in m.Arm()
    cases.append('129 queued callbacks hit bounded buffer and disable without retry')

    # Storage faults are terminal for this module instance, including manual rearm.
    for flag in ('openFail', 'writeFail', 'flushFail', 'closeFail', 'encodeFail', 'encodeInvalid'):
        lua, s, m = env()
        armed(m)
        s[flag] = True
        tick(s, 1)
        assert 'disabled=true' in m.Status()
        before = (s.appendOpens, s.writes)
        s[flag] = False
        no_more_writes(s, m)
        assert 'Not armed:' in m.Arm()
        m.Stop()
        assert (s.appendOpens, s.writes) == before
        cases.append(flag + ' disables later automatic/manual trace writes')

    lua, s, m = env()
    s.allNamesUsed = True
    assert 'no free trace filename' in m.Arm()
    assert s.readOpens == 100 and s.appendOpens == 0
    cases.append('filename probe is bounded to 100 and cannot overwrite an existing trace')

    # Trace lifetime is capped even if in-game dt stalls while a menu is open.
    for wall_time in (False, True):
        lua, s, m = env()
        armed(m)
        if wall_time:
            s.clock += 300
            tick(s, 0)
        else:
            tick(s, 299)
            assert 'active=true' in m.Status()
            tick(s, 1)
        stopped(m)
        assert s.rows[len(s.rows)].kind == 'expired'
        assert 'not a quest timeout diagnosis' in m.Status()
        no_more_writes(s, m)
        cases.append(('wall clock' if wall_time else 'update dt') + ' enforces five-minute trace-only cap')

    result = {
        'status': 'PASS_U5_READ_ONLY_LUAJIT_NOT_ENGINE_PROOF',
        'source_sha256': sha(SOURCE),
        'test_sha256': sha(__file__),
        'cases': cases,
        'case_count': len(cases),
        'game_writes': 0,
        'native_observer_delivery_proven': False,
        'native_phone_repaired': False,
    }
    (OUT / 'tests.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(result['status'], len(cases), 'cases')


if __name__ == '__main__':
    run()
