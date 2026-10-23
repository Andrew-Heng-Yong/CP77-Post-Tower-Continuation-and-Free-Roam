"""Actual LuaJIT getter/logger checks. No native engine claims or game writes."""
import json,re,sys
from catalog_gig_rollout_r2 import ROOT,sha,read
sys.path.insert(0,str(ROOT/'research/phase2b_p0/tooling/python'))
from lupa.luajit21 import LuaRuntime
OUT=ROOT/'research/gig_restoration/stock_shark_u2'
SOURCE=ROOT/'diagnostics/PTFR_StockGigAuditU2/init.lua'
MOCK=r'''
local ffi=require('ffi')
state={epoch=7,epochReads=0,writes=0,opens=0,clock=0}
local function forbid(_,k) error('Unapproved API: '..tostring(k)) end
local function sealed(t) return setmetatable(t,{__index=forbid}) end
local player=sealed({GetEntityID=function() if state.nilHash then return {} end return {hash=ffi.new('uint64_t',1234567)} end,
 GetWorldPosition=function() return {x=10,y=20,z=30} end})
local qs=sealed({GetFactStr=function(_,name)
 if state.badFact==name then error('fact unavailable') end
 if name=='PTFRU1_Shark_Ready' or name=='q307_done' then return 1 end
 if name=='wat_sts_counter' then return ffi.new('int32_t',3) end
 return 0 end})
local jm=sealed({GetEntryByString=function(_,path) if state.missingEntry then return nil end return path end,
 GetEntryState=function() return 1 end})
local history=sealed({BatchEpoch=function() state.epochReads=state.epochReads+1;if state.drift then return state.epochReads end return state.epoch end})
local u1=sealed({Inspect=function() return 'U1 getter' end,TierStatus=function() return 'Tier getter' end})
local container=sealed({Get=function(_,name)
 if name=='PTFR.ActivityStateR3.ActivityState' then return history end
 if name=='PTFR.ActivityStateR3.NativeReuseU1' then return u1 end
 error('unknown system') end})
Game=sealed({GetPlayer=function() if state.noPlayer then return nil end return player end,
 GetQuestsSystem=function() return qs end,GetJournalManager=function() return jm end,
 GetScriptableSystemsContainer=function() return container end,
 GetTransactionSystem=function() return sealed({GetItemQuantity=function() return 100 end}) end})
IsDefined=function(v) return v~=nil end
EnumInt=function(v) return v end
ItemID={FromTDBID=function(v) return v end};TweakDBID={new=function(v) return v end}
json={encode=function(r) state.last=r;if state.encodeFail then error('encode') end return 'mock JSON' end}
io={open=function(_,mode)
 if mode=='r' then return nil end
 state.opens=state.opens+1
 if state.openFail then return nil,'disk unavailable' end
 return {write=function() state.writes=state.writes+1;if state.writeFail then return nil,'write failure' end return true end,
 flush=function() return true end,close=function() return true end} end}
registerForEvent=function(name,fn) assert(name=='onUpdate');tick=fn end
print=function() end
'''

def run():
    assert not (OUT/'install_receipt.json').exists(),'Installed evidence pinned'
    source=SOURCE.read_text(encoding='utf-8')
    assert set(re.findall(r':(\w+)\(',source)) <= {'GetEntityID','GetFactStr','Get','BatchEpoch','GetEntryByString','GetEntryState','Inspect','TierStatus','GetItemQuantity','GetWorldPosition','write','flush','close'}
    cases=[]
    def env():
        lua=LuaRuntime(unpack_returned_tuples=True);lua.execute(MOCK)
        mod=lua.execute(source);return lua,lua.globals().state,mod
    lua,s,m=env();r=m.Sample()
    assert r['stable'] is True and r['facts']['wat_sts_counter']==3 and r['money']==100
    assert '1234567' in r['player'] and len(list(r['errors'].keys()))==0
    lua.globals().tick(.4);assert s.writes==0
    lua.globals().tick(.6);assert s.writes==1 and s.last.sequence==1
    lua.globals().tick(1);assert s.writes==2 and s.last.sequence==2
    cases.append('stable boxed identity, numeric cdata, throttled getter-only logging')
    lua,s,m=env();s.badFact='wat_sts_counter';s.missingEntry=True;r=m.Sample()
    assert r['facts']['wat_sts_counter']=='UNKNOWN' and r['errors']['wat_sts_counter']
    assert all(v=='UNKNOWN' for v in r['journal'].values());cases.append('failed getters remain unknown')
    for flag in ['drift','noPlayer','nilHash']:
        lua,s,m=env();s[flag]=True;lua.globals().tick(1)
        assert s.opens==0 and m.Sample()['stable'] is not True
        cases.append(flag+' prevents file output')
    for flag in ['openFail','writeFail','encodeFail']:
        lua,s,m=env();s[flag]=True;lua.globals().tick(1);opens=s.opens;writes=s.writes
        s[flag]=False;lua.globals().tick(1)
        assert s.opens==opens and s.writes==writes and 'disabled=true' in m.Status()
        cases.append(flag+' disables subsequent writes')
    review=OUT/'source_review.json';assert read(review)['status']=='PASS_U2_STOCK_DEPENDENCY_SOURCE_AUDIT_NOT_ENGINE_PROOF'
    result=dict(status='PASS_U2_READ_ONLY_LUAJIT_NOT_ENGINE_PROOF',source_sha256=sha(SOURCE),
        source_review_sha256=sha(review),test_sha256=sha(__file__),cases=cases,game_writes=0)
    (OUT/'tests.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(result['status'],len(cases),'cases')
if __name__=='__main__':run()
