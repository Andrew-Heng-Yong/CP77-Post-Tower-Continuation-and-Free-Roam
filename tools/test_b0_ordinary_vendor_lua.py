"""Execute CET controller under Lua 5.1 with mocked game/IO boundaries."""
from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'research/phase2b_p0/tooling/python'))
from lupa.lua51 import LuaRuntime  # type: ignore
import json
import hashlib


def main():
    lua=LuaRuntime(unpack_returned_tuples=True)
    lua.execute('''
      events={};facts={};records={};writes={};scene_active=false;driver_available=true;fail_log=false
      function registerForEvent(n,f) events[n]=f end
      function IsDefined(v) return v~=nil end
      CName={new=function(x)return x end}
      function ToVector4(x)return x end
      function ToEulerAngles(x)return x end
      json={encode=function(x)table.insert(records,x);return '{}' end}
      io={open=function()return {write=function()if fail_log then return nil end return true end,
      flush=function()return true end,close=function()end}end}
      q={GetFactStr=function(self,n)return facts[n] or 0 end,
        SetFactStr=function(self,n,v)assert(n:find('^PTFRB0OV'));facts[n]=v;table.insert(writes,n)end}
      player={position={x=-506.4,y=-760.19,z=7.42}}
      function player:GetWorldPosition()return self.position end
      function player:IsInCombat()return false end
      function player:GetEntityID()return 1 end
      runtime={GetPolls=function()return 10 end,GetPositionReads=function()return 8 end,
        GetDistanceChecks=function()return 8 end,GetFactReads=function()return 30 end,GetFactWrites=function()return 2 end}
      Game={GetPlayer=function()return player end,GetQuestsSystem=function()return q end,
        GetScriptableSystemsContainer=function()return {Get=function()if driver_available then return runtime end end}end,
        GetSceneSystem=function()return {GetScriptInterface=function()return {IsEntityInScene=function()return scene_active end}end}end,
        GetWorkspotSystem=function()return {IsActorInWorkspot=function()return false end}end,
        GetTeleportationFacility=function()return {Teleport=function(self,p,xyz,angles)p.position=xyz end}end}
    ''')
    cohort=json.loads((ROOT/'research/b0_ordinary_vendor_batch/cohort.json').read_text())
    manifest=json.loads((ROOT/'research/b0_ordinary_vendor_batch/validation/build_manifest.json').read_text())
    facts=lua.globals().facts
    for f,v in manifest['common_guards'].items():facts[f]=v if f!='PTFRB0OVB_Mode' else 0
    for s in cohort['sites']:facts[s['gate']]=1;facts[s['prefix']+'Ready']=1
    text=(ROOT/'diagnostics/PTFR_B0_OrdinaryVendors/init.lua').read_text()
    mod=lua.execute(text);lua.globals().events.onInit()
    lua.globals().scene_active=True
    assert mod.Start() is False
    lua.globals().scene_active=False;lua.globals().driver_available=False
    assert mod.Start() is False
    lua.globals().driver_available=True
    assert mod.Start() is True
    lua.globals().events.onUpdate(9)
    assert (facts['PTFRB0OVB_Mode'] or 0)==0
    assert all((facts[s['prefix']+'Enabled'] or 0)==0 for s in cohort['sites'])
    # A naturally locked shop and an explicitly excluded working site stay off.
    facts[cohort['sites'][0]['gate']]=0
    assert mod.Skip(cohort['sites'][1]['id']) is True
    assert mod.Start() is True
    facts['PTFRB0OVB_Ack']=facts['PTFRB0OVB_Challenge']
    lua.globals().events.onUpdate(.5)
    assert facts['PTFRB0OVB_Mode']==1
    assert sum(facts[s['prefix']+'Enabled']==1 for s in cohort['sites'])==23
    assert facts[cohort['sites'][0]['gate']]==0
    pfx=cohort['sites'][2]['prefix']
    facts[pfx+'Near']=1;facts[pfx+'Entries']=1
    assert mod.Stop() is False and mod.Checkpoint() is False
    assert mod.Go('junk') is False
    assert mod.Outside() is True
    facts[pfx+'Near']=0;facts[pfx+'Far']=1;facts[pfx+'Exits']=1
    assert mod.Checkpoint() is True
    # Lua module restart must preserve saved mode, exclusions, counters and flags.
    before=len(lua.globals().writes)
    mod=lua.execute(text);lua.globals().events.onInit();lua.globals().events.onUpdate(2)
    assert len(lua.globals().writes)==before
    assert facts['PTFRB0OVB_Mode']==1 and facts[cohort['sites'][1]['prefix']+'Excluded']==1
    assert mod.Start() is False
    assert mod.Stop() is True
    assert facts['PTFRB0OVB_Suspended']==1
    assert all(facts[s['prefix']+'Enabled']==0 and facts[s['prefix']+'Far']==0 for s in cohort['sites'])
    assert mod.Resume() is True and facts['PTFRB0OVB_Suspended']==0
    lua.globals().fail_log=True
    assert mod.Start() is False
    assert facts['PTFRB0OVB_Mode']==0
    report={'status':'PASS','runtime':'Lua 5.1',
            'controller_sha256':hashlib.sha256((ROOT/'diagnostics/PTFR_B0_OrdinaryVendors/init.lua').read_bytes()).hexdigest().upper(),
            'cases':['scene refusal','missing driver','ack timeout','eligible subset','local gate preserved','excluded site persisted','active Stop refusal','idle checkpoint','module reload no rearm','stop','log failure refusal']}
    (ROOT/'research/b0_ordinary_vendor_batch/validation/controller_test.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: Lua5.1 refusal/ack timeout, 23 eligible arm, locked/excluded preservation, active Stop refusal, checkpoint, module reload without rearm, clean Stop and failed-log refusal')


if __name__=='__main__':main()
