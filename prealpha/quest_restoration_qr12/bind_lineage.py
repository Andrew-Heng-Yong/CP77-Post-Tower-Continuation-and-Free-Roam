"""Hash-bind existing human lineage evidence; names alone never qualify a save."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;W=H.parents[1];Q11=H.parent/'quest_restoration_qr11'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def bound(row,known,baseline):
    if not row['metadata_valid']:return False
    if row['sha256']!=known['files']['sav.dat']['sha256']or row['metadata_sha256']!=known['files']['metadata.9.json']['sha256']:return False
    root=Path(row['source']).parent
    return all(baseline.get(str(root/name))==v['sha256']for name,v in known['files'].items())
def main():
    inv=read(H/'inventory.json');b=read(H/'baseline.json');selected=read(Q11/'save_selection.json')
    known={'ManualSave-23':{'files':selected['ManualSave-23']['files'],'label':'USER_CONFIRMED_MASTER'},
        'ManualSave-24':{'files':selected['ManualSave-24']['files'],'label':'USER_CONFIRMED_WORKING_BRANCH'}}
    available={**b['save_sha256'],**b['backup_sha256']};proof=[]
    for row in inv['rows']:
        row['lineage']='NOT_INDEPENDENTLY_CONFIRMED'
        for slot,k in known.items():
            if bound(row,k,available):
                row['lineage']=k['label']if row['kind']=='GAME_SAVE'and row['slot_directory']==slot else'HASH_IDENTICAL_TO_CONFIRMED_SAVE'
                row['lineage_binding']={'known_slot':slot,'body_metadata_screenshot_hashes':'MATCH_ALL_AVAILABLE_PINNED_FILES','source_manifest':str(Q11/'save_selection.json')}
                proof.append({'source':row['source'],'known_slot':slot,'lineage':row['lineage'],'save_sha256':row['sha256']})
    checks=[]
    real=next(r for r in inv['rows']if r['kind']=='GAME_SAVE'and r['slot_directory']=='ManualSave-24')
    assert bound(real,known['ManualSave-24'],available);checks.append('actual working fixture matches original body/metadata/screenshot pins')
    fake={**real,'sha256':'0'*64};assert not bound(fake,known['ManualSave-24'],available);checks.append('same slot name with wrong body rejected')
    fake={**real,'metadata_sha256':'0'*64};assert not bound(fake,known['ManualSave-24'],available);checks.append('same name/body with wrong metadata rejected')
    fake={**real,'metadata_valid':False};assert not bound(fake,known['ManualSave-24'],available);checks.append('unverified metadata rejected')
    # Root name and q307 metadata cannot create a confirmed lineage without the actual pins.
    missing=dict(available);missing.pop(str(Path(real['source']).parent/'screenshot.png'));assert not bound(real,known['ManualSave-24'],missing);checks.append('missing required file pin rejected')
    p=H/'inventory_verified.json';assert not p.exists();p.write_text(json.dumps(inv,indent=2)+'\n',encoding='utf-8')
    result={'status':'PASS_HASH_BOUND_LINEAGE','bindings':proof,'checks':checks,'source_manifest_sha256':sha(Q11/'save_selection.json'),
        'human_authority':[{'path':str(H.parent/'quest_restoration_qr9/selected_master.json'),'sha256':sha(H.parent/'quest_restoration_qr9/selected_master.json')},
            {'path':str(Q11/'observations/D00E_20261103_01/result.json'),'sha256':sha(Q11/'observations/D00E_20261103_01/result.json')}],
        'limits':'Known exact user-confirmed fixtures only; other same-playthrough/PONR identifiers do not establish exact ancestry. Backup byte identity does not make it a Load Game slot.'}
    (H/'lineage_bindings.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print({'bindings':len(proof),'checks':len(checks)})
if __name__=='__main__':main()
