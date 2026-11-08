"""Read-only installed PH3 versus staged QR5 identity and provider snapshot check."""
from pathlib import Path
import sys,argparse
W=Path(__file__).resolve().parents[2];H=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);a=ap.parse_args();O=Path(a.output).resolve();assert not O.exists();O.mkdir(parents=True)
mp=W/'prealpha/phone_studios_ph3/candidate_01/install_manifest_01.json';m=read(mp);G=Path(m['game_root']);checks=[];rows=[]
for r in m['package_files']:
 p=G/r['path'];actual=sha(p);checks.append({'name':'installed PH3 '+r['path'],'status':'PASS'if actual==r['after']else'FAIL','actual':actual,'expected':r['after']});rows.append({'path':str(p),'sha256':actual})
atelier=G/'r6/scripts/virtual-atelier-full/SetupNewTab.reds';expected='5743CDCD6F8CD46A58F9642002F75EBCA25D84BE340856C2E6D85B15DAD973F8'
checks.append({'name':'required external Atelier compatibility bytes','status':'PASS'if sha(atelier)==expected else'FAIL','actual':sha(atelier),'expected':expected})
old=read(W/'prealpha/quest_restoration_qr5/protection_before.json')['game_metadata'];now=read(H/'protection_before.json')['game_metadata']
archives={p:v for p,v in now.items()if p.lower().endswith(('.archive','.archive.xl','.xl'))};oldarchives={p:v for p,v in old.items()if p.lower().endswith(('.archive','.archive.xl','.xl'))}
checks.append({'name':'all archive/XL path size mtime provider inventory unchanged since QR5','status':'PASS'if archives==oldarchives else'FAIL','count':len(archives),'boundary':'All protected selected resource payloads and installed mod archive hashes checked separately. This metadata comparison is not a fresh SHA of every multi-GB stock game archive or new runtime merge evidence.'})
e=read(H/'source_epoch_00.json');C=Path(e['candidate']);installed={r['path']:r['after']for r in m['package_files']};staged={r['path'].replace('\\','/'):r['sha256']for r in e['package_files']};delta=[p for p in staged if installed.get(p)!=staged[p]]
checks.append({'name':'staged QR5 distinct from installed PH3 only archive file','status':'PASS'if delta==['archive/pc/mod/zzzz_PTFR_Combined.archive']else'FAIL','delta':delta})
assert all(x['status']=='PASS'for x in checks),[x for x in checks if x['status']!='PASS']
write(O/'installed_files.json',rows);write(O/'provider_metadata.json',archives);write(O/'checks.json',checks)
write(O/'result.json',{'status':'PASS_INSTALLED_PH3_AND_STAGED_QR5_EXACT_BOUNDARIES','checks':len(checks),'installed_paths':len(rows),'installed_manifest':str(mp),'installed_manifest_sha256':sha(mp),'external_Atelier_sha256':sha(atelier),'staged_candidate':str(C),'provider_metadata_count':len(archives),'native_provider_evidence':'Pinned source manifests/raw payloads from diagnostics/vanilla_parity_20261029_01/analysis_02/resource_inventory.json; exact per-group raw pins and current archive/XL metadata retained. Original archive/provider ambiguities remain explicit.','installed_or_runtime_writes':0})
print({'status':'PASS_INSTALLED_PH3_STAGED_QR5','installed_paths':len(rows),'provider_metadata_count':len(archives)})
