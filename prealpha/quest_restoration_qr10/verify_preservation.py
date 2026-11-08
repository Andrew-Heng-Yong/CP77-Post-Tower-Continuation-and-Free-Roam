"""Final QR10 read-only preservation and artifact verification. Fresh task result only."""
from pathlib import Path
import argparse, datetime, json
from capture_baseline import meta, sha
from preflight import fresh_output, read
H=Path(__file__).resolve().parent

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);a=ap.parse_args();out=fresh_output(a.out)
    b=read(H/'baseline.json');failures=[]
    for p,digest in b['protected_sha256'].items():
        if sha(p)!=digest:failures.append({'protected_hash':p})
    for p,digest in b['save_sha256'].items():
        if sha(p)!=digest:failures.append({'save_hash':p})
    for key,root in [('game_metadata',b['game_root']),('save_metadata',b['save_root']),('QR9_metadata',str(H.parent/'quest_restoration_qr9'))]:
        current=meta(Path(root));before=b[key]
        changes=[p for p in set(current)|set(before)if current.get(p)!=before.get(p)]
        if changes:failures.append({key:changes})
    manifest=read(H/'manifest_02.json')
    for row in manifest['files']:
        assert sha(row['source'])==row['after_sha256']
        assert sha(Path(b['game_root'])/row['path'])==row['before_sha256']
    review=read(H/'review/addendum_result_02.json')
    assert review['manifest_sha256']==sha(H/'manifest_02.json')
    assert review['preflight_sha256']==sha(H/'preflight.py')
    assert review['preflight_test_sha256']==sha(H/'test_preflight.py')
    for row in read(H/'provenance.json')['local_inputs']:assert sha(row['path'])==row['sha256']
    game=Path(b['game_root'])/'bin/x64/Cyberpunk2077.exe'
    assert sha(game)=='D36E74C47592E9C656AE250078CB40B2BE63C782AF5BFBEFF2280D43E653FAB4'
    result={'status':'PASS_PRESERVATION'if not failures else'FAIL','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'baseline_sha256':sha(H/'baseline.json'),'protected_sha256_count':len(b['protected_sha256']),
        'save_files_byte_equal':len(b['save_sha256']),'game_metadata_entries_unchanged':len(b['game_metadata']),
        'QR9_metadata_entries_unchanged':len(b['QR9_metadata']),'failures':failures,
        'installed_diagnostics':'QR9B04 unchanged; QR10D01 not installed','core':'QR8:02 unchanged',
        'limitations':'Full save/protected-file hashes + complete before/after game/QR9 metadata. Unpinned game/QR9 bulk files were not all byte-hashed. Actions were confined to workspace diagnostics/docs.'}
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(result)
    assert not failures

if __name__=='__main__':main()
