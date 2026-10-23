"""Separate cast-aware 72-gig overlay; never regenerate installed R3 history."""
import json,re
from pathlib import Path
from catalog_gig_rollout_r2 import ROOT,read,sha,normalize,journal,value
OUT=ROOT/'research/gig_restoration/batch_b4'
POLICY=ROOT/'research/gig_restoration/lore_whitelists_v4_cast.json'
LIBROOTS=[ROOT/'research/gig_restoration'/p for p in ('watson_sources/json','fresh_candidates/local_sources/json','expanded_sources/json','rollout_r2/native_sources/json','batch_b4/sources/json','batch_b4/extras/json')]

def library():
    lib={};owners={}
    for folder in LIBROOTS:
        if not folder.exists():continue
        for path in folder.rglob('*.json'):
            if path.name.endswith('.scene.json') or path.name.endswith('.community.json'):continue
            obj=read(path);source=str(path.relative_to(ROOT)).replace('\\','/')
            meta={'source':source,'sha256':sha(path),'embedded_index':None}
            name=str(path.relative_to(folder))[:-5].replace('/','\\')
            lib[name]=(obj,obj['Data']['RootChunk'],meta)
            for i,e in enumerate(obj['Data'].get('EmbeddedFiles',[])):
                if e['Content'].get('$type')=='questQuestPhaseResource':
                    depot=value(e['FileName']);lib[depot]=(obj,e['Content'],meta|{'embedded_index':i})
    return lib

def main():
    OUT.mkdir(exist_ok=True)
    assert not (OUT/'install_receipt.json').exists(),'Installed evidence pinned'
    old=read(ROOT/'research/gig_restoration/rollout_r2/catalogue.json')
    titles=read(POLICY)['ignore_two_year_gap']['gigs'];assert len(titles)==72
    old_bytitle={normalize(j['selected_title']):j for j in old['jobs']}
    loc={}
    for path in [ROOT/'research/misty_viktor_world/bradbury_localization/json/base/localization/en-us/onscreens/onscreens.json.json',ROOT/'research/misty_viktor_world/street_localization/json/ep1/localization/en-us/onscreens/onscreens.json.json']:
        for row in read(path)['Data']['RootChunk']['root']['Data']['entries']:loc[str(row['primaryKey'])]=row['femaleVariant']
    allj=[]
    for path in [ROOT/'research/gig_restoration/journal_sources/json/base/journal/cooked_journal.journal.json',ROOT/'research/phase2b_p2/extracted/json/ep1/journal/cooked_journal.journal.json']:allj+=journal(path,loc)
    lib=library();jobs=[]
    for title in titles:
        matches=[j for j in allj if normalize(j['title'] or '')==normalize(title)];assert len(matches)==1,title
        j=matches[0];known={p:m for p,(_,_,m) in lib.items() if re.search(r'\\'+re.escape(j['id'])+r'(?:\\|\.|_)',p)}
        if not known:known={p:m for p,(_,_,m) in lib.items() if j['id'] in p}
        prefab=[p for p in known if lib[p][1].get('phasePrefabs')]
        jobs.append(j|{'selected_title':title,'native_resources':[m|{'depot_path':p} for p,m in known.items()],'prefab_owners':prefab,'legacy_history':normalize(title) in old_bytitle,'current_adapter':{'sts_wat_nid_02':'G1','sts_wat_nid_05':'G2.1','sts_bls_ina_07':'G3'}.get(j['id'])})
    result={'schema':1,'status':'B4_SELECTION_OVERLAY_NOT_RUNTIME_ADMISSION','policy':str(POLICY.relative_to(ROOT)).replace('\\','/'),'policy_sha256':sha(POLICY),'count':72,'jobs':jobs,'installed_r3_definition_unchanged':sha(ROOT/'redscript/PTFR_ActivityStateR3/ActivityDefinition.generated.reds'),'game_writes':0,'direct_save_writes':0}
    (OUT/'catalogue.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'count':len(jobs),'prefab_owner_counts':{str(n):sum(len(j['prefab_owners'])==n for j in jobs) for n in sorted({len(j['prefab_owners']) for j in jobs})},'missing':[(j['id'],j['selected_title']) for j in jobs if not j['native_resources']],'added_history_unknown':[j['id'] for j in jobs if not j['legacy_history']]},indent=2))
if __name__=='__main__':main()
