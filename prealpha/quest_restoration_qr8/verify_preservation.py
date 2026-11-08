"""Compare QR8-start protected bytes and complete game/save metadata, read-only."""
from pathlib import Path
import sys,argparse,concurrent.futures,datetime,hashlib,subprocess
W=Path(__file__).resolve().parents[2];H=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,tree_metadata
ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);a=ap.parse_args();O=Path(a.output).resolve();assert not O.exists();O.mkdir(parents=True)
b=read(H/'protection_before.json');prep=read(H/'prepared.json');checks=[]
def pin(item):
 p,r=item;p=Path(p)
 if not p.is_file():return {'path':str(p),'reason':'missing protected file'}
 h=sha(p)
 return None if h==r['sha256']else{'path':str(p),'expected':r['sha256'],'actual':h}
with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:diff=[x for x in pool.map(pin,b['files'].items())if x]
def meta_delta(before,after):return [{'path':p,'before':before.get(p),'after':after.get(p)}for p in sorted(set(before)|set(after))if before.get(p)!=after.get(p)]
game=tree_metadata(prep['game']);saves=tree_metadata(b['save_root']);gd=meta_delta(b['game_metadata'],game);sd=meta_delta(b['save_metadata'],saves)
old=read(H/'workspace_before.json');git=['git','-c','safe.directory='+str(W).replace('\\','/')];head=subprocess.check_output(git+['rev-parse','HEAD'],cwd=W,text=True).strip();branch=subprocess.check_output(git+['branch','--show-current'],cwd=W,text=True).strip();dh=hashlib.sha256(subprocess.check_output(git+['diff','--binary'],cwd=W)).hexdigest().upper()
compile=read(W/'prealpha/quest_restoration_qr6/verification/compile_01/result.json');cd=[{'path':p,'expected':h,'actual':sha(p)if Path(p).is_file()else None}for p,h in compile['input_pins'].items()if not Path(p).is_file()or sha(p)!=h]
write(O/'discrepancies.json',{'protected_hashes':diff,'game_metadata':gd,'save_metadata':sd,'compile_inputs':cd})
status='PASS'if not(diff or gd or sd or cd)and head==old['head']and branch==old['branch']and dh==old['tracked_diff_sha256']else'FAIL'
out={'status':status,'captured_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'protected_sha256_files':len(b['files']),'protected_hash_differences':len(diff),'whole_game_metadata_files':len(game),'whole_save_metadata_files':len(saves),'game_metadata_differences':len(gd),'save_metadata_differences':len(sd),'current_compile_input_pins_rechecked':len(compile['input_pins']),'compile_input_differences':len(cd),'branch':branch,'head':head,'tracked_diff_unchanged':dh==old['tracked_diff_sha256'],'tracked_diff_sha256':dh,'game_writes':0,'save_writes':0,'staged_resource_deltas':len(read(read(H/'queue.json')['source_epoch_manifest']).get('changes',[])),'starting_snapshot':str(H/'protection_before.json'),'starting_snapshot_sha256':sha(H/'protection_before.json'),'preexisting_external_drift':str(H/'external_drift_since_QR7.json'),'scope':'All named protected files byte-hashed, complete game/save filenames+sizes+mtimes compared; not a SHA of every unlisted multi-GB game file. Current-session baseline preserves external changes already present before QR8.'}
write(O/'result.json',out);assert status=='PASS',out;print({k:out[k]for k in ['status','protected_sha256_files','game_metadata_differences','save_metadata_differences','current_compile_input_pins_rechecked','tracked_diff_unchanged']})
