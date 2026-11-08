"""Exact complete-input equality gate; no compiler/cache/game writes."""
from pathlib import Path
import sys,argparse
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);ap.add_argument('--epoch',default=str(O/'source_epoch_00.json'));args=ap.parse_args();out=Path(args.output).resolve();assert out.is_relative_to(O)and not out.exists()
cp=W/'prealpha/quest_restoration_qr6/verification/compile_01/result.json';cr=read(cp);assert cr['status']=='PASS_CURRENT_INPUTS_OFFLINE_COMPILED'
e=read(args.epoch);candidate=Path(e['candidate']);mismatches=[]
for p,h in cr['input_pins'].items():
 if not Path(p).is_file()or sha(p)!=h:mismatches.append({'kind':'current_compiler_source_cache_input','path':p,'expected':h,'actual':sha(p)if Path(p).is_file()else None})
for p,r in cr['staged_sources'].items():
 if not Path(p).is_file()or sha(p)!=r['sha256']:mismatches.append({'kind':'prior_compiled_staged_source','path':p})
for r in cr['managed']:
 p=candidate/'package'/r['path']
 if sha(p)!=r['sha256']:mismatches.append({'kind':'candidate_managed_source','path':str(p)})
assert len(list((candidate/'package/r6/scripts').rglob('*.reds')))==len(cr['managed'])
compiled=Path(cr['command'][cr['command'].index('-outputCacheFile')+1]);assert sha(compiled)==cr['compiled_sha256']
write(out/'result.json',{'status':'PASS_EXACT_FULL_INPUT_COMPILE_REUSE'if not mismatches else'INPUT_DRIFT_FRESH_OFFLINE_COMPILE_REQUIRED','prior_actual_compile':str(cp),'prior_actual_compile_sha256':sha(cp),'source_epoch':args.epoch,'source_epoch_sha256':sha(args.epoch),'current_input_pins':len(cr['input_pins']),'prior_staged_sources':len(cr['staged_sources']),'candidate_managed_sources':len(cr['managed']),'actual_prior_compiled_output_sha256':sha(compiled),'mismatches':mismatches,'fresh_SCC_invocation':False,'reason':'Exact current input/source/managed bytes and actual prior output checked. Unchanged resources do not justify rebuilding unchanged script code.','game_writes':0,'save_writes':0})
assert not mismatches,mismatches;print({'status':'PASS_EXACT_FULL_INPUT_COMPILE_REUSE','inputs':len(cr['input_pins']),'sources':len(cr['staged_sources']),'managed':len(cr['managed'])})
