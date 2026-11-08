"""Read-only QR12 before/after verification; only creates a fresh local receipt."""
from pathlib import Path
import concurrent.futures,datetime,json,sys
H=Path(__file__).resolve().parent;W=H.parents[1]
sys.path.insert(0,str(H.parent/'quest_restoration_qr10'))
from capture_baseline import meta,sha
SAVE=Path(r'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077')
GAME=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def main():
    dest=H/'preservation.json';assert not dest.exists()
    b=read(H/'baseline.json');checks=[]
    for label,root,key in [('save',SAVE,'save_metadata'),('game',GAME,'game_metadata'),('QR9',H.parent/'quest_restoration_qr9','old_QR9_metadata'),('QR10',H.parent/'quest_restoration_qr10','old_QR10_metadata'),('QR11',H.parent/'quest_restoration_qr11','prior_QR11_metadata')]:
        after=meta(root);before=b[key]
        assert after==before,(label,'file name/size/mtime/type drift')
        checks.append({'scope':label,'result':'MATCH_ALL_FILE_NAMES_SIZES_MTIMES_TYPES','file_entries':len(before)})
    pins={}
    for name in ['save_sha256','backup_sha256','game_protected_sha256']:
        for p,digest in b[name].items():
            if p in pins:assert pins[p]==digest
            pins[p]=digest
    with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:
        actual=dict(zip(pins,pool.map(lambda p:sha(Path(p)),pins)))
    assert actual==pins,'Pinned bytes drift'
    jobs=read(H/'parse_jobs.json')['jobs']
    assert all(actual[j['source']]==j['sha256']and actual[j['metadata']]==j['metadata_sha256']for j in jobs)
    for r in read(H/'catalogue.json')['sources']:
        assert sha(Path(r['path']))==r['sha256'],'Source evidence drift'
    assert not read(H/'analysis_final_02/runtime_test_queue.json')['ready']
    result={'status':'PASS_READ_ONLY_PRESERVATION','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'baseline_sha256':sha(H/'baseline.json'),
        'saved_files_sha256_matched':len(b['save_sha256']),'backup_and_metadata_pins_matched':len(b['backup_sha256']),
        'installed_protected_sha256_matched':len(b['game_protected_sha256']),'unique_saved_body_inputs_reverified':len(jobs),
        'metadata_checks':checks,'scope':'All current save files byte checked; retained body/metadata pins checked. Complete game/QR9/QR10/QR11 metadata checked, not a full-byte census of every external file. Backup screenshots not universally byte-pinned.',
        'operations':{'game_launches':0,'CUA_calls':0,'installations':0,'runtime_resource_changes':0,'save_or_fact_writes':0,'diagnostic_implementation_changes':0,'core_builds':0}}
    dest.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(result)
if __name__=='__main__':main()
