"""QR12 read-only save/evidence inventory. Fresh outputs only, no game APIs."""
from pathlib import Path
import csv,datetime,hashlib,json,os,re,stat,subprocess,sys
H=Path(__file__).resolve().parent;W=H.parents[1];Q11=H.parent/'quest_restoration_qr11'
sys.path.insert(0,str(H.parent/'quest_restoration_qr10'))
from capture_baseline import meta,sha
SAVE=Path(r'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077')
GAME=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def put(name,x):
    p=H/name;assert not p.exists();p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def safe(p):
    for q in(p,*p.parents):
        s=q.lstat()
        assert not stat.S_ISLNK(s.st_mode)and not(getattr(s,'st_file_attributes',0)&0x400),'Linked input refused:'+str(q)
def metadata(p):
    try:
        x=read(p);assert x['RootType']=='saveMetadataContainer';return x['Data']['metadata']
    except (OSError,ValueError,KeyError,AssertionError):return None
def main():
    assert not(H/'baseline.json').exists(),'Fresh QR12 inventory only'
    ss=meta(SAVE);save_hashes={str(SAVE/p):sha(SAVE/p)for p,r in ss.items()if r['kind']=='file'}
    game_protected={}
    current=read(Q11/'d00e_01/diagnostics_manifest_01.json')
    for r in current['files']+current['required_files']:
        p=GAME/r['path'];safe(p);expected=r.get('after',r.get('sha256'));assert sha(p)==expected;game_protected[str(p)]=expected
    # Existing directory census only; old test fixtures are not real save evidence.
    raw=subprocess.check_output(['rg','--files','-uu','prealpha','research','diagnostics','recovery','-g','sav.dat'],cwd=W,text=True,stderr=subprocess.DEVNULL).splitlines()
    backups=[];excluded=[]
    for name in raw:
        p=W/name;parts=[x.lower()for x in p.parts]
        if any('fixture'in x for x in parts)or 'attch'in parts or any('crash'in x for x in parts):excluded.append({'path':str(p),'reason':'TEST_FIXTURE_OR_CRASH_ATTACHMENT_NOT_LOADABLE_SAVE'});continue
        if p.is_file():backups.append(p)
    sources=[(p/'sav.dat','GAME_SAVE')for p in sorted(SAVE.iterdir())if p.is_dir()and(p/'sav.dat').is_file()]+[(p,'OFFLINE_BACKUP')for p in backups]
    rows=[];backup_pins={}
    for p,kind in sources:
        safe(p);before=p.stat();digest=sha(p);mp=p.parent/'metadata.9.json';m=metadata(mp)if mp.is_file()else None
        if kind=='OFFLINE_BACKUP':backup_pins[str(p)]=digest
        if mp.is_file():safe(mp);backup_pins[str(mp)]=sha(mp)
        with p.open('rb')as f:header=f.read(16).hex().upper()
        after=p.stat();assert(before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns),'Input changed; rerun fresh'
        facts={}
        if m:
            for s in m.get('facts',[]):
                if isinstance(s,str)and'='in s:
                    k,v=s.rsplit('=',1);facts.setdefault(k,[]).append(v)
        rows.append({'source':str(p),'kind':kind,'slot_directory':p.parent.name,'sha256':digest,'bytes':before.st_size,'header16':header,
            'metadata_source':str(mp)if mp.is_file()else None,'metadata_sha256':sha(mp)if mp.is_file()else None,'metadata_valid':m is not None,
            'metadata':{k:m.get(k)for k in['name','timestampString','playthroughID','pointOfNoReturnId','visitID','playTime','playthroughTime','level','debugString','gameVersion','saveVersion','isPointOfNoReturn','isEndGameSave','trackedQuestEntry','activeQuests']}if m else{},
            'finished_quests':m.get('finishedQuests','').split()if m else[],'metadata_facts':facts,
            'lineage':'NOT_INDEPENDENTLY_CONFIRMED'})
    wanted=set();journals={};inputs=[]
    watch=read(GAME/'bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_QR9_Diagnostics/watch.json')
    for profile,c in watch['profiles'].items():
        if profile.startswith('S'):
            wanted.update(c['facts'])
            for j in c.get('journals',[]):journals[j['path']]=j['class']
    signals=read(H.parent/'quest_restoration_qr9/worker_b/signal_catalog.json')
    def walk(x):
        if isinstance(x,dict):
            if 'factName'in x:
                v=x['factName'];v=v.get('$value')if isinstance(v,dict)else v
                if isinstance(v,str)and re.fullmatch('[A-Za-z0-9_]+',v):wanted.add(v)
            for v in x.values():walk(v)
        elif isinstance(x,list):
            for v in x:walk(v)
    for pin in signals['inputs']:
        p=Path(pin['json']);assert sha(p)==pin['json_sha256'];walk(read(p));inputs.append({'path':str(p),'sha256':sha(p),'depot':pin['depot']})
    wanted.update(['q302_ronald_messages_enabled','q302_ronald_contact_added','mq007_skippy_owner_known','mq007_done','mq007_skippy_re_acquiring_done',
        'PTFRS23_MQ007_Issued','PTFRS23_MQ007_ModeTalkConfirmed','carbought_counter','mq037_brendan_introduced','mq037_done'])
    # Use source journal definitions from the existing live catalog, not invented paths.
    snapdir=GAME/'bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_HistorySnapshotHS1'
    snapshots=sorted(snapdir.glob('snapshot_hs1_*.json'))
    for p in snapshots[-3:]:
        for r in read(p)['rows']:
            if r['definition']['id']in('mq007_smartgun','mq037_brendan','mq037_brendan_hooligan001','sts_pac_cvi_02','mq060_nitro'):
                wanted.update(r['definition']['fact_names'])
                for v in r['definition']['journals']:
                    if isinstance(v,list):journals[v[0]]=v[1]
        inputs.append({'path':str(p),'sha256':sha(p),'scope':'post-ending fallback, no exact save-slot binding or earned-history certificate'})
    unique={}
    for r in rows:unique.setdefault(r['sha256'],r)
    put('catalogue.json',{'facts':sorted(wanted),'journals':[{'path':p,'class':c}for p,c in sorted(journals.items())],'sources':inputs})
    put('inventory.json',{'rows':rows,'excluded_backups':excluded,'counts':{'game_slots':sum(r['kind']=='GAME_SAVE'for r in rows),'offline_backups':len(backups),'unique_bodies':len(unique)},
        'bounds':'Offline backups are not assumed loadable or genuine; fixture/crash attachments excluded. Same playthrough/PONR IDs are correlation, not ancestry.'})
    put('baseline.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'save_sha256':save_hashes,'save_metadata':ss,'backup_sha256':backup_pins,
        'game_protected_sha256':game_protected,'game_metadata':meta(GAME),'prior_QR11_metadata':meta(Q11),'old_QR9_metadata':meta(H.parent/'quest_restoration_qr9'),'old_QR10_metadata':meta(H.parent/'quest_restoration_qr10')})
    put('parse_jobs.json',{'jobs':[{'source':r['source'],'sha256':r['sha256'],'metadata':r['metadata_source'],'metadata_sha256':r['metadata_sha256']}for r in unique.values()]})
    print({'slots':sum(r['kind']=='GAME_SAVE'for r in rows),'backups':len(backups),'unique_bodies':len(unique),'wanted_facts':len(wanted),'journals':len(journals)})
if __name__=='__main__':main()
