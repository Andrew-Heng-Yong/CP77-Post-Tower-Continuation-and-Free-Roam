"""Native prevention evidence and manual command checks; not a live gameplay test."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'research/phase2b_p0/tooling/python'))
from lupa.luajit21 import LuaRuntime
sha=lambda p: hashlib.sha256(p.read_bytes()).hexdigest().upper()
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))

def main():
 out=ROOT/'research/dogtown_dt1/wanted/tests_01.json'
 if out.exists(): raise FileExistsError(out)
 data=read(ROOT/'research/dogtown_dt1/wanted/native_records_01.json')
 records={r['hash']:r for r in data['records']}; named={r['name']:r for r in data['records'] if r.get('name')}
 checks=0; heat0={}
 for name,threshold in [('PreventionData.NCPDDataMatrix',100),('PreventionData.DogTownDataMatrix',100),('PreventionData.DogTown_Kurt_DataMatrix',200),('PreventionData.DogTown_Bennet_DataMatrix',50)]:
  r=records[named[name]['fields']['heat0']['hash']]['fields']; assert float(r['heatThresholdCapacity'])==threshold; checks+=1
  assert float(r['heatKillPolice'])==200 and float(r['heatRangeAttackPolice'])==100 and float(r['heatKillCiv'])==100; checks+=3
  heat0[name]={k:r[k] for k in ['heatKillCiv','heatRangeAttackCiv','heatKillPolice','heatRangeAttackPolice','heatThresholdCapacity']}
 source=(HERE/'diagnostic.lua').read_text()
 for word in ['SetFact','QueueRequest','Toggle','Clear','Register','Override','Observe','Save','Load','execute','GetAgentRegistry']:
  assert word not in source,word; checks+=1
 outputs=[]
 for enabled,locked,react,dogtown,free,heat in [(True,False,True,True,False,0),(False,True,False,True,True,0),(True,False,True,False,False,1)]:
  lua=LuaRuntime(); rows=[]; lua.globals().print=lambda x: rows.append(x)
  lua.globals().cfg=lua.table_from(dict(enabled=enabled,locked=locked,react=react,dogtown=dogtown,free=free,heat=heat))
  lua.execute('''local function deny(_,n) error('Disallowed API '..n) end
   local d={IsDogTown=function()return cfg.dogtown end};setmetatable(d,{__index=deny})
   local p={IsSystemEnabled=function()return cfg.enabled end,IsSystemLocked=function()return cfg.locked end,CanPreventionReactToInput=function()return cfg.react end,GetCurrentDistrict=function()return d end,GetHeatStageAsInt=function()return cfg.heat end};setmetatable(p,{__index=deny})
   local s={IsPointInPreventionFreeArea=function()return cfg.free end};setmetatable(s,{__index=deny})
   Game={GetScriptableSystemsContainer=function()return {Get=function(_,n)assert(n=='PreventionSystem');return p end} end,GetPreventionSpawnSystem=function()return s end,GetPlayer=function()return {GetWorldPosition=function()return {} end} end};setmetatable(Game,{__index=deny})''')
  lua.execute(source); assert len(rows)==6 and all('Unknown' not in r for r in rows); checks+=7; outputs.append(rows)
 lua=LuaRuntime(); rows=[];lua.globals().print=lambda x:rows.append(x)
 lua.execute('Game={GetScriptableSystemsContainer=function()return {Get=function()return nil end} end,GetPreventionSpawnSystem=function()return nil end,GetPlayer=function()return nil end}')
 lua.execute(source); assert rows==[n+'=Unknown' for n in ['enabled','locked','canReact','Dogtown','freeArea','heat']];checks+=6
 native=(ROOT/'research/finalboards_dismissal/decompiled/core/systems/preventionSystem.script').read_text()
 for method in ['IsSystemEnabled','IsSystemLocked','CanPreventionReactToInput','GetCurrentDistrict','GetHeatStageAsInt']: assert f'func {method}(' in native;checks+=1
 spawn=(ROOT/'research/finalboards_dismissal/decompiled/core/systems/preventionSpawnSystem.script').read_text();assert 'func IsPointInPreventionFreeArea(' in spawn;checks+=1
 saved=read(ROOT/'research/dogtown_dt1/wanted/saved_prevention_01.json')
 assert len(saved['samples'])==2;checks+=1
 for s in saved['samples']:
  f=s['persistent_fields_decoded'];assert f['SystemEnabled']=='True' and f['CrimeScoreMultiplierByQuest']=='1' and f['SystemLockSources']==[];checks+=3
 for i in data['inputs']:assert sha(Path(i['path']))==i['sha256'];checks+=1
 result={'status':'PASS_NATIVE_EVIDENCE_AND_LUAJIT_NOT_LIVE','checks':checks,'heat0':heat0,'command_outputs':outputs,'source_pins':{str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in [HERE/'audit_tweaks.ps1',HERE/'inspect_save.ps1',HERE/'diagnostic.lua',HERE/'test.py',ROOT/'research/dogtown_dt1/wanted/native_records_01.json',ROOT/'research/dogtown_dt1/wanted/saved_prevention_01.json',ROOT/'research/finalboards_dismissal/decompiled/core/systems/preventionSystem.script',ROOT/'research/finalboards_dismissal/decompiled/core/systems/preventionSpawnSystem.script',ROOT/'research/finalboards_dismissal/decompiled/core/systems/prevention/districtManager.script']},'native_writes':0,'game_writes':0,'save_writes':0,'wanted_repair_implemented':False}
 out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'checks':checks,'out':str(out)}))
if __name__=='__main__':main()
