"""R3 source fidelity, guard/stream scheduler and read-only audit tests.

These are offline contracts, not proof that an engine command animates an NPC.
"""
import binascii
import copy
import itertools
import json
import re
import subprocess
import sys
from pathlib import Path

from audit_world_interactions import walk
from test_afterlife_population_r2 import Model, graph
from test_misty_viktor_access_r10 import read, sha as path_sha
from test_radio_memorial import canonical, handles, nodes

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'research/afterlife_world/idles_r3'
GAME = Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')

def sha(path):
    return path_sha(Path(path))


class Readiness(Model):
    def settle(self, before=None):
        for _ in range(1000):
            progress = False
            for i in sorted(self.pending):
                if i == before:
                    return
                n = self.nn[i]; kind = n['$type']; socket = 'Out'
                if kind == 'questPauseConditionNodeDefinition':
                    if not self.condition(n['condition']):
                        continue
                elif kind == 'questConditionNodeDefinition':
                    socket = 'True' if self.condition(n['condition']) else 'False'
                elif kind == 'questFactsDBManagerNodeDefinition':
                    p = n['type']; assert p['factName'].startswith('PTFRAL3_')
                    self.f[p['factName']] = p['value']
                elif kind == 'questWorldDataManagerNodeDefinition':
                    for p in n['type']['params']:
                        assert p['$type'] == 'questTogglePrefabVariant_NodeTypeParams'
                        assert len(p['variantStates']) == 1
                        self.log.append((i, p['variantStates'][0]['show']))
                else:
                    assert kind == 'questInputNodeDefinition', kind
                self.pending.remove(i)
                self.pending.update(self.edges[i, socket]); progress = True
            if not progress:
                return
        raise AssertionError('non-settling graph')


def lua_audit_test(source):
    sys.path.insert(0, str(ROOT / 'research/phase2b_p0/tooling/python'))
    from lupa.lua51 import LuaRuntime
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute('''
events={}; lines={}; prints={}; entities={}; byid={}; closes=0
function registerForEvent(k,f) events[k]=f end
function Observe(a,b,f) attached=f end
function IsDefined(v) return type(v)=="table" end
function print(s) table.insert(prints,s) end
json={encode=function(row) lastrow=row;return "{}" end}
io={open=function() return {write=function(self,s)table.insert(lines,s);return self end,
close=function()closes=closes+1;return true end} end}
CName={new=function(s)return s end}
pos={x=-1440,y=1013,z=17};p={GetWorldPosition=function()return pos end,GetGame=function()return {} end}
q={GetFactStr=function()return 1 end}
function make(id,ws,scene)
 local a={id=id,pos={x=-1424,y=1023,z=17},ws=ws,scene=scene,dead=false,combat=false,defeated=false}
 a.GetEntityID=function()return {hash=id}end;a.GetWorldPosition=function()return a.pos end
 a.GetRecordID=function()return "Character.q005_afterlife_mercenary_male" end
 a.IsNPC=function()return true end;a.IsDead=function()return a.dead end
 a.GetHighLevelStateFromBlackboard=function()return "Relaxed" end
 byid[id]=a;table.insert(entities,a);return a
end
for i=1,4 do make("123456789012345678"..i.."ULL",false,false) end
work=make("50ULL",true,false);scene=make("51ULL",false,true);moving=make("52ULL",false,false)
target=entities[1]
function CreateEntityReference(c,n)return n[1]end
function GetFixedEntityIdsFromEntityReference(ref,game)return {} end
NPCPuppet={IsInCombat=function(e)return e.combat end}
ScriptedPuppet={IsDefeated=function(e)return e.defeated end}
Game={GetPlayer=function()return p end,GetQuestsSystem=function()return q end,
GetEntityList=function()return entities end,FindEntityByID=function(id)return byid[id.hash]end,
GetTargetingSystem=function()return {GetLookAtObject=function()return target end}end,
GetWorkspotSystem=function()return {IsActorInWorkspot=function(self,e)return e.ws end,
GetWorkspotInstance=function()return {animName="sit_idle",idleAnim="sit"}end}end,
GetSceneSystem=function()return {GetScriptInterface=function()return {
IsEntityInScene=function(self,id)return byid[id.hash].scene end}end}end}
''')
    mod = lua.execute(source); g = lua.globals(); g.events.onInit()
    for _ in range(4):
        g.moving.pos.x += 1
        g.events.onUpdate(8)
    actors = {a['id']: a for a in g.lastrow.actors.values()}
    assert len(actors) == 7  # Same records never collapse distinct actor IDs.
    assert len(g.lastrow.errors) == 0
    assert all(actors[f'123456789012345678{i}ULL']['classification'].startswith('stationary_unowned_candidate') for i in range(1,5))
    assert actors['50ULL']['classification'] == 'workspot_active'
    assert actors['51ULL']['classification'] == 'scene_owned'
    assert actors['52ULL']['classification'] == 'moving_or_transitioning'
    assert g.lastrow.bindings[1].state == 'UNKNOWN'
    assert g.lastrow.coverage.complete_census_proven is False
    lua.execute('entities={};Game.GetEntityList=function()error("unavailable")end')
    g.events.onUpdate(8)
    assert g.lastrow.errors.entity_list and len(g.lastrow.actors) == 7
    lua.execute('byid["50ULL"]=nil;target=nil')
    g.events.onUpdate(8)
    assert len(g.lastrow.actors) == 6
    lua.execute('newActor=make("9007199254740993ULL",false,false);attached(newActor)')
    g.events.onUpdate(8)
    assert any(a.id == '9007199254740993ULL' for a in g.lastrow.actors.values())
    lua.execute('newActor.IsDead=function()error("missing")end')
    g.events.onUpdate(8)
    a = next(a for a in g.lastrow.actors.values() if a.id == '9007199254740993ULL')
    assert a.dead == 'UNKNOWN' and a.classification == 'unknown'
    g.pos.x = 0
    assert mod.Observe('outside') == 'outside/unloaded'
    assert len(g.lines) == g.closes
    return 11


def main():
    m = read(OUT / 'manifest.json')
    assert sha(m['archive']) == m['sha256'] and sha(m['archive']+'.xl') == m['xl_sha256']
    assert m['packed_readback_pass'] and m['spawn_actions'] == m['new_actor_identities'] == m['original_overrides'] == 0
    for p,h in m['source_hashes'].items():
        assert sha(ROOT / p) == h, p
    root, nn, edges = graph(OUT / 'readiness.questphase.json')
    assert len(nn) == m['native_nodes'] == 34
    assert not root['phasePrefabs']
    assert not any('Spawn' in o.get('$type','') or 'Scene' in o.get('$type','') for o in walk(root))
    guards = m['guards']; refs = {r['private_ref']: True for r in m['entries']}
    def simulate(facts=None, loaded=None):
        s = Readiness(nn, edges, facts or guards, refs if loaded is None else loaded, {})
        s.settle(); return s
    s = simulate()
    assert s.log == [(12, 1)]
    assert all(s.f[r['ready_fact']] == 1 for r in m['entries'])
    negatives = 0
    for k,v in guards.items():
        for bad in {-1,0,1,2,3}-{v}:
            assert not simulate(dict(guards,**{k:bad})).log
            s = simulate(); s.f[k] = bad; s.settle()
            assert s.log[-1] == (15,0) and all(s.f[r['ready_fact']]==0 for r in m['entries'])
            s.f[k] = v; s.settle()
            assert s.log[-1] == (12,1) and all(s.f[r['ready_fact']]==1 for r in m['entries'])
            negatives += 1
    for values in itertools.product((False,True),repeat=4):
        loaded = dict(zip(refs,values)); s=simulate(loaded=loaded)
        assert [s.f[r['ready_fact']] for r in m['entries']] == list(values)
        s.loaded=dict.fromkeys(refs,False);s.settle()
        assert all(s.f[r['ready_fact']]==0 for r in m['entries'])
        s.loaded=dict.fromkeys(refs,True);s.settle()
        assert all(s.f[r['ready_fact']]==1 for r in m['entries'])
    # Guard/stream changes between the wait and its recheck cannot publish ready.
    races = 0
    for k,v in guards.items():
        for i,r in enumerate(m['entries']):
            s=Readiness(nn,edges,guards,refs,{});s.settle(before=101+10*i)
            s.f[k]=v+1;s.settle();assert s.f[r['ready_fact']]==0;races+=1
    # Exact geometry, workspot resource, orientation and non-identity settings.
    src = read(ROOT / 'research/afterlife_world/patron_world_sources/json/base/worlds/03_night_city/_compiled/default/quest_9da2b9328cb64d35.streamingsector.json')['Data']['RootChunk']
    dst = read(OUT/'spots.streamingsector.json')['Data']['RootChunk']
    assert len(dst['nodes']) == len(dst['nodeData']['Data']) == 4
    assert dst['variantIndices'] == [0,0]
    hs, hd = handles(src), handles(dst)
    for i,r in enumerate(m['entries']):
        a=canonical(src['nodes'][r['source_node']],hs);b=canonical(dst['nodes'][i],hd)
        for key in ('sourcePrefabHash','debugName'): a.pop(key);b.pop(key)
        assert a==b, r['entry']
        a=next(copy.deepcopy(x) for x in src['nodeData']['Data'] if x['NodeIndex']==r['source_node'])
        b=copy.deepcopy(dst['nodeData']['Data'][i])
        for key in ('Id','NodeIndex','QuestPrefabRefHash','UkHash1'):a.pop(key);b.pop(key)
        assert a==b, r['entry']
    reg=read(OUT/'registry.streamingsector.json')['Data']['RootChunk']
    assert len(reg['nodes'])==1 and not reg['nodes'][0]['Data']['communitiesData']
    assert len(reg['nodes'][0]['Data']['workspotsPersistentData'])==4
    b=read(OUT/'world.streamingblock.json')['Data']['RootChunk']
    assert b['descriptors'][1]['variants'][0]['enabledByDefault']==0
    assert b['descriptors'][1]['variants'][0]['name']['$value']==m['variant']
    assert all(p.startswith('towercontinued\\afterlife_idles_r3\\') for p in m['resources'])
    driver=ROOT/'redscript/PTFR_Afterlife_Idles_R3/AfterlifeIdlesR3.reds'; text=driver.read_text()
    guard_text=text.split('private func Allowed')[1].split('private func Count')[0]
    actual=dict((k,int(v)) for k,v in re.findall(r'q.GetFact\(n"([^"]+)"\) == (\d+)',guard_text))
    assert actual==dict(guards,PTFRAL3_WorldApplied=1)
    assert text.count('ai.SendCommand(command)')==text.count('ai.CancelCommand(this.command)')==1
    assert not any(x in text for x in ['ActivateCommunity','SetCommunityPhase','CreateEntity(','Teleport','SetAnimation','SetFact(n"q'])
    assert text.count('q.SetFact(')==1 and all(x.startswith('PTFRAL3_') for x in re.findall(r'this.Count\(q, n"([^"]+)"',text))
    for r in m['entries']:
        assert r['community'] in text and r['private_ref'] in text and r['ready_fact'] in text
    for term in ['ArraySize(ids) != 1','row.requests >= 3','row.quiet < 5','row.age < 20',
                 'GetFixedEntityIdsFromEntityReference','moveToWorkspot = true','jumpToEntry = false',
                 'continueInCombat = false','IsEntityInScene','IsActorInWorkspot','IsDead()',
                 'IsDefeated','gamedataNPCHighLevelState.Relaxed','> 9.0','epoch != this.epoch']:
        assert term in text,term
    lint=subprocess.run([str(ROOT/'research/finalboards_dismissal/tooling/redscript-cli.exe'),'lint','-s',str(driver),'-b',str(GAME/'r6/cache/final.redscripts.modded')],capture_output=True,text=True)
    output=lint.stdout+lint.stderr;(OUT/'redscript_lint.log').write_text(output)
    assert lint.returncode==0 and 'Lint successful' in output,output
    diagnostic=ROOT/'diagnostics/PTFR_Afterlife_Behavior_Audit/init.lua';lua=diagnostic.read_text()
    assert not any(x in lua for x in ['SetFact','SendCommand','Teleport','QueueEvent','ActivateCommunity','ChangeEntryState'])
    lua_cases=lua_audit_test(lua)
    rid=binascii.crc_hqx((m['resources'][3]+':1').encode(),65535)
    parent=read(ROOT/'research/q307_extracted/json/ep1/quest/ep1.quest.json')['Data']['RootChunk']
    assert rid not in nodes(parent)
    peers=[]
    for xl in (GAME/'archive/pc/mod').glob('*.archive.xl'):
        for depot in re.findall(r'- path: ([^\r\n]+)\s+parent: ep1\\quest\\ep1.quest\s+input:\s+node: \[1\]',xl.read_text(encoding='utf-8-sig')):
            peers.append(depot);assert binascii.crc_hqx((depot+':1').encode(),65535)!=rid
    # Verify preservation against receipts, not only our expected new payloads.
    old=read(ROOT/'research/afterlife_world/install_receipt.json')['files']
    r2=read(ROOT/'research/afterlife_world/population_r2/install_receipt.json')['files']
    accepted={x['relative']:x['sha256'] for x in old+r2}
    for p,h in accepted.items():assert sha(GAME/p)==h,p
    result=dict(status='PASS_R3_OFFLINE_NOT_INSTALLED_NOT_LIVE',native_nodes=len(nn),
        guard_negative_release_rearm=negatives,stream_cases=16,wait_recheck_races=races,
        exact_source_workspots=4,new_npcs=0,spawn_actions=0,redscript_lint=True,
        runtime_contracts_checked=True,runtime_engine_execution_proven=False,
        lua_mock_cases=lua_cases,registration_id=rid,peer_registrations_checked=len(peers),
        protected_accepted_afterlife_files=len(accepted),archive_sha256=m['sha256'],xl_sha256=m['xl_sha256'],
        manifest_sha256=sha(OUT/'manifest.json'),builder_sha256=sha(ROOT/'tools/build_afterlife_idles_r3.ps1'),
        validator_sha256=sha(Path(__file__)),driver_sha256=sha(driver),diagnostic_sha256=sha(diagnostic))
    (OUT/'tests.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
