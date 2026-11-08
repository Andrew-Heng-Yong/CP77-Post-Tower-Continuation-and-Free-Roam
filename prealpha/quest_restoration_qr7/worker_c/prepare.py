"""Capture the eight QR6 UNKNOWN contracts and verify their exact baseline.

Read-only outside this worker's fresh output tree. No production imports.
"""
from pathlib import Path
import hashlib, json, argparse

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
Q6 = ROOT / 'prealpha/quest_restoration_qr6'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

def main(out):
    assert not out.exists(), out
    epoch_path = Q6 / 'source_epoch_00.json'
    assert sha(epoch_path) == 'A532E6F1CD46B898259F78FD4D303E31C7BDC14EC1774FA2EA3875CFF1B23BC2'
    epoch = read(epoch_path)
    matrix_path = Q6 / 'contract_status_matrix.json'
    rows = [x for x in read(matrix_path) if x['status']=='UNKNOWN']
    expected = {
        ('mq060_nitro','entry'), ('mq060_nitro','eligibility'), ('mq060_nitro','shared_dependencies'),
        ('mws_wat_08_trauma_drama','persistence'), ('sts_std_rcr_02','shared_dependencies'),
        ('q304_splinter_stash','eligibility'), ('q304_splinter_stash','completion_rewards_cleanup'),
        ('q304_splinter_stash','persistence'),
    }
    assert {(x['quest_id'],x['stage']) for x in rows} == expected
    candidate = Path(epoch['candidate'])
    targets = [d for d in epoch['source_resources'] if any(n in d for n in
        ('mq060','mws_wat_08','sts_std_rcr_02','voodoo_boot','slider_stash'))]
    pins = []
    for depot in sorted(targets):
        p = candidate / 'archive_source' / depot.replace('\\','/')
        actual = sha(p)
        assert actual == epoch['source_resources'][depot], depot
        pins.append({'depot':depot,'path':str(p),'sha256':actual})
    scripts = []
    for name in ('PTFR_SideJobsS23.reds','PTFR_SideJobsS29.reds','PTFR_HistorySnapshotHS1.reds'):
        p = candidate / 'package/r6/scripts/PTFR_Consolidated' / name
        scripts.append({'path':str(p),'sha256':sha(p)})
    historical = sorted({x['findings_source'] for x in rows})
    prior = [{'path':p,'sha256':sha(p)} for p in historical]
    for row in rows:
        assert sha(row['findings_source']) == row['findings_source_sha256']
    game = Path('C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077')
    binary = []
    for relative in ('r6/cache/final.redscripts','bin/x64/Cyberpunk2077.exe','r6/cache/tweakdb.bin','r6/cache/tweakdb_ep1.bin'):
        p=game/relative
        binary.append({'path':str(p),'sha256':sha(p),'length':p.stat().st_size})
    write(out/'original_unknowns.json',rows)
    write(out/'baseline.json',{'status':'PINNED_EIGHT_UNKNOWN_CONTRACTS','epoch':str(epoch_path),
        'epoch_sha256':sha(epoch_path),'matrix':str(matrix_path),'matrix_sha256':sha(matrix_path),
        'candidate':str(candidate),'source_pins':pins,'scripts':scripts,'original_findings':prior,
        'current_game_read_only_inputs':binary,'limits':['Installed PH3 is separate from the staged candidate.',
        'No game launch, saves, facts, runtime, release or existing evidence changed.']})
    print(json.dumps({'unknowns':len(rows),'resource_pins':len(pins),'out':str(out)}))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True)
    main(ap.parse_args().output)
