"""Replay installed-byte contract and mutations into an explicit fresh directory."""
from inspect_archivexl import Binary,DLL,HERE
from verify_binary_contract import verify
import argparse,json,hashlib,struct
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();out=Path(a.output).resolve();out.relative_to(HERE.resolve());out.mkdir(exist_ok=False)
 x=Binary(DLL);checks=verify(x.b,x);mutants=json.loads((HERE/'binary_verification_01/controls.json').read_text());controls=[]
 for c in mutants:
  r=int(c['rva'],16);v=bytes.fromhex(c['after']);b=bytearray(x.b);b[x.off(r):x.off(r)+len(v)]=v
  try:verify(bytes(b),x)
  except AssertionError as err:controls.append({'name':c['name'],'pass':True,'caught_by':str(err)})
  else:raise AssertionError('missed '+c['name'])
 pins=[{'path':str(HERE/name),'sha256':hashlib.sha256((HERE/name).read_bytes()).hexdigest().upper()} for name in ['inspect_archivexl.py','verify_binary_contract.py','binary_verification_01/controls.json','recheck_binary.py']]
 result={'status':'PASS_BOUNDED_BYTE_CONTRACT_REPLAY','input':x.freshness(),'checks':checks,'controls':controls,'checker_pins':pins,'not_runtime_execution':True};(out/'result.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps({'checks':len(checks),'controls':len(controls),'output':str(out)}))
if __name__=='__main__':main()
