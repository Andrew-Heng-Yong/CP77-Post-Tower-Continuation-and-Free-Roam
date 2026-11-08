import argparse
from pathlib import Path
def main():
 p=argparse.ArgumentParser(description='Read-only PTFR static parity auditing; fresh output required.')
 p.add_argument('stage',choices=['prepare','refine','analyze','review','protect'])
 p.add_argument('--workspace',type=Path,default=Path.cwd());p.add_argument('--out',type=Path,required=True)
 p.add_argument('--candidate',default='prealpha/phone_studios_ph3/candidate_01')
 p.add_argument('--capture',default='pass_02/capture.json');p.add_argument('--next-pass',default='pass_03')
 p.add_argument('--reuse-models',type=Path)
 a=p.parse_args();w=a.workspace.resolve();o=a.out.resolve();assert o.is_relative_to(w/'diagnostics'),'Audit outputs must be under diagnostics'
 o.mkdir(parents=True,exist_ok=True)
 if a.stage=='prepare':
  from prepare import prepare
  prepare(w,o,a.candidate)
 elif a.stage=='refine':
  from refine import refine
  refine(w,o,a.capture,a.next_pass)
 elif a.stage=='analyze':
  from engine import analyze
  analyze(w,o,a.reuse_models.resolve() if a.reuse_models else None)
 elif a.stage=='review':
  from review import review
  review(w,o)
 else:
  from protect import verify
  verify(w,o)
if __name__=='__main__':main()
