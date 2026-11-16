"""Evaluate preservation prerequisites and retain explicit negative/unknown results."""
from collections import Counter
from pathlib import Path
import json,struct
from prepare import HERE,ROOT,BASE,read,write,sha
from analyze import phase_hash,paths,framed,freezer

def value(x):return x.get('$value',x) if isinstance(x,dict) else x
def walk(x):
    if isinstance(x,dict):
        yield x
        for v in x.values():yield from walk(v)
    elif isinstance(x,list):
        for v in x:yield from walk(v)
def token(name):
    result=0xCBF29CE484222325
    for b in name.encode():result=((result^b)*0x100000001B3)&0xFFFFFFFFFFFFFFFF
    return str(result)

def main():
    out=HERE/'analysis_03';assert not out.exists();out.mkdir()
    plan=read(HERE/'evidence_01/inputs.json');cases=read(HERE/'analysis_01/cases.json');saves=read(HERE/'analysis_01/save_comparison.json')
    resources=read(HERE/'analysis_01/sources.json');models=read(HERE/'analysis_01/graphs.json');byrid={r['rid']:r for r in resources};bydepot={r['depot']:r['rid'] for r in resources}
    providers=read(HERE/'evidence_02/providers.json');checks=[]
    def check(name,condition):
        assert condition,name
        checks.append({'name':name,'pass':True})
    def graph(rid,path):return next(x for x in models[str(rid)]['graphs'] if x['path']==path)
    def node(rid,path,num):return next(n for n in graph(rid,path)['nodes'] if n['id']==num)
    def resolve(path):
        rid={0:9717,1:13718}[path[0]];gr='root'
        for num in path[1:]:
            n=node(rid,gr,num);dep=value(n['parameters'].get('phaseResource',{}).get('DepotPath','0'))
            if dep not in ('0',0,None):rid=bydepot[dep];gr='root'
            else:gr+='/'+str(num)
        return rid,gr
    resolved={};timers={};supports={};private_gates={}
    for qid,c in cases.items():
        before=saves['ManualSave-26']['cases'][qid];hospital=saves['AutoSave-10']['cases'][qid]
        rows=[]
        for event in before['handlers']:
            rid,gr=resolve(event['path']);n=node(rid,gr,event['node'])
            names=[o['$type'] for o in walk(n['parameters']) if '$type' in o and token(o['$type'])==event['type_token']]
            # Some pause nodes register using their condition type rather than the outer definition.
            check(f'{qid} exact saved node {event["slot"]} resolves a matching native type token',bool(names))
            rows.append({**event,'resource':byrid[rid]['depot'],'graph':gr,'definition_type':n['type'],'registered_type_matches':names,'parameters':n['parameters']})
        resolved[qid]=rows
        check(qid+' original registration identities unchanged before vs first hospital checkpoint',before['handlers']==hospital['handlers'])
        check(qid+' original handlers absent after native shutdown and after credits',all(saves[slot]['cases'][qid]['handler_count']==0 for slot in ('AutoSave-11','AutoSave-5')))
        check(qid+' cached native path catalogue survives removal',all(saves[slot]['cases'][qid]['catalog_paths']==before['catalog_paths']>0 for slot in saves))
        check(qid+' no saved target/ancestor freeze group in any inspected fixture',not any(saves[slot]['cases'][qid]['freezer_groups'] for slot in saves))
        timers[qid]=[];supports[qid]=[]
        for rid in c['native_body_resources']:
            m=models[str(rid)];resource=byrid[rid]['depot']
            if m['support'].get('phasePrefabs'):supports[qid].append({'resource':resource,'scope':'ROOT','prefabs':m['support']['phasePrefabs']})
            for gr in m['graphs']:
                for n in gr['nodes']:
                    times=[o['type'] for o in walk(n['parameters']) if o.get('$type')=='questTimeCondition' and 'type' in o]
                    if times:timers[qid].append({'resource':resource,'graph':gr['path'],'node':n['id'],'conditions':times})
                    if n['parameters'].get('phaseInstancePrefabs'):supports[qid].append({'resource':resource,'graph':gr['path'],'node':n['id'],'scope':'INSTANCE','prefabs':n['parameters']['phaseInstancePrefabs']})
        private_gates[qid]=[{'resource':byrid[rid]['depot'],'graph':gr['path'],'node':n['id'],'parameters':n['parameters']} for rid in c['private_resources'] for gr in models[str(rid)]['graphs'] for n in gr['nodes'] if any(k in json.dumps(n['parameters']) for k in ('q307_main_game_killed','q307_ep1_killed','_Issued','_Permit'))]
    check('Inactive Highwayman has eleven native registrations',saves['ManualSave-26']['cases']['mq029_tourist']['handler_count']==11)
    roots={r['definition']['id']:r for r in plan['snapshot_rows']}
    check('Inactive control journal is genuinely Inactive in the captured history',roots['mq029_tourist']['states'][0]==1)
    check('Active cases preserve captured delivery and first-door objectives',all(any(v==2 and p[0].endswith(suffix) for p,v in zip(roots[q]['definition']['journals'],roots[q]['states'])) for q,suffix in [('mq007_smartgun','01_deliver_skippy'),('q304_car_retrieval','01_reach_the_door')]))
    # The actual loaded root route uses the base terminating output and EP1 parent cut.
    base=graph(6628,'root');ep1=graph(13133,'root/10')
    check('Base root termination follows its own native kill receipt',all(edge in base['edges'] for edge in [[106,'Out','Output',109,'In','Input'],[109,'Out','Output',107,'In','Input']]) and node(6628,'root',107)['parameters']['type']=='Terminating')
    check('EP1 cut removes the selected parent before its receipt',all(edge in ep1['edges'] for edge in [[8,'Out','Output',9,'In','Input'],[9,'CutSource','CutSource',4,'CutDestination','CutDestination'],[9,'Out','Output',10,'In','Input']]))
    check('All loaded case routes bypass the standalone q307.quest test root',all(not any(s['depot'].endswith('\\q307.quest') for s in c['route']['steps']) for c in cases.values()))
    check('Moving Heat cut ancestor is the additional-content owner',cases['q304_car_retrieval']['route']['path'][:4]==[1,0,10,4])
    check('After-credits fixture retains genuine ending receipts',all(saves['AutoSave-5']['facts'][name]==1 for name in ('q307_done','q307_finished','q307_main_game_killed','q307_ep1_killed')))
    # Provider readback also sees the current HS3 pickup gate. Its byte donor is retained.
    expected={(r['archive'],r['key']) for r in resources};extras=[r for r in providers['providers'] if (r['archive'],r['key']) not in expected]
    check('Only extra relevant provider is the installed HS3 capture gate',len(extras)==1 and extras[0]['depot'].endswith('q307_01_pickup.questphase'))
    installed=read(BASE/'deployment_01/installed_manifest_01.json');archive_source=Path(installed['archive_source'])
    check('Current pickup override equals the installed HS3 donor',sha(archive_source/extras[0]['depot'])==extras[0]['sha256'])
    # Native resource references do not redirect to the private Johnny-edited resources.
    johnny=[]
    for native,private in [('mq029_garage.questphase',14538),('mq029_josie_corpse.questphase',15387)]:
        nrid=next(r['rid'] for r in resources if r['role']=='STOCK' and r['depot'].endswith('\\'+native))
        def scenes(rid):return sorted({value(n['parameters']['sceneFile']['DepotPath']) for gr in models[str(rid)]['graphs'] for n in gr['nodes'] if 'sceneFile' in n['parameters']})
        ns,ps=scenes(nrid),scenes(private)
        check(native+' preserved native execution misses private edited scenes',bool(ns) and bool(ps) and set(ns).isdisjoint(ps))
        for dep in ns:
            matches=[r for r in providers['providers'] if r['depot']==dep]
            check(dep+' native scene is not overridden by the installed private edits',len(matches)==1 and '\\archive\\pc\\content\\' in matches[0]['archive'])
        johnny.append({'native_phase':byrid[nrid]['depot'],'native_scenes':ns,'private_phase':byrid[private]['depot'],'edited_scenes':ps})
    scripts=[];game=Path(installed['game_root'])
    for file in ('PTFR_SideJobsS22.reds','PTFR_SideJobsS23.reds','PTFR_SideJobsS28.reds'):
        path=game/'r6/scripts/PTFR_Consolidated'/file;text=path.read_text(encoding='utf-8-sig')
        check(file+' fresh/resume admission assumes both old root shutdowns',all(x in text for x in ('this.Fact("q307_main_game_killed") == 1','this.Fact("q307_ep1_killed") == 1')))
        scripts.append({'path':str(path),'sha256':sha(path),'gate_lines':[{'line':i+1,'text':s} for i,s in enumerate(text.splitlines()) if any(k in s for k in ('q307_main_game_killed','q307_ep1_killed','PTFRSKIP_SC3_Stopped'))]})
    # Real-data malformed controls prevent a phantom preserved handler or freezer record.
    capture=read(HERE/'saves_01/ManualSave-26/manifest.json');parts={r['name']:r for r in capture['nodes']}
    rejects=[]
    for name,decode in [('customArray',paths),('eventManager',lambda b,n:list(struct.iter_unpack('<QII',framed(b,n,16)))),('questPhaseFreezer',freezer)]:
        row=parts[name];raw=Path(row['path']).read_bytes()
        for label,changed in [('truncated',raw[:-1]),('extra-byte',raw+b'\0'),('wrong-id',struct.pack('<I',row['id']^1)+raw[4:])]:
            try:decode(changed,row['id'])
            except (ValueError,struct.error):rejects.append(name+':'+label)
            else:raise AssertionError('Malformed saved component accepted')
    check('Nine damaged actual saved components rejected',len(rejects)==9)
    check('Positive freezer records exist elsewhere, so target absence is not an empty-decoder artifact',saves['ManualSave-26']['total_freezer_groups']>0)
    check('Selected registered callbacks contain no active timer condition',not any('questTimeCondition' in json.dumps(r['parameters']) for rows in resolved.values() for r in rows))
    result={'status':'PRESERVATION_NOT_QUALIFIED_USE_STAGE_ADAPTERS','checks':checks,'check_count':len(checks),'resolved_handlers':resolved,'native_timer_definitions':timers,'support_scopes':supports,'private_admission_sites':private_gates,'johnny_reference_counterexamples':johnny,'admission_scripts':scripts,'malformed_controls':rejects,
        'experiments':[
            {'proposal':'Only prevent bulk journal failure','result':'REJECTED_SOURCE_COUNTEREXAMPLE','reason':'Both loaded root retirement paths still unregister all three native owners.'},
            {'proposal':'Skip the standalone q307.quest cut','result':'REJECTED_SOURCE_COUNTEREXAMPLE','reason':'These saves bind base/EP1 roots; their independent terminating/cut paths remain.'},
            {'proposal':'Skip all loaded ancestor shutdowns and keep killed facts true','result':'REJECTED_CONTRACT','reason':'Retirement receipts become false; installed admission has no native-preserved ownership arbitration. Callbacks remain registered and timers are not suspended by bypassing cuts. Highwayman keeps original Johnny scene references.'},
            {'proposal':'Skip ancestor shutdowns and leave killed facts false','result':'REJECTED_CONTRACT','reason':'Existing continuation/admission requiring genuine retirement receipts remains gated; timer suspension and scene mapping are still absent.'},
            {'proposal':'Move preserved jobs beneath a private root','result':'REJECTED_IDENTITY_SHORTCUT','reason':'Full phase paths and hashes change; existing saved registrations are bound to original parent/node addresses. This needs explicit native migration and lease handling.'},
            {'proposal':'Use native area freezer as a complete pause API','result':'NOT_QUALIFIED','reason':'Exact engine evidence covers stored groups/deferred inputs and wake dispatch. It does not establish remaining-time suspension, all external callbacks, support lifetime or reload of a selectively preserved quest.'}],
        'decision':'Keep genuine native retirement and existing inactive routes; implement shared earned-stage adapters in later steps. No preservation family was qualified by this bounded experiment.',
        'live_preservation_test':'NOT_RUN_UNSAFE_PREREQUISITES_UNMET','timer_suspend_resume':'NOT_VERIFIED; no active timer in these captured stages and no qualified general suspension mechanism.',
        'genuine_tower_completion':'Unmodified baseline independently observed to reach Ready; after-credits historical control has done/finished. No preserved-owner variant was run through Tower.',
        'save_reload_preserved_owner':'NOT_VERIFIED; no preservation candidate deployed. Saved-address binding and before/after removal were checked offline.',
        'game_writes':0,'save_writes':0,'game_launches':0}
    write(out/'qualification.json',result)
    print(json.dumps({'status':result['status'],'checks':len(checks),'resolved_handlers':{q:len(r) for q,r in resolved.items()},'timer_definition_sites':{q:len(r) for q,r in timers.items()},'live_preservation_test':result['live_preservation_test']}))

if __name__=='__main__':main()
