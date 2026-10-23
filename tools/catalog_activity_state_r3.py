"""Build-time save-local activity observation definition; no gameplay writes."""
import hashlib, json, re
from pathlib import Path
from catalog_gig_rollout_r2 import ROOT, read, sha, handles, deref, value, normalize, walk
OUT=ROOT/'research/activity_state_r3'
ALIASES={
    'Burning Desire/Night Moves':['Burning Desire','Night Moves'],
    'Sacrum Profanum / Losing My Religion':['Sacrum Profanum','Losing My Religion'],
}

def all_quests(path,loc):
    obj=read(path);h=handles(obj);found=[]
    def visit(w,p):
        n=deref(w,h);key=n.get('id','');ep=p+([key] if key else [])
        if n.get('$type')=='gameJournalQuest':
            k=str(value(n.get('title'))).removeprefix('LocKey#')
            nodes=[]
            def collect(x,parent):
                e=deref(x,h);id=e.get('id','');q=parent+([id] if id else [])
                if e.get('$type') in ('gameJournalQuest','gameJournalQuestPhase','gameJournalQuestObjective','gameJournalQuestDescription'):
                    nodes.append({'path':'/'.join(q),'className':e['$type']})
                for child in e.get('entries',[]):collect(child,q)
            collect(w,p)
            found.append({'id':key,'journal_path':'/'.join(ep),'native_title':loc.get(k),'quest_type':n.get('type'),'journal_entries':nodes})
        for child in n.get('entries',[]):visit(child,ep)
    visit(obj['Data']['RootChunk']['entry'],[])
    return found

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    gigcat=read(ROOT/'research/gig_restoration/rollout_r2/catalogue.json')
    whitelist=read(ROOT/'research/gig_restoration/lore_whitelists_v3_broad.json')['ignore_two_year_gap']
    jps=[ROOT/'research/gig_restoration/journal_sources/json/base/journal/cooked_journal.journal.json',ROOT/'research/phase2b_p2/extracted/json/ep1/journal/cooked_journal.journal.json']
    lps=[ROOT/'research/misty_viktor_world/bradbury_localization/json/base/localization/en-us/onscreens/onscreens.json.json',ROOT/'research/misty_viktor_world/street_localization/json/ep1/localization/en-us/onscreens/onscreens.json.json']
    loc={}
    for p in lps:
        for e in read(p)['Data']['RootChunk']['root']['Data']['entries']:loc[str(e['primaryKey'])]=e['femaleVariant']
    quests=[e for p in jps for e in all_quests(p,loc)]
    jobs=[{k:v for k,v in e.items() if k in ('id','journal_path','selected_title','journal_entries','fact_names')}|{'category':'gig'} for e in gigcat['jobs']]
    unresolved=[]
    for title in whitelist['side_and_minor_jobs']:
        names={normalize(n) for n in ALIASES.get(title,[title])}
        matches=[e for e in quests if normalize(e['native_title'] or '') in names]
        if len(matches)!=1:
            unresolved.append({'title':title,'matches':[{'id':e['id'],'path':e['journal_path'],'native_title':e['native_title']} for e in matches]})
        else:
            e=matches[0];jobs.append(e|{'selected_title':title,'category':'side_job','fact_names':[]})
    native=[];facts=set(gigcat['fact_names']);native_hashes={}
    for p in (OUT/'native_sources/json').rglob('*.json'):
        obj=read(p);owned={v['factName'] for v in walk(obj) if isinstance(v.get('factName'),str) and re.fullmatch('[A-Za-z0-9_]+',v['factName'])}
        rel=str(p.relative_to(ROOT)).replace('\\','/');native_hashes[rel]=sha(p)
        native.append({'resource':str(p.relative_to(OUT/'native_sources/json'))[:-5].replace('/','\\'),'source':rel,'facts':owned})
        facts|=owned
    for e in jobs:
        if e['category']!='side_job':continue
        match=re.match(r'^(mq\d+|sq\d+|wst_ep1_\d+)',e['id'])
        prefix=match[1] if match else e['id']
        related=[n for n in native if re.search(r'\\'+re.escape(prefix)+r'(?:[\\_.]|c\d)',n['resource'])]
        e['fact_names']=sorted(set().union(*(n['facts'] for n in related)))
        e['native_fact_sources']=[n['source'] for n in related]
        e['physical_owner_review']='PENDING_NOT_RUNTIME_ADMISSION'
    result={'schema':1,'status':'OBSERVATION_DEFINITION_NOT_ACTIVITY_RESTORATION','jobs':jobs,'unresolved':unresolved,
        'gig_count':71,'selected_side_job_count':len(whitelist['side_and_minor_jobs']),
        'resolved_side_job_count':len(jobs)-71,'fact_names':sorted(facts),
        'source_inputs':{str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in jps+lps+[ROOT/'research/gig_restoration/rollout_r2/catalogue.json',ROOT/'research/gig_restoration/lore_whitelists_v3_broad.json']}|native_hashes,
        'game_writes':0,'save_writes':0}
    result['fingerprint']=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(',',':')).encode()).hexdigest().upper()
    (OUT/'definition.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    entries=[];index={}
    for job in jobs:
        job['entry_indices']=[]
        for e in job['journal_entries']:
            if e['path'] not in index:index[e['path']]=len(entries);entries.append(e)
            job['entry_indices'].append(index[e['path']])
        job['root_index']=index[job['journal_path']]
    out=ROOT/'redscript/PTFR_ActivityStateR3';out.mkdir(parents=True,exist_ok=True)
    def quote(s):return json.dumps(s)
    chunks=['module PTFR.ActivityStateR3','// Generated by tools/catalog_activity_state_r3.py. Observation targets, not adapters.','public class ActivityDefinition {',
        f'  public static func Fingerprint() -> CName {{ return n"{result["fingerprint"]}"; }}',
        f'  public static func JobCount() -> Int32 {{ return {len(jobs)}; }}',
        f'  public static func EntryCount() -> Int32 {{ return {len(entries)}; }}',
        f'  public static func FactCount() -> Int32 {{ return {len(facts)}; }}']
    arrays={'JobIDs':[e['id'] for e in jobs],'JobTitles':[e['selected_title'] for e in jobs],
        'Categories':[e['category'] for e in jobs],'Paths':[e['path'] for e in entries],
        'Classes':[e['className'] for e in entries],'FactNames':sorted(facts)}
    for name,values in arrays.items():
        chunks+=['  public static func '+name+'(page: Int32) -> array<String> {','    switch page {']
        for page,start in enumerate(range(0,len(values),64)):
            chunks.append(f'      case {page}: return ['+', '.join(quote(s) for s in values[start:start+64])+'];')
        chunks+=['    }','    return [];','  }']
    chunks+=['  public static func RootIndex(job: Int32) -> Int32 {','    switch job {']
    chunks += [f'      case {i}: return {job["root_index"]};' for i,job in enumerate(jobs)]
    chunks+=['    }','    return -1;','  }','  public static func JobEntries(job: Int32) -> array<Int32> {','    switch job {']
    chunks += [f'      case {i}: return ['+', '.join(str(n) for n in job['entry_indices'])+'];' for i,job in enumerate(jobs)]
    chunks+=['    }','    return [];','  }','}']
    (out/'ActivityDefinition.generated.reds').write_text('\n'.join(chunks)+'\n',encoding='utf-8')
    print(json.dumps({'entries':len(entries),'facts':len(facts),'side_jobs_with_native_fact_sources':sum(bool(e.get('native_fact_sources')) for e in jobs)},indent=2))
    print(json.dumps({k:v for k,v in result.items() if k not in ('jobs','source_inputs','fact_names')},indent=2))
if __name__=='__main__':main()
