"""Fresh read-only before/after evidence for the single-profile update."""
from pathlib import Path
import hashlib,json,sys
H=Path(__file__).resolve().parent;P=H.parent
sys.path.insert(0,str(P.parent/'quest_restoration_qr10'))
from capture_baseline import meta,sha
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def main():
    stage=sys.argv[1];assert stage in('before','after');out=H/'deployment_01'
    m=read(H/'diagnostics_manifest_01.json');game=Path(m['game_root']);save=Path(m['save_root'])
    if stage=='before':assert not out.exists();out.mkdir()
    target=out/(stage+'.json');assert not target.exists()
    base=read(P/'deployment_01/after.json')['protected_sha256'];watch=game/m['files'][0]['path'];protected={}
    for p,v in base.items():
        expected=m['files'][0]['after']if stage=='after'and Path(p)==watch else v
        assert sha(p)==expected,('protected drift',p);protected[p]=expected
    data={'protected':protected,'saves':{p:sha(save/p)for p,r in meta(save).items()if r['kind']=='file'},'save_metadata':meta(save),'game_metadata':meta(game),
        'old_QR9':meta(P.parent/'quest_restoration_qr9'),'old_QR10':meta(P.parent/'quest_restoration_qr10')}
    if stage=='after':
        b=read(out/'before.json');assert data['saves']==b['saves']and data['save_metadata']==b['save_metadata']
        assert data['old_QR9']==b['old_QR9']and data['old_QR10']==b['old_QR10']
        changed=[p for p in set(b['game_metadata'])|set(data['game_metadata'])if b['game_metadata'].get(p)!=data['game_metadata'].get(p)]
        assert changed==[m['files'][0]['path']]
        result={'status':'PASS_SINGLE_PROFILE_DEPLOYMENT_PRESERVATION','changed_game_paths':changed,'save_files_unchanged':len(data['saves']),
            'protected_files_verified':len(protected),'Lua_Core_dependencies':'UNCHANGED','old_evidence':'UNCHANGED_METADATA_AND_PINNED_HASHES','native_callbacks':'UNSUPPORTED_NOT_VERIFIED','live_sampling':'NOT_TESTED',
            'limits':'All save/protected bytes and full game/old-evidence metadata compared; unpinned bulk not all byte-hashed.'}
        (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    target.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8');print({'stage':stage,'saves':len(data['saves']),'protected':len(protected)})
if __name__=='__main__':main()
