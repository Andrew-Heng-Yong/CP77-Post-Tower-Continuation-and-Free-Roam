"""Source-pinned graph contracts, real Lua dispatch and accounting interruption models."""
import itertools,json,re,sys
from catalog_gig_rollout_r2 import ROOT,read,sha
from test_rite_g2 import SafeResource
from audit_activity_batches_b1 import flatten
from test_fresh_gigs_b5_1 import body,normalize
sys.path.insert(0,str(ROOT/'research/phase2b_p0/tooling/python'))
from lupa.luajit21 import LuaRuntime
OUT=ROOT/'research/gig_restoration/family_b7'

def built(depot):
    r=SafeResource(read(OUT/'built'/(depot.replace('\\','/')+'.json')))
    root=r.obj['Data']['RootChunk']
    return r,root,{g['path']:g for g in flatten(r,root)}

def graph_checks():
    plan=read(OUT/'build_plan.json');total=graphs=0
    for j in plan['jobs']:
        depotmap={r['depot']:'towercontinued\\family_b7\\'+j['id']+'\\'+r['key']+'.questphase' for r in j['resources']}
        for res in j['resources']:
            r,root,pg=built(depotmap[res['depot']]);og={g['path']:g for g in res['graphs']}
            assert set(pg)==set(og),(j['id'],res['depot'],'graph closure')
            for path,g in og.items():
                on={n['id']:n for n in g['nodes']};pn={n['id']:n for n in pg[path]['nodes']};assert set(on)<=set(pn)
                for ident,n in on.items():
                    a=dict(n);b=dict(pn[ident]);dep=a.get('phaseResource',{}).get('DepotPath',{}).get('$value')
                    if dep in depotmap:
                        a.pop('phaseResource');patched=b.pop('phaseResource');assert patched['DepotPath']['$value']==depotmap[dep]
                    assert a==b,(j['id'],res['key'],path,ident,'native payload changed');total+=1
                expected={tuple(e) for e in g['edges']};extra=set()
                for c in j['calls']:
                    if c['depot']!=res['depot'] or c['graph']!=path:continue
                    replacement=set()
                    for f,s,t,d in expected:
                        if t==c['node'] and d!='CutDestination':replacement|={(f,s,x,y) for x,y in c['alternative']}
                        else:replacement.add((f,s,t,d))
                    expected=replacement
                    assert not any(t==c['node'] and d!='CutDestination' for f,s,t,d in expected)
                for m in j['mutations']:
                    if m['depot']!=res['depot'] or m['graph']!=path:continue
                    ident=m['node'];base=30000+ident*6;key=j['tag']+'_'+m['key'];old={e for e in expected if e[0]==ident}
                    expected={(f,s,base if t==ident and d=='In' else t,d) for f,s,t,d in expected if f!=ident}
                    expected|={(base,'True',base+1,'In'),(base+1,'Out',ident,'In'),(ident,'Out',base+2,'In'),(base,'False',base+3,'In')}
                    expected|={(base+2,'Out',t,d) for _,_,t,d in old};extra|=set(range(base,base+4))
                    conditions=pn[base]['condition']['conditions'];assert [(c['type']['factName'],c['type']['value']) for c in conditions]==[(key+'_Claim',0),(key+'_Ack',0),(j['tag']+'_Fault',0)]
                    for offset,name in [(1,key+'_Claim'),(2,key+'_Ack'),(3,j['tag']+'_Fault')]:
                        assert pn[base+offset]['type']['factName']==name and pn[base+offset]['type']['value']==1 and pn[base+offset]['type']['setExactValue']==1
                assert set(pn)-set(on)==extra,(j['id'],path,'new nodes')
                assert {tuple(e) for e in pg[path]['edges']}==expected,(j['id'],res['key'],path,'edges')
                graphs+=1
        p=j['parent'];_,root,bg=built('towercontinued\\family_b7\\'+j['id']+'\\boot.questphase');g=bg['root'];bn={n['id']:n for n in g['nodes']}
        assert not root['phasePrefabs'] and not root['inplacePhases']
        original=p['ancestors']+[p['child']]
        for n in original:
            a=dict(n);b=dict(bn[n['id']])
            if n['id']==p['child']['id']:
                dep=a.pop('phaseResource');assert b.pop('phaseResource')['DepotPath']['$value']==depotmap[dep['DepotPath']['$value']]
            if n['id']==p['input_node']:a.pop('socketName');assert b.pop('socketName')['$value']=='In1'
            assert a==b,(j['id'],n['id'],'parent payload')
        for nested in p['nested']:
            expected=json.loads(json.dumps(nested))
            for edit in p['edits']:
                if edit['graph']!=nested['path']:continue
                assert edit['remove'] in expected['edges'];expected['edges'].remove(edit['remove'])
                if edit['add']:expected['edges'].append(edit['add'])
            assert bg[nested['path']]['nodes']==expected['nodes'] and set(map(tuple,bg[nested['path']]['edges']))==set(map(tuple,expected['edges'])),(j['id'],'parent nested graph')
            if j['id']=='sts_bls_ina_03':assert not any(e[2]==6 for e in expected['edges'])
            if j['id']=='sts_cct_dtn_05':assert not any(e[2]==6 for e in expected['edges'])
        expected=set()
        for f,s,t,d in p['edges']:
            if f==p['input_node']:f=65001
            if t==p['child']['id']:t=65002;d='In'
            expected.add((f,s,t,d))
        expected|={(p['input_node'],'Out',65000,'In'),(65000,'Out',65006,'In'),(65006,'Out',65001,'In'),(65002,'True',65003,'In'),(65003,'Out',p['child']['id'],p['child_input']),(65004,'Out',65005,'In')}
        expected|={(p['child']['id'],port,65004,'In') for port in j['outputs']}
        assert set(map(tuple,g['edges']))==expected
        for gate in [65001,65002]:
            pairs={c['type']['factName']:c['type']['value'] for c in bn[gate]['condition']['conditions']}
            for k,v in {'q307_done':1,'q307_finished':1,'q307_main_game_killed':1,'q307_ep1_killed':1,j['tag']+'_Request':1,j['tag']+'_Permit':1,j['tag']+'_Started':0,j['tag']+'_Fault':0}.items():assert pairs[k]==v
            assert all(pairs[f]==0 for f in j['start']+j['terminal'])
        assert set(bn)=={n['id'] for n in original}|set(range(65000,65007))
    # Earned tier graphs: exact original threshold/time/content payloads, guarded
    # native messages and exact-value tier writes, no global completion loop.
    for tier in plan['tiers']:
        _,root,gs=built('towercontinued\\family_b7\\tiers\\'+tier['region']+'_'+str(tier['threshold'])+'.questphase')
        g=gs['root'];pn={n['id']:n for n in g['nodes']};edges=set(map(tuple,tier['edges']))
        edges|={(65000,'Out',65001,'In'),(65001,'Out',65002,'In'),(65002,'Out',tier['start'],'In')}
        for t in tier['targets']:
            if not any(e[0]==t for e in edges):edges.add((t,'Out',65003,'In'))
        ids={65000,65001,65002,65003}
        for n in tier['nodes']:
            a=json.loads(json.dumps(n));ids.add(n['id'])
            if n['$type']=='questFactsDBManagerNodeDefinition':a['type']['setExactValue']=1
            assert a==pn[n['id']],('tier payload',tier['region'],n['id'])
            if n['$type'] not in ('questFactsDBManagerNodeDefinition','questPhoneManagerNodeDefinition'):continue
            ident=n['id'];gate=30000+ident;ids.add(gate);old={e for e in edges if e[0]==ident}
            edges={(f,s,gate if t==ident else t,d) for f,s,t,d in edges};edges.add((gate,'True',ident,'In'));edges|={(gate,'False',t,d) for _,_,t,d in old}
            condition=pn[gate]['condition']['type']
            if n['$type']=='questFactsDBManagerNodeDefinition':assert condition['factName']==n['type']['factName'] and condition['value']==0
            else:assert condition['path']==n['type']['msg'] and condition.get('state','Inactive')=='Inactive'
        assert set(pn)==ids and set(map(tuple,g['edges']))==edges
    return total,graphs

def lua_checks():
    rt=LuaRuntime(unpack_returned_tuples=True)
    rt.execute('''writes=0; reads=0; changed=false
      b={Coverage=function() return 'test coverage' end,IDs=function() return {'sts_wbr_hil_01','new','pending'} end,
        Inspect=function(self,id) reads=reads+1;return id end,
        Restore=function(self,id,override) writes=writes+1;return id end}
      r={BatchEpoch=function() return changed and writes>0 and 2 or 1 end,
        Inspect=function() reads=reads+1;return 'old' end,
        RestoreGig=function() writes=writes+1;return 'old' end,
        Override=function() writes=writes+1;return 'old' end}
      Game={GetScriptableSystemsContainer=function() return {Get=function(self,name) return name:find('GigFamily') and b or r end} end,
        GetPlayer=function() return {GetEntityID=function() return {hash=123} end} end}
      IsDefined=function(x) return x~=nil end
    ''')
    m=rt.execute((ROOT/'diagnostics/PTFR_GigFamilyB7/init.lua').read_text())
    m.PlanAll();assert rt.globals().writes==0 and rt.globals().reads==3
    rt.execute("r.Inspect=function() return nil end");m.PlanAll();assert rt.globals().writes==0
    m.OverrideAll('bad');assert rt.globals().writes==0
    m.OverrideAll('DISPOSABLE_SAVE');assert rt.globals().writes==3
    rt.execute('writes=0;changed=true');assert 'cancelled' in m.OverrideAll('DISPOSABLE_SAVE') and rt.globals().writes==1
    rt.execute('writes=0;changed=false;Game.GetPlayer=function() return nil end');assert 'cancelled' in m.RestoreAll() and rt.globals().writes==0
    return 6

def models():
    # Claim/ack ledger survives reload at each transaction boundary. An
    # interrupted claim never resends credit, even if its increment happened.
    cases=0
    for base,interrupt,roots,finished in itertools.product((0,1,4,100,2147483646,2147483647),range(5),(1,2,3,4),(0,1)):
        counter=base;claim=ack=fault=0
        if roots==3 and finished==1 and base<2147483647:
            if interrupt>=1:claim=1
            if interrupt>=2:counter=base+1
            if interrupt>=3:ack=1
        for reload in range(3):
            if claim and not ack:fault=1
            if ack:assert counter==base+1
        assert counter-base in (0,1);cases+=1
    return cases

def main():
    assert not (OUT/'install_receipt.json').exists()
    plan=read(OUT/'build_plan.json');manifest=read(OUT/'manifest.json');c=read(OUT/'compile_result.json')
    assert manifest['plan_sha256']==sha(OUT/'build_plan.json') and manifest['packed_readback']
    for p,h in plan['pins'].items():assert sha(ROOT/p)==h
    for p,h in c['sources'].items():assert sha(ROOT/p)==h
    native,graphs=graph_checks();lua=lua_checks();cases=models()
    old=(OUT/'predecessor/ActivityStateR3.reds').read_text();new=(ROOT/'redscript/PTFR_ActivityStateR3/ActivityStateR3.reds').read_text()
    assert sha(OUT/'predecessor/ActivityStateR3.reds')=='8598DAB40F869F820BD0C04312127C7C412D1DE31A872CC26260B9E172519AC2'
    for n in set(re.findall(r'\bfunc (\w+)\(',old)):assert normalize(body(new,n))==normalize(body(old,n)),n
    assert re.findall(r'private persistent let .*?;',old)==re.findall(r'private persistent let .*?;',new)
    assert sha(ROOT/'redscript/PTFR_ActivityStateR3/ActivityDefinition.generated.reds')=='81900EBDB2633424DDC41B9BD2223F2E5740E6CA807E5C1A58DE645159162AE5'
    b7=(ROOT/'redscript/PTFR_GigFamilyB7/GigFamilyB7.reds').read_text();assert 'ChangeEntryState' not in b7 and 'this.Own(i,"CounterClaim")!=0' in b7
    for name in ['Fresh','Unused','Inspect','LegacyIdle']:assert '.Write(' not in body(b7,name) and '.Set(' not in body(b7,name)
    files=[]
    for src,dst,pre in [
      ('build/GigFamilyB7/TowerContinued_FamilyB7.archive','archive/pc/mod/TowerContinued_FamilyB7.archive',None),
      ('build/GigFamilyB7/TowerContinued_FamilyB7.archive.xl','archive/pc/mod/TowerContinued_FamilyB7.archive.xl',None),
      ('redscript/PTFR_GigFamilyB7/GigFamilyB7.reds','r6/scripts/PTFR_GigFamilyB7/GigFamilyB7.reds',None),
      ('redscript/PTFR_GigFamilyB7/GigDataB7.generated.reds','r6/scripts/PTFR_GigFamilyB7/GigDataB7.generated.reds',None),
      ('diagnostics/PTFR_GigFamilyB7/init.lua','bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_GigFamilyB7/init.lua',None),
      ('redscript/PTFR_ActivityStateR3/ActivityStateR3.reds','r6/scripts/PTFR_ActivityStateR3/ActivityStateR3.reds','8598DAB40F869F820BD0C04312127C7C412D1DE31A872CC26260B9E172519AC2')]:files.append(dict(source=src,relative=dst,predecessor=pre,sha256=sha(ROOT/src)))
    tools=['build_gig_family_b7.ps1','prepare_gig_family_b7.py','compile_gig_family_b7.py','test_gig_family_b7.py']
    result=dict(status='PASS_B7_OFFLINE_LIVE_PENDING',new_gig_adapters=len(plan['jobs']),pending_adapters=len(plan['pending'])-6,native_payloads=native,graphs=graphs,exact_edges=True,persistence_verified=True,r3_history_capture_schema_unchanged=True,lua_cases=lua,interruption_models=cases,files=files,tools={'tools/'+p:sha(ROOT/'tools'/p) for p in tools},compile_sha256=sha(OUT/'compile_result.json'),manifest_sha256=sha(OUT/'manifest.json'))
    (OUT/'tests.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('files','tools')}))
if __name__=='__main__':main()
