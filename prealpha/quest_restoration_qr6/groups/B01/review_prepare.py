"""Independent review preparation; no imports from investigation workers."""
from pathlib import Path
import json,hashlib,sys,argparse
W=Path(__file__).resolve().parents[4]
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def save(p,x):Path(p).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('group');a=a.parse_args();P=W/'prealpha/quest_restoration_qr6/groups'/a.group;H=W/'prealpha/quest_restoration_qr6/groups/B01/reviews'/a.group;H.mkdir(parents=True,exist_ok=True);assert not(H/'raw_inputs.json').exists();R=read(P/'results.json');inp=[];seen=set()
 for p in R['source_pin_paths']:
  for r in read(p):
   if 'depot'not in r or r['depot']in seen:continue
   raw=r.get('binary',r.get('raw'));h=r.get('sha256',r.get('raw_sha256',r.get('resource_sha256')));assert sha(raw)==h;assert sha(r['json'])==r['json_sha256'];inp.append(dict(depot=r['depot'],raw=raw,hash=h,provider='Exact source-pinned worker readback; independent re-export from unchanged raw'));seen.add(r['depot'])
 save(H/'raw_inputs.json',inp);save(H/'reviewed_input.json',{'results':str(P/'results.json'),'results_sha256':sha(P/'results.json'),'contract_pins':[{'path':r['contracts'],'sha256':sha(r['contracts'])}for r in R['quest_results']],'source_pins':[{'path':p,'sha256':sha(p)}for p in R['source_pin_paths']]});print(a.group,len(inp))
