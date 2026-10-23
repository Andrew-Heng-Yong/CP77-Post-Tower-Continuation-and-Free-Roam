"""Source/graph and LuaJIT checks. Not a substitute for native gameplay tests."""
import hashlib, json, re, sys, zlib
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'research/gig_restoration/pilot_r1'
sys.path.insert(0,str(ROOT/'research/phase2b_p0/tooling/python'))
from lupa.luajit21 import LuaRuntime
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def load(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
class Resource:
    def __init__(self,obj):
        self.obj=obj;self.handles={}
        def walk(v):
            if isinstance(v,dict):
                if 'HandleId' in v and 'Data' in v: self.handles[v['HandleId']]=v['Data']
                for x in v.values(): walk(x)
            elif isinstance(v,list):
                for x in v: walk(x)
        walk(obj)
    def d(self,v):
        if not isinstance(v,dict): return v
        return v['Data'] if 'Data' in v else self.handles[v['HandleRefId']] if 'HandleRefId' in v else v
    def nodes(self,g): return {self.d(h)['id']:self.d(h) for h in self.d(g)['nodes']}
    def edges(self,g):
        nodes=self.nodes(g);owners={};result=set()
        for n in nodes.values():
            for h in n['sockets']:
                s=self.d(h);owners[id(s)]=(n['id'],s['name']['$value'])
        for n in nodes.values():
            for h in n['sockets']:
                s=self.d(h)
                for ch in s['connections']:
                    c=self.d(ch);src=self.d(c['source']);dest=self.d(c['destination'])
                    if id(src)==id(s): result.add((*owners[id(src)],*owners[id(dest)]))
        return result
    def payload(self,n):
        def normalize(v):
            if isinstance(v,list): return [normalize(x) for x in v]
            if isinstance(v,dict):
                if 'HandleRefId' in v or 'HandleId' in v: return normalize(self.d(v))
                if v.get('$type')=='TweakDBID':
                    value=v['$value']
                    if v['$storage']=='string':
                        b=value.encode();value=(len(b)<<32)|zlib.crc32(b)
                    return {'$type':'TweakDBID','hash':int(value)}
                return {k:normalize(x) for k,x in v.items() if k not in ('sockets','phaseGraph')}
            return v
        return normalize(n)
def reachable(edges,start):
    seen={start}
    while True:
        new=seen|{t for f,_,t,_ in edges if f in seen}
        if new==seen:return seen
        seen=new
def graphs():
    original=Resource(load(ROOT/'research/gig_restoration/watson_sources/json/base/open_world/street_stories/watson/northside_industrial_district/sts_wat_northside_industrial_district.questphase.json'))
    roots={};count=0
    def compare(og,pg,patched,route,changed=set()):
        nonlocal count
        on=original.nodes(og);pn=patched.nodes(pg)
        assert set(on)==set(pn),route
        assert original.edges(og)==patched.edges(pg),route+' edges'
        for id in on:
            assert original.payload(on[id])==patched.payload(pn[id]),(route,id,'payload')
            if on[id].get('phaseGraph') and ('HandleRefId' in on[id]['phaseGraph'] or 'Data' in on[id]['phaseGraph']):
                compare(on[id]['phaseGraph'],pn[id]['phaseGraph'],patched,route+'/'+str(id))
            count+=1
    embedded=original.obj['Data']['EmbeddedFiles']
    for name,index in [('owner',1),('ow',7),('gameplay',17)]:
        patched=Resource(load(OUT/f'{name}.questphase.json'));roots[name]=patched
        assert patched.obj['Data']['RootChunk']['$type']=='questQuestPhaseResource'
        if name=='gameplay':compare(embedded[index]['Content']['graph'],patched.obj['Data']['RootChunk']['graph'],patched,'gameplay')
    # The boot resource is inert: native location ownership lives behind its gate.
    boot=roots['owner'];br=boot.obj['Data']['RootChunk'];bn=boot.nodes(br['graph'])
    assert not br['phasePrefabs'] and not br['inplacePhases']
    be=boot.edges(br['graph'])
    assert be=={(0,'Out',400,'In'),(400,'Out',401,'In'),(401,'Out',402,'In'),(402,'Out',403,'In'),(403,'Out',405,'In1'),(405,'Out1',404,'In'),(404,'Out',1,'In')}
    assert bn[402]['$type']=='questPauseConditionNodeDefinition'
    assert bn[405]['phaseResource']['DepotPath']['$value']==r'towercontinued\gig_pilot_r1\native_owner.questphase'
    parent=Resource(load(OUT/'native_owner.questphase.json'));pr=parent.obj['Data']['RootChunk']
    assert pr['phasePrefabs']==embedded[1]['Content']['phasePrefabs']
    assert len(pr['phasePrefabs'])==1
    assert parent.edges(pr['graph'])==original.edges(embedded[1]['Content']['graph'])
    pn=parent.nodes(pr['graph']);on=original.nodes(embedded[1]['Content']['graph'])
    for i in on:
        opayload=original.payload(on[i]);ppayload=parent.payload(pn[i])
        if i in (8,9):
            opayload.pop('phaseResource');ppayload.pop('phaseResource')
        assert opayload==ppayload,('native owner',i)
    ow=roots['ow'];og=embedded[7]['Content']['graph'];pg=ow.obj['Data']['RootChunk']['graph']
    assert original.edges(og)==ow.edges(pg)
    onn=original.nodes(og);pnn=ow.nodes(pg)
    for i in onn:
        assert original.payload(onn[i])==ow.payload(pnn[i]),('ow',i)
        if i==2:compare(onn[i]['phaseGraph'],pnn[i]['phaseGraph'],ow,'entry')
    op=original.nodes(onn[4]['phaseGraph']);pp=ow.nodes(pnn[4]['phaseGraph'])
    oe=original.edges(onn[4]['phaseGraph']);pe=ow.edges(pnn[4]['phaseGraph'])
    assert pe=={e for e in oe if e[0]!=3}|{(3,'Out',27,'Active'),(3,'Out',202,'In')}
    for i in op:
        assert original.payload(op[i])==ow.payload(pp[i]),('play',i)
        if i!=138 and op[i].get('phaseGraph'):compare(op[i]['phaseGraph'],pp[i]['phaseGraph'],ow,'play/'+str(i))
    reached=reachable(pe,3)
    assert not reached & {81,136,208,217,247,197},reached & {81,136,208,217,247,197}
    assert {79,168,171,172,96,97,85,288,98,99,177}<=reached
    oc=original.nodes(op[138]['phaseGraph']);pc=ow.nodes(pp[138]['phaseGraph'])
    ce=original.edges(op[138]['phaseGraph'])
    expected={(f,'Out1' if f==92 else s,t,'In1' if t==92 else d) for f,s,t,d in ce}
    assert expected==ow.edges(pp[138]['phaseGraph'])
    assert pc[92]['$type']=='questLogicalXorNodeDefinition'
    for i in oc:
        if i!=92: assert original.payload(oc[i])==ow.payload(pc[i]),('chase',i)
    of=original.nodes(onn[5]['phaseGraph']);pf=ow.nodes(pnn[5]['phaseGraph'])
    oe=original.edges(onn[5]['phaseGraph']);fe=ow.edges(pnn[5]['phaseGraph'])
    expected={(f,s,94 if f==93 and s=='False' else t,'In' if f==93 and s=='False' else d) for f,s,t,d in oe if (f,t) not in {(96,69),(69,60)}}
    expected|={(96,'Out1',400,'In'),(400,'True',401,'In'),(401,'Out',69,'In'),(69,'Out',402,'In'),(402,'Out',60,'In'),(400,'False',403,'In'),(403,'Out',60,'In')}
    assert expected==fe
    for i in of:assert original.payload(of[i])==ow.payload(pf[i]),('cleanup',i)
    assert original.payload(of[69])==ow.payload(pf[69])
    assert 66 not in reachable(fe,93),'debrief scene still reachable'
    return dict(native_nodes_unchanged=count,exact_edge_deltas=True,init_replay_excluded=True,foreign_side_effect_removed=True,native_reward_kept=True,prefab_behind_optin=True)
def contracts():
    source=(ROOT/'redscript/PTFR_GigPilotR1/GigPilotR1.reds').read_text()
    writes=re.findall(r'this\.Set\(n"([^"]+)"',source)
    assert set(writes)=={'PTFRG1_Request','PTFRG1_CounterAck','PTFRG1_Fault','wat_sts_counter'}
    assert 'SetFact(n"q307' not in source and 'SetFact(n"nid_02' not in source
    for token in ('this.Preflight(0)','this.Preflight(this.prepared)','!this.ForeignSame()', 'this.inflight', 'this.schema != 1','CyberwarePolicy.Safe(player)','this.stage == 5 || this.stage == 4','count != 3 && count != 4'):assert token in source,token
    assert 'TrackEntry(' not in source and 'GiveItem' not in source and 'StartQuest' not in source
    assert source.count('jm.ChangeEntryState(')==1
    observed=load(ROOT/'research/gig_restoration/live_pair_v2_20261009.json')['records'][1]['snapshot']['journal']
    for path in re.findall(r'this\.Is\("([^"]+)"',source):assert path in observed,path
    return dict(source_guard_contracts=True,save_local_optin=True,no_global_start=True)
def logger():
    lua=LuaRuntime(unpack_returned_tuples=True)
    lua.execute('callbacks={};writes=0;registerForEvent=function(k,v) callbacks[k]=v end; print=function() end; IsDefined=function(v) return v~=nil end; os={date=function() return "STAMP" end}; io={open=function() return nil end}; Game={GetQuestsSystem=function() return {GetFactStr=function() return 0 end} end,GetPlayer=function() return nil end}')
    source=(ROOT/'diagnostics/PTFR_GigPilotR1/init.lua').read_text()
    for token in ('SetFact','ChangeEntryState','TrackEntry','Override(','Observe(','loadstring','loadfile'):assert token not in source,token
    mod=lua.execute(source);lua.execute('callbacks.onUpdate(2)');row=mod.Sample()
    assert not row['player_present'] and row['facts']['PTFRG1_Ready']==0
    return dict(luajit_syntax=True,no_gameplay_writes=True)
def admission_models():
    import copy
    pair=load(ROOT/'research/gig_restoration/live_pair_v2_20261009.json')['records']
    post=pair[1]['snapshot'];source=(ROOT/'redscript/PTFR_GigPilotR1/GigPilotR1.reds').read_text()
    body=source.split('private func LocalFacts()',1)[1].split('private func OtherObjectives()',1)[0]
    required={k:int(v) for k,v in re.findall(r'this\.Fact\(n"([^"]+)"\) == (\d+)',body)}
    assert all(post['facts'][k]==v for k,v in required.items())
    def admissible(s):
        j=s['journal'];r='quests/street_stories/watson/northside_industrial_district/sts_wat_nid_02';p=r+'/sts_wat_nid_02'
        return all(s['facts'].get(k)==v for k,v in required.items()) and all(j[x]['state']==4 for x in (r,p,p+'/inside')) and all(j[p+'/'+x]['state']==1 for x in ('info','get_into','convey','get_authorization','find_the_van','get_out','steal','optional','get_reward','get_out1'))
    assert admissible(post) and not admissible(pair[0]['snapshot'])
    refused=0
    for k,v in required.items():
        for bad in (None,v+1):
            changed=copy.deepcopy(post);changed['facts'][k]=bad
            assert not admissible(changed);refused+=1
    r='quests/street_stories/watson/northside_industrial_district/sts_wat_nid_02'
    for path in (r,r+'/sts_wat_nid_02',r+'/sts_wat_nid_02/inside'):
        for bad in (0,1,2,3):
            changed=copy.deepcopy(post);changed['journal'][path]['state']=bad
            assert not admissible(changed);refused+=1
    # Abstract transaction model: a queued native journal write is issued once;
    # interruption refuses instead of replaying it. This is NOT engine scheduling.
    for delay in range(0,12):
        writes=0;pending=False;ack=False
        for tick in range(14):
            if not pending and not ack: writes+=1;pending=True
            if tick>=delay and pending: pending=False;ack=True
        assert writes==1 and ack
    for attempts in range(1,20):
        claim=0;payouts=0
        for _ in range(attempts):
            if claim==0: claim=1;payouts+=1
        assert payouts==1
    return dict(observed_post_matches_local_admission=True,pre_tower_refused=True,admission_refusals=refused,delayed_write_cases=12,reward_repeat_cases=19,not_engine_proof=True)
def main():
    result=dict(status='PASS_GIG_PILOT_R1_OFFLINE_LIVE_PENDING',graph=graphs(),contracts=contracts(),logger=logger(),models=admission_models())
    compile=load(OUT/'compile_result.json');manifest=load(OUT/'manifest.json')
    assert compile['source_sha256']==sha(ROOT/'redscript/PTFR_GigPilotR1/GigPilotR1.reds')
    assert manifest['sha256']==sha(Path(manifest['archive'])) and manifest['packed_readback']
    result['equipmentex_full_compile']=compile['equipmentex']
    result['files']=[dict(source=s,relative=t,sha256=sha(ROOT/s)) for s,t in [
      ('build/GigPilotR1/TowerContinued_GigPilotR1.archive','archive/pc/mod/TowerContinued_GigPilotR1.archive'),
      ('archive/gig_pilot_r1/TowerContinued_GigPilotR1.archive.xl','archive/pc/mod/TowerContinued_GigPilotR1.archive.xl'),
      ('redscript/PTFR_GigPilotR1/GigPilotR1.reds','r6/scripts/PTFR_GigPilotR1/GigPilotR1.reds'),
      ('diagnostics/PTFR_GigPilotR1/init.lua','bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_GigPilotR1/init.lua')]]
    result['protected']=compile['protected'];result['dependencies']=compile['dependencies']
    result['tools']={f'tools/{n}':sha(ROOT/f'tools/{n}') for n in ('build_gig_pilot_r1.ps1','compile_gig_pilot_r1.py','test_gig_pilot_r1.py','deploy_gig_pilot_r1.ps1','afterlife_faces_r5_deployment.ps1')}
    (OUT/'tests.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('protected','dependencies','files','tools')},indent=2))
if __name__=='__main__':main()
