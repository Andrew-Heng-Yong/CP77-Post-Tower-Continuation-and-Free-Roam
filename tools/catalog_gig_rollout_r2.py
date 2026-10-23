"""Join the approved 71 titles to stock journal entries and native resources.

Generated catalogue/audit only; no game/save/runtime writes. Fail on ambiguous
title matches rather than guessing an ID from a wiki title or tier name.
"""
import hashlib, json, re, unicodedata
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'research/gig_restoration'
OUT=BASE/'rollout_r2'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def normalize(s):
    s=unicodedata.normalize('NFKC',s).replace('’',"'").replace('…','...')
    return re.sub(r'[^a-z0-9]','',s.lower().removeprefix('gig: '))
def walk(v):
    if isinstance(v,dict):
        yield v
        for x in v.values():yield from walk(x)
    elif isinstance(v,list):
        for x in v:yield from walk(x)
def handles(obj):return {v['HandleId']:v['Data'] for v in walk(obj) if 'HandleId'in v and 'Data'in v}
def value(v):return v.get('$value',v.get('value')) if isinstance(v,dict) else v
def deref(v,h):return v.get('Data',h.get(v.get('HandleRefId'),v)) if isinstance(v,dict) else v
def journal(jp,localization):
    obj=read(jp);h=handles(obj);entries=[]
    def visit(wrapper,path):
        n=deref(wrapper,h);key=n.get('id','');path=path+([key] if key else [])
        if n.get('$type')=='gameJournalQuest' and n.get('type')=='StreetStory':
            loc=value(n.get('title'));locid=str(loc).removeprefix('LocKey#')
            nodes=[]
            def collect(w,p):
                e=deref(w,h);id=e.get('id','');ep=p+([id] if id else [])
                if e.get('$type') in ('gameJournalQuest','gameJournalQuestPhase','gameJournalQuestObjective','gameJournalQuestDescription'):
                    nodes.append({'path':'/'.join(ep),'className':e['$type'],'id':id})
                for child in e.get('entries',[]):collect(child,ep)
            collect(wrapper,path[:-1])
            entries.append({'id':key,'title':localization.get(locid),'title_key':loc,'journal_path':'/'.join(path),'journal_entries':nodes})
        for child in n.get('entries',[]):visit(child,path)
    visit(obj['Data']['RootChunk']['entry'],[])
    return entries
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    jp=[BASE/'journal_sources/json/base/journal/cooked_journal.journal.json',ROOT/'research/phase2b_p2/extracted/json/ep1/journal/cooked_journal.journal.json']
    locpaths=[ROOT/'research/misty_viktor_world/bradbury_localization/json/base/localization/en-us/onscreens/onscreens.json.json',ROOT/'research/misty_viktor_world/street_localization/json/ep1/localization/en-us/onscreens/onscreens.json.json']
    loc={}
    for p in locpaths:
        for e in read(p)['Data']['RootChunk']['root']['Data']['entries']:loc[str(e['primaryKey'])]=e['femaleVariant']
    entries=[e for p in jp for e in journal(p,loc)]
    bytitle={}
    for e in entries:
        if e['title']:bytitle.setdefault(normalize(e['title']),[]).append(e)
    selected=read(BASE/'lore_whitelists_v3_broad.json')['ignore_two_year_gap']['gigs']
    assert len(selected)==71 and len(set(selected))==71
    jobs=[]
    for title in selected:
        matches=bytitle.get(normalize(title),[])
        assert len(matches)==1,(title,[(e['id'],e['title']) for e in matches])
        e=dict(matches[0]);e['selected_title']=title;jobs.append(e)
    sources=[BASE/'watson_sources/json',BASE/'fresh_candidates/local_sources/json',BASE/'expanded_sources/json',OUT/'native_sources/json']
    library={};inputhashes={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in jp+locpaths+[BASE/'lore_whitelists_v3_broad.json']}
    for src in sources:
        if not src.exists():continue
        for p in src.rglob('*.json'):
            obj=read(p);name=str(p.relative_to(src))[:-5].replace('/','\\')
            library[name]={'content':obj['Data']['RootChunk'],'source':str(p.relative_to(ROOT)).replace('\\','/'),'embedded_index':None,'sha256':sha(p)}
            for i,e in enumerate(obj['Data'].get('EmbeddedFiles',[])):
                library[value(e['FileName'])]={'content':e['Content'],'source':str(p.relative_to(ROOT)).replace('\\','/'),'embedded_index':i,'sha256':sha(p)}
    allfacts=set(('PostTowerFreeRoamActive','PTFRP0_DR13','q307_active','q307_done','q307_finished','q307_2079','q307_main_game_killed','q307_ep1_killed','q115_point_of_no_return','q307_point_of_no_return','wat_sts_counter','cct_sts_counter','std_sts_counter','wbr_sts_counter','hey_sts_counter','bls_sts_counter','pac_sts_counter','ep1_sts_counter','wat_achievement','PTFRG1_Started','PTFRG1_RewardClaim','PTFRG1_RewardAck','PTFRG1_OwnerFinished','PTFRG1_CounterAck'))
    rows=[]
    for e in jobs:
        id=e['id'];known={n:d for n,d in library.items() if re.search(r'\\'+re.escape(id)+r'(?:\\|\.|_)',n)}
        # EP1 06 folder includes a suffix; source-owned journal paths remain exact.
        if not known:
            known={n:d for n,d in library.items() if id in n}
        facts=set();scenes=set();journalpaths=set();rewards=set();hazards=set();native=[]
        for name,data in known.items():
            native.append({k:v for k,v in data.items() if k!='content'}|{'depot_path':name})
            for v in walk(data['content']):
                if isinstance(v.get('factName'),str):facts.add(v['factName'])
                if isinstance(v.get('realPath'),str):journalpaths.add(v['realPath'])
                if 'sceneFile'in v:
                    s=value(v['sceneFile'].get('DepotPath'))
                    if s and s!='0':scenes.add(s)
                if v.get('$type')=='questGiveReward_NodeType':
                    rewards.update(str(value(x)) for x in v.get('rewards',[]))
                if v.get('$type') in ('questInjectLoot_NodeType','questGiveItem_NodeType','questAddRemoveItem_NodeType','questStartQuest_NodeType'):hazards.add(v['$type'])
        e['fact_names']=sorted(facts);allfacts|=facts
        e['native_resources']=native;e['scene_resources']=sorted(scenes)
        e['reward_records']=sorted(rewards);e['initialization_review_types']=sorted(hazards)
        e['native_journal_paths']=sorted(journalpaths)
        e['external_story_facts']=sorted(f for f in facts if f.startswith(('q','sq','mq')))
        e['source_coverage']='RESOLVED_NATIVE_RESOURCES_NOT_RUNTIME_ADMISSION' if known else 'NATIVE_RESOURCES_NOT_YET_EXTRACTED'
        for d in known.values():inputhashes[d['source']]=d['sha256']
        rows.append(e)
    # Also capture authored district entry-gate/fixer-loop facts, not guessed tiers.
    for data in library.values():
        for v in walk(data['content']):
            if isinstance(v.get('factName'),str):allfacts.add(v['factName'])
    allfacts={f for f in allfacts if re.fullmatch('[A-Za-z0-9_]+',f)}
    result={'schema':1,'status':'71_SELECTED_CATALOGUE_NOT_RESTORED','selected_whitelist':'ignore_two_year_gap','jobs':rows,'count':len(rows),'fact_names':sorted(allfacts),'source_inputs':inputhashes,'game_writes':0,'save_writes':0,'runtime_ready':False}
    result['fingerprint']=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(',',':')).encode()).hexdigest().upper()
    (OUT/'catalogue.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'count':len(rows),'native_resources_resolved':sum(bool(j['native_resources']) for j in rows),'journal_entries':sum(len(j['journal_entries']) for j in rows),'facts':len(allfacts),'missing_native':[j['selected_title'] for j in rows if not j['native_resources']]},indent=2))
if __name__=='__main__':main()
