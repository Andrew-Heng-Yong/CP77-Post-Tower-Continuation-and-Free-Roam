"""Pin existing earlier saves/installed observer; copy evidence only to workspace."""
from pathlib import Path
import hashlib,json,stat
H=Path(__file__).resolve().parent
SAVE=Path(r'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077')
GAME=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
def safe(p):
    for v in(p,*p.parents):
        s=v.lstat();assert not stat.S_ISLNK(s.st_mode)and not(getattr(s,'st_file_attributes',0)&0x400),'Linked source refused'
def main():
    out=H/'jinguji_replay_01';assert not out.exists();out.mkdir()
    inv=read(H/'analysis_final_02/verified_fixture_inventory.json');manifest=H.parent/'quest_restoration_qr11/d00e_01/diagnostics_manifest_01.json'
    installed=[]
    for r in read(manifest)['files']+read(manifest)['required_files']:
        p=GAME/r['path'];safe(p);expected=r.get('after',r.get('sha256'));actual=sha(p);assert actual==expected,('Installed drift',p)
        installed.append({'path':str(p),'sha256':actual})
    rows=[]
    for slot in ['AutoSave-18','AutoSave-3']:
        r=next(x for x in inv['rows']if x['kind']=='GAME_SAVE'and x['slot_directory']==slot)
        assert 'q307'in r['finished_quests']and'mq030'not in r['finished_quests']
        source=SAVE/slot;target=out/'saved_inputs'/slot;target.mkdir(parents=True)
        files=[]
        for name in ['sav.dat','metadata.9.json','screenshot.png']:
            p=source/name;safe(p);before=sha(p)
            if name=='sav.dat':assert before==r['sha256']
            if name=='metadata.9.json':assert before==r['metadata_sha256']
            d=target/name;d.write_bytes(p.read_bytes());assert sha(d)==before==sha(p),'Unstable source copy'
            files.append({'source':str(p),'copy':str(d),'sha256':before})
        facts={n:vs for n,vs in r['saved_parse']['facts'].items()if n.startswith(('mq030','PTFRS23_MQ030','PTFRB0ZAN'))or n in ['q307_done','q307_finished','q307_2079','q307_main_game_killed','PostTowerFreeRoamActive']}
        rows.append({'slot':slot,'timestamp':r['metadata']['timestampString'],'debug':r['metadata']['debugString'],'files':files,'facts':facts,
            'lineage':'CORROBORATED_POST_TOWER_CANDIDATE_NOT_INDEPENDENT_USER_CERTIFICATION','reason':'Pinned body/metadata, positive native Tower completion/2079/continuation facts, matching prior working-run timeline. Shared IDs alone were not used as proof.',
            'limits':'Native executing owners/journal enums not decoded. Saved fact absence is not live zero. User must verify expected Jinguji state after normal load; no force-entry/reset.'})
    lua=GAME/'bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_QR9_Diagnostics/init.lua';watch=GAME/'bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_QR9_Diagnostics/watch.json';cfg=read(watch)
    assert len(cfg['profiles']['S05']['facts'])==32
    result={'status':'PINNED_EARLIER_SAVE_CANDIDATES_FOR_USER_REQUESTED_REPLAY','user_authority':'User explicitly proposed earlier-save Jinguji replay after previous successes; no assistant game operation authorized/performed.',
        'primary':'AutoSave-18, 2November2026 16:20:12','pending_stage_alternative':'AutoSave-3, 2November2026 16:33:46','candidates':rows,
        'installed_manifest':str(manifest),'installed_manifest_sha256':sha(manifest),'installed_files_verified':installed,
        'observer':{'init_lua_sha256':sha(lua),'watch_json_sha256':sha(watch),'profile':'S05','facts':cfg['profiles']['S05']['facts'],'journal':cfg['profiles']['S05']['journals'],
            'start':'GetMod("PTFR_QR9_Diagnostics").start("S05", "QR12-Jinguji-Replay", 900)','stop':'GetMod("PTFR_QR9_Diagnostics").stop("QR12_JINGUJI_DONE")','limit_seconds':900,'sample_interval_seconds':2},
        'coverage_purpose':'User-requested encounter replay with validated S05 getter sampling through activation/MaxTac/cleanup. Existing functional completion/vendor/reload successes retained. AutoSave3 is only a separate pending-stage-resume candidate, not proof of owner retirement or a requested extra test yet.',
        'next':'Follow NEXT_STEPS.md. No install/rebuild, fact/save edits or assistant launch/control.',
        'game_or_save_source_writes':0,'diagnostic_runtime_changes':0,'assistant_game_launches_or_CUA':0,
        'copy_limit':'Evidence copies are outside the save root and not Load Game slots. No restore is requested or executed. Human play may rotate actual autosaves; master/current manual saves must not be overwritten.'}
    (out/'fixture_manifest.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print({'status':result['status'],'installed_hashes_matched':len(installed),'save_sources_copied_unchanged':len(rows),'profile':'S05','facts':32})
if __name__=='__main__':main()
