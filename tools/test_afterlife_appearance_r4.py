"""Source, lint and read-only diagnostic checks; no game writes/live claims."""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'research/afterlife_world'
OUT = BASE / 'appearance_r4'
GAME = Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
DRIVER = ROOT / 'redscript/PTFR_Afterlife_Appearance_R4/AfterlifeAppearanceR4.reds'
DIAG = ROOT / 'diagnostics/PTFR_Afterlife_Behavior_Audit/init.lua'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def lua_tests():
    sys.path.insert(0, str(ROOT / 'research/phase2b_p0/tooling/python'))
    from lupa.lua51 import LuaRuntime
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute('''
events={}; entities={}; byid={}; writes=0; closed=0; getterCalls=0
function registerForEvent(k,f) events[k]=f end
function Observe(a,b,f) attached=f end
function IsDefined(v) return type(v)=="table" end
function print(s) end
json={encode=function(row) lastrow=row;return "{}" end}
io={open=function() return {write=function(self,s)writes=writes+1;return self end,
 close=function()closed=closed+1 end} end}
CName={new=function(s)return s end}
pos={x=-1424,y=1023,z=17}
p={GetWorldPosition=function()return pos end}
q={GetFactStr=function()return 1 end}
function make(id,entry,app,ws)
 local a={id=id,entry=entry,app=app,ws=ws,pos={x=-1424,y=1023,z=17}}
 a.GetEntityID=function()return {hash=id}end;a.GetWorldPosition=function()return a.pos end
 a.GetRecordID=function()return "Character.q005_afterlife_mercenary_male" end
 a.GetCurrentAppearanceName=function()return {value=a.app}end
 a.IsNPC=function()return true end;a.IsDead=function()return false end
 a.GetHighLevelStateFromBlackboard=function()return "Relaxed" end
 byid[id]=a;table.insert(entities,a);return a
end
for i=1,4 do make("900719925474099"..i.."ULL",string.format("merc_%02d",i),"merc_01",i==1) end
function CreateEntityReference(c,n)return n[1]end
function GetFixedEntityIdsFromEntityReference(...)
 assert(select('#',...)==1,"CET requires ONE argument")
 getterCalls=getterCalls+1
 local entry=...
 local out={};for _,e in ipairs(entities)do if e.entry==entry then table.insert(out,{hash=e.id})end end
 return out
end
NPCPuppet={IsInCombat=function()return false end}
ScriptedPuppet={IsDefeated=function()return false end}
ws={IsActorInWorkspot=function(self,e)return e.ws end,
 GetExtendedInfo=function()return {isActive=true,entering=false,exiting=true,inMotion=true,inReaction=false}end,
 GetWorkspotInstance=function()return nil end}
inspector={ResolveCommunityEntryDataFromEntityID=function(self,id)
 return {sectorHash=1,communityID={hash="3275354341639988159ULL"},
 entryName={value=byid[id].entry},entryPhase={value="scene1"}}
end}
Game={GetPlayer=function()return p end,GetQuestsSystem=function()return q end,
 GetEntityList=function()return entities end,FindEntityByID=function(id)return byid[id.hash]end,
 GetTargetingSystem=function()return {GetLookAtObject=function()return entities[1]end}end,
 GetWorkspotSystem=function()return ws end,GetWorldInspector=function()return inspector end,
 GetSceneSystem=function()return {GetScriptInterface=function()return {IsEntityInScene=function()return false end}end}end}
''')
    mod = lua.execute(DIAG.read_text()); g = lua.globals(); g.events.onInit()
    for _ in range(4): g.events.onUpdate(8)
    assert len(g.lastrow.actors) == 4
    assert g.getterCalls == 16
    assert all(b.state == 'one_id_resolved' for b in g.lastrow.bindings.values())
    assert all(a.appearance == 'merc_01' for a in g.lastrow.actors.values())
    assert {a.community.entry for a in g.lastrow.actors.values()} == {f'merc_{i:02d}' for i in range(1,5)}
    assert all(a.community.id == '3275354341639988159ULL' and a.community.phase == 'scene1' for a in g.lastrow.actors.values())
    first = g.lastrow.actors[1]
    assert first.workspot_extended.exiting is True and first.errors.workspot_instance == 'unavailable'
    assert g.lastrow.actors[2].classification.startswith('stationary_unowned_candidate')
    lua.execute('Game.GetWorldInspector=function()error("not installed")end')
    g.events.onUpdate(8)
    assert len(g.lastrow.actors) == 4 and all(a.errors.community for a in g.lastrow.actors.values())
    lua.execute('entities[2].GetCurrentAppearanceName=function()error("unsupported")end')
    g.events.onUpdate(8)
    assert g.lastrow.actors[2].appearance == 'UNKNOWN'
    lua.execute('function GetFixedEntityIdsFromEntityReference(...)return {}end')
    g.events.onUpdate(8)
    assert all(b.state == 'UNKNOWN' for b in g.lastrow.bindings.values()) and len(g.lastrow.actors) == 4
    lua.execute('function GetFixedEntityIdsFromEntityReference(...)return {{hash=entities[1].id},{hash=entities[2].id}}end')
    g.events.onUpdate(8)
    assert all(b.state == 'ambiguous' for b in g.lastrow.bindings.values()) and len(g.lastrow.actors) == 4
    g.pos.x = 0
    assert mod.Observe('outside') == 'outside/unloaded' and g.writes == g.closed
    return 13


def snapshot_logs():
    folder = GAME / 'bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_Afterlife_Behavior_Audit'
    result = []
    for name in ('afterlife_behavior_20261005T152826Z.jsonl', 'afterlife_behavior_20261005T154401Z.jsonl'):
        data = (folder / name).read_bytes()
        rows = []; invalid = 0
        for line in data.splitlines():
            try: rows.append(json.loads(line))
            except ValueError: invalid += 1
        timeline = []; previous = None
        for r in rows:
            actors = [{k:a.get(k) for k in ('id','position','in_workspot','in_scene','dead','in_combat','high_level_state')}
                      for a in r['actors'] if a['id'] in {f'1002998{i}ULL' for i in range(4)}]
            facts = {k:v for k,v in r['facts'].items() if k.startswith('PTFRAL3_') or k in ('PTFRAL2_LocalActive','PTFRAL2_Migration')}
            state = dict(actors=actors, facts=facts)
            if state != previous:
                timeline.append(dict(utc=r['utc'], **state)); previous = state
        result.append(dict(file=name,sha256_snapshot=hashlib.sha256(data).hexdigest().upper(),
            bytes_read=len(data),rows=len(rows),invalid_lines=invalid,last_utc=rows[-1]['utc'],
            transitions=timeline,final_actor_ids=[a['id'] for a in rows[-1]['actors']],
            limitation='Existing objects are not proof of rendered visibility. Snapshot may precede later appended rows.'))
    return result


def main():
    OUT.mkdir(exist_ok=True)
    registry_path = BASE / 'patron_vanilla_registry.json'
    ent_path = BASE / 'idles_r3/entry_sources/json/base/quest/main_quests/prologue/q005/afterlife/characters/q005_afterlife_mercenary_male.ent.json'
    registry = read(registry_path)
    community = next(c for c in registry if c['community_index']==3027)
    entity = read(ent_path)['Data']['RootChunk']
    appearances = {a['name']['$value']: a['appearanceName']['$value'] for a in entity['appearances']}
    mappings = []
    for i in range(1,5):
        name = f'merc_{i:02d}'
        e = next(e['data'] for e in community['entries'] if e['name']==name)
        assert e['characterRecordId']['$value']=='Character.q005_afterlife_mercenary_male'
        phases = []
        for p in e['phases']:
            p = p['Data']; assert [a['$value'] for a in p['appearances']]==[name]
            assert len(p['timePeriods'])==1 and p['timePeriods'][0]['quantity']==1
            phases.append(p['phaseName']['$value'])
        assert name in appearances
        mappings.append(dict(entry=name,appearance=name,asset_appearance=appearances[name],phases=phases))
    assert len({m['asset_appearance'] for m in mappings})==4
    text = DRIVER.read_text()
    actual = {k:int(v) for k,v in re.findall(r'q.GetFact\(n"([^"]+)"\) == (\d+)',text)}
    expected = dict(read(BASE/'idles_r3/manifest.json')['guards'], PTFRAL4_Suspended=0)
    assert actual == expected
    assert re.findall(r'BoothAppearanceR4.Create\(n"(merc_\d+)"\)',text)==[m['entry'] for m in mappings]
    assert text.count('npc.ScheduleAppearanceChange(row.entry)')==1
    assert text.index('row.attempted = true;') < text.index('npc.ScheduleAppearanceChange(row.entry)')
    for token in ('ArraySize(ids) != 1', 'row.actor != npc', 'row.attempted',
                  'workspots.IsActorInWorkspot(npc)', 'IsEntityInScene(npc.GetEntityID())',
                  'GetCurrentAppearanceName()', 'gamedataNPCHighLevelState.Relaxed',
                  'row.quiet < 3', 'epoch != this.epoch', '> 36.0', '> 900.0'):
        assert token in text,token
    for forbidden in ('SendCommand','CancelCommand','SetFact','SetFlat','CreateEntity(','Teleport',
                      'ChangeEntryState','ActivateCommunity','GetEntityList'):
        assert forbidden not in text,forbidden
    # Exact source signatures, not inferred method names.
    native = (ROOT/'research/finalboards_dismissal/decompiled/core/entity/entity.script').read_text()
    vanilla = (ROOT/'research/finalboards_dismissal/decompiled/core/ai/actions/aiActionHelperTask.script').read_text()
    assert 'func ScheduleAppearanceChange(newAppearanceName: CName) -> Void' in native
    assert 'ScheduleAppearanceChange(this.m_appearance)' in vanilla
    result = subprocess.run([str(ROOT/'research/finalboards_dismissal/tooling/redscript-cli.exe'),
        'lint','-s',str(DRIVER),'-b',str(GAME/'r6/cache/final.redscripts.modded')],capture_output=True,text=True)
    output = result.stdout+result.stderr
    (OUT/'redscript_lint.log').write_text(output)
    assert result.returncode==0 and 'Lint successful' in output,output
    lua = DIAG.read_text()
    assert not any(x in lua for x in ('SetFact','SendCommand','Teleport','QueueEvent','ActivateCommunity','ChangeEntryState','ScheduleAppearanceChange'))
    lua_cases = lua_tests()
    # Installed packages must remain unchanged, including failed R3 for provenance.
    protected = {}
    for receipt in (BASE/'install_receipt.json',BASE/'population_r2/install_receipt.json',BASE/'idles_r3/install_receipt.json'):
        for f in read(receipt)['files']: protected[f['relative']]=f['sha256']
    for path,expected_hash in protected.items(): assert sha(GAME/path)==expected_hash,path
    logs = snapshot_logs()
    (OUT/'live_r3_evidence.json').write_text(json.dumps(logs,indent=2)+'\n')
    report = dict(status='PARTIAL_APPEARANCE_CANDIDATE_OFFLINE_PASS_NOT_INSTALLED',
        scope='Four original booth entries only; second photographed group still unidentified.',
        source_mappings=mappings,guards=actual,source_sha256={str(p.relative_to(ROOT)):sha(p) for p in (registry_path,ent_path)},
        driver_sha256=sha(DRIVER),diagnostic_sha256=sha(DIAG),redscript_lint=True,lua_mock_checks=lua_cases,
        installed_afterlife_files_unchanged=len(protected),spawn_or_density_changes=0,
        appearance_engine_readback_proven=False,visual_pass=False,routine_fix=False,
        limitation='One bounded repair request, not a guarantee of unique appearance across arbitrary crowd pools.')
    (OUT/'tests.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('source_mappings','guards','source_sha256')},indent=2))


if __name__=='__main__': main()
