"""Independent, offline one-light scope and serial-controller regression tests.

Does not launch the game, change installed files, or claim renderer visibility.
The native simulator tests graph logic, not native callback delivery or atomicity.
"""
import binascii
import copy
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

from audit_world_interactions import walk
from test_radio_memorial import canonical, handles, nodes
from test_streetkid_scene_load_s3 import quest_edges

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'research/misty_viktor_world'
GAME = Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
PREFIX = 'towercontinued\\misty_viktor_light_poc\\'
REF = '$/03_night_city/#PTFRMV_LightPOC01'
OWNER = '$/03_night_city/c_watson/little_china/wlc_02/#wlc_02_b_env'
FACT = 'PTFRMVLP_'
GUARDS = dict(PostTowerFreeRoamActive=1, PTFRP0_DR13=1, q307_active=0,
              q307_done=1, q307_finished=1, q307_2079=1,
              q307_main_game_killed=1, q307_ep1_killed=1,
              q305_johnny_scene_active=0, q115_point_of_no_return=0,
              PTFRBASE_Suspended=0, PTFRWORLD_Suspended=0,
              PTFRMVLP_Enabled=1, PTFRMVLP_Suspended=0, PTFRMVLP_QuestOwns=0)
EDGES = [(0,'Out',1),(1,'Out',2),(2,'Out',3),(3,'Out',4),(4,'Out',5),
         (5,'Out',6),(6,'Out',7),(7,'Out',8),(8,'Out',9),(9,'Out',10),
         (10,'Out',11),(11,'Out',12),(12,'True',13),(12,'False',25),
         (13,'True',14),(14,'Out',15),(15,'Out',16),(16,'Out',17),
         (17,'Out',18),(18,'Out',24),(13,'False',19),(19,'Out',20),
         (20,'Out',21),(21,'Out',22),(22,'Out',23),(23,'Out',24),
         (24,'Out',25),(25,'True',11),(25,'False',26),(26,'Out',27),
         (27,'Out',28),(28,'Out',29),(29,'Out',30),(30,'Out',7)]
INPUTS = set()


def used(path):
    path = Path(path).resolve()
    path.relative_to(ROOT)
    INPUTS.add(path)
    return path


def read(path):
    return json.loads(used(path).read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(used(path).read_bytes()).hexdigest().upper()


def root(name):
    return read(BASE / name)['Data']['RootChunk']


def evaluate(c, facts, resident):
    if c['$type'] == 'questNodeLoadingCondition':
        assert c['objectRef'] == {'$type':'NodeRef','$storage':'string','$value':REF}
        assert c['inverted'] in (0, 1)
        return bool(resident) != bool(c['inverted'])
    if c['$type'] == 'questLogicalCondition':
        assert c['operation'] in ('AND', 'OR')
        values = [evaluate(v, facts, resident) for v in c['conditions']]
        return all(values) if c['operation'] == 'AND' else any(values)
    assert c['$type'] == 'questFactsDBCondition'
    t = c['type']
    assert t['$type'] == 'questVarComparison_ConditionType'
    assert t['comparisonType'] in ('Equal', 'NotEqual')
    equal = facts.get(t['factName'], 0) == t['value']
    return equal if t['comparisonType'] == 'Equal' else not equal


def test_world(m):
    wm = read(Path(m['world_manifest']))
    assert sha(Path(m['world_manifest'])) == m['world_manifest_sha256']
    assert wm['source_data_index'] == 3907 and wm['source_node_index'] == 3368
    assert wm['private_ref'] == REF and wm['variant_name'] == 'PTFRMV_LightPOC'
    assert wm['variant_owner'] == OWNER and wm['variant_id'] == 3980092801
    assert wm['nodes'] == wm['placements'] == wm['static_lights'] == 1
    assert all(wm[k] == 0 for k in ('entities','meshes','collisions','triggers',
                                   'scene_starts','sector_auxiliary_payloads','original_resource_overrides'))
    original = root('r7_lighting_sources/base/worlds/03_night_city/_compiled/default/exterior_-25_18_0_0.streamingsector.json')
    exported = read(BASE / 'light_poc_world_sector.json')
    world = exported['Data']['RootChunk']
    assert exported['Data']['EmbeddedFiles'] == []
    assert len(world['nodes']) == len(world['nodeData']['Data']) == 1
    before = original['nodes'][3368]['Data']
    expected = copy.deepcopy(before)
    expected['debugName']['$value'] = 'PTFRMV_LightPOC01'
    expected['sourcePrefabHash'] = '0'
    assert world['nodes'][0]['Data'] == expected
    assert expected['$type'] == 'worldStaticLightNode' and expected['type'] == 'LT_Point'
    assert (expected['intensity'],expected['radius'],expected['EV']) == (25,3,1.5)
    before = original['nodeData']['Data'][3907]
    actual = world['nodeData']['Data'][0]
    assert before['NodeIndex'] == 3368 and before['QuestPrefabRefHash']['$value'] == '0'
    expected = copy.deepcopy(before)
    for component in ('Position','Pivot'):
        for axis, delta in zip('XYZ',wm['translation']):
            assert abs(actual[component][axis] - (before[component][axis]+delta)) < .00015
            expected[component][axis] = actual[component][axis]
    for corner in ('Min','Max'):
        for axis, delta in zip('XYZ',wm['translation']):
            assert abs(actual['Bounds'][corner][axis] - (before['Bounds'][corner][axis]+delta)) < .00015
            expected['Bounds'][corner][axis] = actual['Bounds'][corner][axis]
    expected.update(Id='750000000008001', NodeIndex=0,
                    QuestPrefabRefHash={'$type':'NodeRef','$storage':'string','$value':REF})
    assert actual == expected
    assert all(abs(actual['Position'][axis]-value)<.00002 for axis,value in
               zip('XYZ',(-1570.2421875,1210.5838623,17.5439548)))
    assert world['nodeRefs'] == [expected['QuestPrefabRefHash']]
    assert world['persistentNodes'] == world['localInplaceResource'] == []
    assert world['externInplaceResource']['DepotPath']['$value'] == '0'
    assert world['persistentNodeIndex'] == 0
    assert world['variantIndices'] == [0,0] and all(v == [] for v in world['variantNodes'])
    assert [o for o in walk(world) if 'BufferId' in o] == [world['nodeData']]
    blockfile = read(BASE / 'light_poc_world_block.json')
    block = blockfile['Data']['RootChunk']
    assert blockfile['Data']['EmbeddedFiles'] == [] and len(block['descriptors']) == 1
    d = block['descriptors'][0]
    assert d['data']['DepotPath']['$value'] == PREFIX+'light_poc.streamingsector'
    assert d['level'] == 0 and d['category'] == 'Exterior' and d['numNodeRanges'] == 2
    assert d['variants'] == [{'$type':'worldStreamingSectorVariant','enabledByDefault':0,
        'name':{'$type':'CName','$storage':'string','$value':'PTFRMV_LightPOC'},
        'nodeRef':{'$type':'NodeRef','$storage':'string','$value':OWNER},
        'parentVariantID':0,'rangeIndex':1,'variantId':3980092801}]
    assert wm['ranges'] == [{'count':0,'index':0,'start':0},{'count':1,'index':1,'start':0}]
    for axis in 'XYZ':
        assert d['streamingBox']['Min'][axis] <= actual['Position'][axis] <= d['streamingBox']['Max'][axis]
    for depot, key in zip(wm['resources'], ('sector_sha256','block_sha256')):
        src = Path(wm['source_root']) / depot
        packaged = Path(m['source_root']) / depot
        assert sha(src) == sha(packaged) == wm[key]
    return wm


class Simulator:
    """Serialized graph runner; pause nodes wait until their condition is true."""
    def __init__(self, nn):
        self.nodes, self.pc = nn, 0
        self.facts, self.resident, self.actions = dict(GUARDS), False, []
        self.edges = {(a,s):b for a,s,b in EDGES}
        self.run()
        assert self.pc == 7 and self.facts[FACT+'Enabled'] == 0

    def run(self, stop_before=None):
        for _ in range(100):
            if self.pc == stop_before:
                return
            n = self.nodes[self.pc]
            kind = n['$type']
            socket = 'Out'
            if kind in ('questPauseConditionNodeDefinition','questConditionNodeDefinition'):
                truth = evaluate(n['condition'],self.facts,self.resident)
                if kind == 'questPauseConditionNodeDefinition':
                    if not truth:
                        return
                else:
                    socket = 'True' if truth else 'False'
            elif kind == 'questFactsDBManagerNodeDefinition':
                t = n['type']
                self.facts[t['factName']] = t['value'] + (0 if t['setExactValue'] else self.facts.get(t['factName'],0))
            elif kind == 'questWorldDataManagerNodeDefinition':
                t = n['type']
                if t['$type'] == 'questShowWorldNode_NodeType':
                    assert self.resident and all(self.facts[k] == v for k,v in GUARDS.items())
                    assert self.facts[FACT+'DesiredVisible'] == t['show']
                    self.actions.append(('visibility',t['show']))
                else:
                    self.actions.append(('variant',t['params'][0]['variantStates'][0]['show']))
            else:
                assert kind == 'questInputNodeDefinition'
            self.pc = self.edges[self.pc,socket]
        raise AssertionError('Graph does not settle at one wait (possible busy loop)')

    def start(self, resident=False):
        self.resident = resident
        self.facts[FACT+'DesiredVisible'] = 1
        self.facts[FACT+'Enabled'] = 1
        self.run()

    def released(self):
        assert self.pc == 7 and self.actions[-1] == ('variant',0)
        assert all(self.facts[FACT+k] == 0 for k in ('Enabled','Applied','Ready'))


def test_native(m):
    phase = root('light_poc_phase.json')
    h, raw = handles(phase), nodes(phase)
    nn = {i:canonical(n,h) for i,n in raw.items()}
    assert set(nn) == set(range(31)) and phase['phasePrefabs'] == []
    for obj in walk(phase):
        if 'HandleRefId' in obj:
            assert str(obj['HandleRefId']) in h
    actual_edges = quest_edges(phase)[0]
    assert actual_edges == {(a,s,b,'In') for a,s,b in EDGES}
    assert len({(a,s) for a,s,b in EDGES}) == len(EDGES)
    assert m['edges'] == [list(e) for e in EDGES]
    assert m['guards'] == GUARDS and len(GUARDS) == 15
    factspec = {1:('Registered',1,1),2:('Revision',1,1),3:('Applied',0,1),
        4:('Ready',0,1),5:('Enabled',0,1),6:('DesiredVisible',1,1),
        9:('Acquires',1,0),10:('Applied',1,1),15:('ShowRequests',1,0),
        16:('LastRequested',1,1),17:('Ready',1,1),20:('HideRequests',1,0),
        21:('LastRequested',0,1),22:('Ready',1,1),24:('Ready',0,1),
        27:('Releases',1,0),28:('Applied',0,1),29:('Ready',0,1),30:('Enabled',0,1)}
    for i,(fact,value,exact) in factspec.items():
        assert nn[i]['$type'] == 'questFactsDBManagerNodeDefinition'
        assert nn[i]['type'] == {'$type':'questSetVar_NodeType','factName':FACT+fact,
                                 'value':value,'setExactValue':exact}
    assert {n['id'] for n in nn.values() if n['$type']=='questFactsDBManagerNodeDefinition'} == set(factspec)
    assert nn[0]['$type'] == 'questInputNodeDefinition' and nn[0]['socketName']['$value'] == 'In1'
    for i in (7,11,18,23):
        assert nn[i]['$type'] == 'questPauseConditionNodeDefinition'
    for i in (12,13,25):
        assert nn[i]['$type'] == 'questConditionNodeDefinition'
    proof = read(BASE / 'r7_showworld_static_light_proof.json')
    assert proof['target']['node']['$type'] == 'worldStaticLightNode'
    for i, show in ((14,1),(19,0)):
        assert nn[i]['$type'] == 'questWorldDataManagerNodeDefinition'
        source = copy.deepcopy(next(a['action'] for a in proof['actions'] if a['action']['show']==show))
        source['objectRef']['$value'] = REF
        assert nn[i]['type'] == source
    for i, show in ((8,1),(26,0)):
        assert nn[i]['$type'] == 'questWorldDataManagerNodeDefinition'
        t = nn[i]['type']
        assert t['$type'] == 'questTogglePrefabVariant_NodeType' and len(t['params']) == 1
        assert t['params'][0] == {'$type':'questTogglePrefabVariant_NodeTypeParams',
            'prefabNodeRef':{'$type':'NodeRef','$storage':'string','$value':OWNER},
            'variantStates':[{'$type':'questVariantState',
                'name':{'$type':'CName','$storage':'string','$value':'PTFRMV_LightPOC'},'show':show}]}
    assert {n['id'] for n in nn.values() if n['$type']=='questWorldDataManagerNodeDefinition'} == {8,14,19,26}
    assert {o['factName'] for o in walk(phase) if o.get('$type')=='questSetVar_NodeType'} == {FACT+v[0] for v in factspec.values()}
    guard = nn[7]['condition']
    facts = GUARDS | {FACT+'DesiredVisible':1}
    assert evaluate(guard,facts,False) and not evaluate(nn[11]['condition'],facts,False)
    assert evaluate(nn[11]['condition'],facts,True) and evaluate(nn[12]['condition'],facts,True)
    cases = 0
    negatives = [(key,bad) for key,value in GUARDS.items() for bad in (-1,0,1,2) if bad!=value]
    assert len(negatives) == 45
    negatives += [(FACT+'DesiredVisible',v) for v in (-1,2)]
    for key,bad in negatives:
        state = facts | {key:bad}
        for resident in (False,True):
            assert not evaluate(guard,state,resident)
            assert not evaluate(nn[12]['condition'],state,resident)
            assert not evaluate(nn[25]['condition'],state,resident)
            for pause in (11,18,23):
                assert evaluate(nn[pause]['condition'],state,resident)
                cases += 1
        for waiting in (11,18,23):
            s = Simulator(nn);s.start(waiting != 11)
            if waiting == 23:
                s.facts[FACT+'DesiredVisible']=0;s.run()
            assert s.pc == waiting
            before = len([a for a in s.actions if a[0]=='visibility'])
            s.facts[key] = bad;s.run();s.released()
            assert len([a for a in s.actions if a[0]=='visibility']) == before
    s = Simulator(nn);s.start();assert s.pc==11 and s.actions==[('variant',1)]
    s.facts[FACT+'Enabled']=0;s.run();s.released()
    s = Simulator(nn);s.start(True);assert s.pc==18 and s.actions==[('variant',1),('visibility',1)]
    s.run();assert len(s.actions)==2
    s.facts[FACT+'DesiredVisible']=0;s.run();assert s.pc==23 and s.actions[-1]==('visibility',0)
    s.run();assert len(s.actions)==3
    for visible in (0,1):
        s.facts[FACT+'DesiredVisible']=visible;s.run()
        s.resident=False;s.run();assert s.pc==11 and s.facts[FACT+'Ready']==0
        before=len(s.actions)
        s.facts[FACT+'DesiredVisible']=1-visible;s.run();assert len(s.actions)==before
        s.resident=True;s.run();assert s.actions[-1]==('visibility',1-visible)
    for checkpoint in (12,25):
        s=Simulator(nn);s.start();s.resident=True
        s.run(stop_before=checkpoint) if checkpoint==12 else None
        if checkpoint==25:
            s.run();s.resident=False;s.run(stop_before=25)
        assert s.pc==checkpoint
        s.facts['q307_active']=1;s.run();s.released()
    return {'negative_guards':45,'invalid_desired_values':2,'condition_cases':cases,
            'wait_invalidation_routes':141,'native_nodes':31,'edges':len(EDGES)}


def test_lua(m):
    sys.path.insert(0,str(ROOT/'research/phase2b_p0/tooling/python'))
    from lupa.lua51 import LuaRuntime
    source = used(Path(m['probe'])).read_text(encoding='utf-8-sig')
    assert set(re.findall(r'SetFactStr\("([^"]+)"',source)) == {FACT+'Enabled',FACT+'DesiredVisible'}
    assert not any(x in source for x in ('NewObject','TogglePrefab','QueueEvent','ExecuteQuest','Teleport(','SetTime','SetEntryState'))
    setup = '''events={};writes={};rows={};f={};noPlayer=false;noQuests=false;failOpen=false;failWrite=false
    pos={x=-1570.2421875,y=1210.5838623,z=16.9989319}
    function print(...)end
    function registerForEvent(n,cb)events[n]=cb end
    function IsDefined(x)return x~=nil end
    json={encode=function(row)rows[#rows+1]=row;return '{}' end}
    io={open=function(n,mode)
      if mode=='r' or failOpen then return nil end
      return {write=function(self)if failWrite then return nil,'disk full' end;return self end,
        flush=function()return true end,close=function()return true end}end}
    q={GetFactStr=function(self,k)return f[k] or 0 end,
       SetFactStr=function(self,k,v)f[k]=v;writes[#writes+1]={k,v}end}
    player={GetWorldPosition=function()return pos end}
    Game={GetQuestsSystem=function()if not noQuests then return q end end,
          GetPlayer=function()if not noPlayer then return player end end}'''
    def fresh():
        lua=LuaRuntime(unpack_returned_tuples=True);lua.execute(setup)
        mod=lua.execute(source);f=lua.globals().f
        for k,v in GUARDS.items():f[k]=v
        f.PTFRMVLP_Enabled=0;f.PTFRMVLP_Registered=1;f.PTFRMVLP_Revision=1
        return lua,mod,f
    negatives=0
    for key,value in GUARDS.items():
        if key==FACT+'Enabled':continue
        for bad in (-1,0,1,2):
            if bad==value:continue
            lua,mod,f=fresh();f[key]=bad
            mod.Start();assert len(lua.globals().writes)==0
            f.PTFRMVLP_Enabled=1
            mod.Show();mod.Hide();assert len(lua.globals().writes)==0
            mod.Stop();assert f.PTFRMVLP_Enabled==0 and len(lua.globals().writes)==1
            negatives+=1
    for key in ('Registered','Revision'):
        for bad in (-1,0,2):
            lua,mod,f=fresh();f[FACT+key]=bad;mod.Start();assert len(lua.globals().writes)==0
    for mutation in ('noPlayer=true','noQuests=true','pos.x=pos.x+30','pos.z=pos.z+6','failOpen=true','failWrite=true'):
        lua,mod,f=fresh();lua.execute(mutation);mod.Start();assert len(lua.globals().writes)==0,mutation
    lua,mod,f=fresh()
    lua.globals().events.onUpdate(25);mod.Inspect();mod.Show();mod.Hide();mod.Finish()
    assert len(lua.globals().writes)==0
    mod.Start();mod.Start();mod.Show();assert len(lua.globals().writes)==2
    mod.Hide();mod.Hide();assert len(lua.globals().writes)==3 and f.PTFRMVLP_DesiredVisible==0
    mod.Show();mod.Show();assert len(lua.globals().writes)==4
    lua.globals().events.onUpdate(21);lua.globals().events.onUpdate(600)
    assert len(lua.globals().writes)==4 and f.PTFRMVLP_Enabled==1
    mod.Finish();lua.globals().events.onShutdown();assert len(lua.globals().writes)==4
    lua.execute('noPlayer=true;pos.x=0');f.q307_active=1
    mod.Stop();mod.Stop();assert len(lua.globals().writes)==5 and f.PTFRMVLP_Enabled==0
    lua.execute('noQuests=true');mod.Stop();assert len(lua.globals().writes)==5
    assert all(lua.globals().writes[i][1] in (FACT+'Enabled',FACT+'DesiredVisible') for i in range(1,6))
    return {'lua_runtime':'Lua 5.1','lua_guard_negatives':negatives,
            'lua_world_actions':0,'lua_write_allowlist':[FACT+'Enabled',FACT+'DesiredVisible']}


def test_archive_and_registration(m):
    resources = [PREFIX+'light_poc.streamingsector',PREFIX+'light_poc.streamingblock',PREFIX+'light_poc.questphase']
    assert m['resources']==resources
    src=Path(m['source_root'])
    assert sorted(str(p.relative_to(src)) for p in src.rglob('*') if p.is_file())==sorted(resources)
    for path in src.rglob('*'):
        if path.is_file():used(path)
    assert sha(Path(m['archive']))==m['sha256']
    assert sha(Path(m['archive']+'.xl'))==m['xl_sha256']
    assert sha(Path(m['probe']))==m['probe_sha256']
    expectedxl=['streaming:','  blocks:','    - '+resources[1],'quest:','  phases:',
        '    - path: '+resources[2],'      parent: ep1\\quest\\ep1.quest','      input:',
        '        node: [1]','        socket: Out']
    assert Path(m['archive']+'.xl').read_text(encoding='utf-8-sig').splitlines()==expectedxl
    crc=binascii.crc_hqx((resources[2]+':1').encode(),65535)
    assert crc==m['registration_id']==16426
    collision_checked=0
    for path in (GAME/'archive/pc/mod').glob('*.xl'):
        # Installed XL is read-only external evidence, separately inventoried.
        for registered in re.findall(r'path:\s*([^\s#]+\.questphase)',path.read_text(encoding='utf-8-sig')):
            assert binascii.crc_hqx((registered+':1').encode(),65535)!=crc,(path,registered)
            collision_checked+=1
    # Reopen the packed archive and compare every payload byte hash to source.
    # No extraction to disk and no game state changes.
    code = r'''$ErrorActionPreference='Stop'
    . ./tools/build_phase2a.ps1 -HelpersOnly
    $m=Get-Content ./research/misty_viktor_world/light_poc_manifest.json -Raw|ConvertFrom-Json
    $hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$ar=$null
    if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($m.archive,$hs,[ref]$ar).ToString() -ne 'NoError'){throw 'Packed archive cannot reopen'}
    if($ar.Files.Count -ne 3){throw 'Packed archive payload count changed'}
    foreach($f in $ar.Files.Values){
      if($f.Name -notin $m.resources){throw ('Extra packed payload '+$f.Name)}
      $ms=[IO.MemoryStream]::new()
      try{$f.Extract($ms);$digest=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($ms.ToArray()))}finally{$ms.Dispose()}
      if($digest -ne (Get-FileHash -LiteralPath (Join-Path $m.source_root $f.Name)).Hash){throw ('Packed bytes differ '+$f.Name)}
    }
    $p=Read-Cr2wFile ./research/q307_extracted/raw/ep1/quest/ep1.quest
    if(@($p.RootChunk.Graph.Chunk.Nodes|Where-Object {$_.Chunk.Id.ToString() -eq '16426'}).Count){throw 'Native parent registration collision'}
    Write-Output 'PACKED_EXACT_THREE_PAYLOADS_AND_NATIVE_REGISTRATION_PASS'
    '''
    result=subprocess.run(['pwsh','-NoProfile','-Command',code],cwd=ROOT,text=True,capture_output=True)
    assert result.returncode==0,(result.stdout,result.stderr)
    assert 'PACKED_EXACT_THREE_PAYLOADS_AND_NATIVE_REGISTRATION_PASS' in result.stdout
    used(ROOT/'research/q307_extracted/raw/ep1/quest/ep1.quest')
    return {'packed_payloads_verified':3,'installed_registration_ids_checked':collision_checked}


def main():
    m=read(BASE/'light_poc_manifest.json')
    assert m['status']=='BUILT_LIGHT_POC_NOT_INSTALLED_OR_LIVE'
    assert m['node_ref']==REF and m['variant_owner']==OWNER and m['private_variant']=='PTFRMV_LightPOC'
    assert m['native_nodes']==31 and m['single_serial_controller'] is True
    assert all(m[k]==0 for k in ('original_world_resource_overrides','original_lighting_changes','story_fact_writes','scene_starts'))
    test_world(m)
    results=test_native(m)|test_lua(m)|test_archive_and_registration(m)
    for name in ('tools/test_misty_light_poc.py','tools/install_misty_light_poc.ps1',
                 'tools/build_misty_light_poc.ps1','tools/build_misty_light_poc_world.ps1',
                 'tools/build_phase2a.ps1','tools/audit_world_interactions.py',
                 'tools/test_radio_memorial.py','tools/test_streetkid_scene_load_s3.py',
                 'tools/audit_scene_actor_ids.py'):
        used(ROOT/name)
    # Freeze the complete tested workspace input set; report itself is not an input.
    hashes={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest().upper()
            for p in sorted(INPUTS)}
    report={'status':'PASS_LIGHT_POC_OFFLINE_NOT_LIVE',
        'archive_sha256':m['sha256'],'xl_sha256':m['xl_sha256'],'probe_sha256':m['probe_sha256'],
        'manifest_sha256':sha(BASE/'light_poc_manifest.json'),'input_hashes':hashes,
        'private_static_lights':1,'original_resource_overrides':0,'story_fact_writes':0,
        'scene_starts':0,'live_tested':False,
        'not_proven':['actual renderer visibility','live streaming callback delivery',
                      'save/reload of a mid-test graph (not permitted by disposable test)'],**results}
    (BASE/'light_poc_tests.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='input_hashes'},indent=2))


if __name__=='__main__':
    main()
