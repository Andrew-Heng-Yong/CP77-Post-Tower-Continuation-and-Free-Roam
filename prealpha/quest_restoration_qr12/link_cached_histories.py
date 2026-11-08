"""Bind saved cache references, explicitly separate cached history from live state."""
from pathlib import Path
import hashlib,json,re
H=Path(__file__).resolve().parent
GAME=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def unbox(x):
    if isinstance(x,dict)and'$value'in x:return unbox(x['$value'])
    return x
def main():
    result=[]
    for p in [H/'history_master_01.json',H/'history_package_verified_02.json']:
        x=read(p);r=next(r for r in x['rows']if r['class']=='PTFR.HistorySnapshotHS1.SnapshotStateHS1');d=json.loads(r['decoded_json'])
        fields={k:unbox(v)for k,v in d.items()if not k.startswith('$')};token=fields['fileToken'];assert re.fullmatch(r'[0-9TZ_]+',token)
        target=GAME/'bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_HistorySnapshotHS1'/('snapshot_hs1_'+token+'.json')
        item={'saved_body':x['source'],'saved_sha256':x['sha256'],'fields':fields,'package_output_sha256':sha(p),'snapshot_exists':target.exists(),
            'meaning':'Saved pointer/catalogue/revision compatibility, not cryptographic historical snapshot content binding or current journal/owner state. ready1 means cached data exists, not a READY test fixture.'}
        if target.exists():
            s=read(target);assert s['catalogue']==fields['catalogue']and s['revision']==fields['revision']and s['origin']==fields['origin']
            item['referenced_snapshot']={'path':str(target),'sha256':sha(target),'origin':s['origin'],'revision':s['revision']}
        assert fields['origin']=='post_ending_fallback';item['earned_pre_tower_certificate']='NOT_ESTABLISHED_BY_POST_ENDING_CACHE';result.append(item)
    dest=H/'saved_cache_bindings.json';assert not dest.exists();dest.write_text(json.dumps({'status':'CACHED_FALLBACK_IDENTITIES_VERIFIED_NOT_LIVE_STATE','rows':result},indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
