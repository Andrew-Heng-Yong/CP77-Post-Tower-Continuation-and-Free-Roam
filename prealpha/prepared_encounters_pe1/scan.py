"""Locate actual admission guards and source writers, without changing inputs."""
from pathlib import Path
from collections import defaultdict,Counter
import gzip
import json
import sys
from inventory import HERE,WS,BASE,CACHE,read,sha,write
sys.path.insert(0,str(WS/'tools/parity_audit'))
from model import Resource
from common import walk


def main():
    target=HERE/'scan_01.json';assert not target.exists()
    inventory=read(HERE/'inventory_01.json')
    fresh={r['depot']:r for r in read(HERE/'fresh_01/manifest.json')['resources']}
    models={};pins=[]
    for row in inventory['resources']:
        if row['reuse']=='EXACT_RAW_HASH_MATCH':
            assert sha(row['model'])==row['model_sha256']
            model=json.loads(gzip.decompress(Path(row['model']).read_bytes()))
            pins.append({'path':row['model'],'sha256':row['model_sha256']})
        else:
            r=fresh[row['depot']];assert r['sha256']==row['sha256'] and sha(r['json'])==r['json_sha256']
            model=Resource(read(r['json'])).normalize()
            pins.append({'path':r['json'],'sha256':r['json_sha256']})
        assert not model['errors'],(row['depot'],model['errors'])
        models[row['depot']]=model
    guards=[];all_zero=Counter()
    for depot,model in models.items():
        for gp,g in model['graphs'].items():
            for i,node in g['nodes'].items():
                reads=[r for r in node.get('reads',[]) if r.get('$type')=='questVarComparison_ConditionType']
                zeros=[r['factName'] for r in reads if r['comparisonType']=='Equal' and r['value']==0 and not r['factName'].startswith('PTFR')]
                all_zero.update(zeros)
                own=[r for r in reads if r['factName'].startswith('PTFR') and (r['factName'].endswith(('_Permit','_Request','_Eligible','_Ready')) and r['value']==1)]
                tower=any(r['factName']=='PostTowerFreeRoamActive' and r['value']==1 for r in reads)
                if not (tower or own):continue
                if not zeros:continue
                guards.append({'depot':depot,'graph':gp,'node':i,'type':node['type'],'tower':tower,'owner_gates':own,'zero_facts':zeros,'journal_paths':node.get('journal_paths',[]),'other_reads':reads})
    flags=sorted({n for g in guards for n in g['zero_facts'] if n.endswith(('_active','_started')) or 'start_community' in n})
    private_writers=defaultdict(list)
    for depot,model in models.items():
        for gp,g in model['graphs'].items():
            for i,node in g['nodes'].items():
                for r in node.get('writes',[]):
                    if r['factName'] in flags:
                        private_writers[r['factName']].append({'depot':depot,'graph':gp,'node':i,'write':r,'incoming':[e for e in g['edges'] if e[2]==i],'outgoing':[e for e in g['edges'] if e[0]==i]})
    cache=read(CACHE);native_writers=defaultdict(list);native_models=0
    for depot,row in cache.items():
        if depot.startswith('towercontinued\\') or not depot.endswith(('.questphase','.quest')):continue
        assert sha(row['normalized_model'])==row['normalized_sha256']
        model=json.loads(gzip.decompress(Path(row['normalized_model']).read_bytes()));native_models+=1
        if model.get('errors'):continue
        for gp,g in model['graphs'].items():
            for i,node in g['nodes'].items():
                for r in node.get('writes',[]):
                    if r['factName'] in flags:
                        native_writers[r['factName']].append({'depot':depot,'graph':gp,'node':i,'write':r,'incoming':[e for e in g['edges'] if e[2]==i],'outgoing':[e for e in g['edges'] if e[0]==i],'resource_sha256':row['resource_sha256'],'model':row['normalized_model'],'model_sha256':row['normalized_sha256'],'source_json':row['source_json']})
    report={'schema':1,'status':'ALL_PHASE_ADMISSION_AND_NATIVE_WRITERS_SCANNED','phase_resources':len(models),'admission_guard_nodes':len(guards),'guards':guards,'flags':flags,'private_writers':private_writers,'native_writers':native_writers,'native_phase_models_scanned':native_models,'current_model_pins':pins,'zero_fact_counts':dict(all_zero),'source_limit':'Cached native model bytes are pinned; current native provider equivalence is required before approving a change. Current private models match the exact installed KM1 source inventory.','game_writes':0,'save_writes':0}
    write(target,report)
    print(json.dumps({'current_phases':len(models),'guard_nodes':len(guards),'candidate_active_started_flags':len(flags),'native_phases_scanned':native_models,'native_writer_flags_found':len(native_writers)}))


if __name__=='__main__':
    main()
