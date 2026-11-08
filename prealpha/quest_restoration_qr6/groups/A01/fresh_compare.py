from pathlib import Path
import sys,copy,collections
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H));from source_lib import *
def leaves(a,b,p=''):
 if type(a)!=type(b):return[dict(path=p,before=a,after=b)]
 if isinstance(a,dict):
  out=[]
  for k in sorted(set(a)|set(b)):
   if k not in a or k not in b:out.append(dict(path=p+'/'+k,before=a.get(k),after=b.get(k)))
   else:out+=leaves(a[k],b[k],p+'/'+k)
  return out
 if isinstance(a,list):
  if len(a)!=len(b):return[dict(path=p,before_count=len(a),after_count=len(b))]
  return[z for i,(x,y)in enumerate(zip(a,b))for z in leaves(x,y,p+'/'+str(i))]
 return[]if a==b else[dict(path=p,before=a,after=b)]
if __name__=='__main__':
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);O=Path(ap.parse_args().output);assert not O.exists();M={};pins=read(H/'readback_01/manifest.json')
 for p in pins:
  assert sha(p['binary'])==p['sha256']and sha(p['json'])==p['json_sha256'];M[p['depot']]=Resource(read(p['json'])).normalize()
 pref='towercontinued\\sidejobs_s29\\native\\';reloc={d[len(pref):]:d for d in E['source_resources']if d.startswith(pref)};out=[]
 for orig,d in [(d[len(pref):],d)for d in M if d.startswith(pref)]:
  a=canon(M[orig],reloc);b=canon(M[d]);dif=leaves(a,b);out.append(dict(vanilla=orig,current=d,diffs=dif))
 write(O/'comparisons.json',out);write(O/'models.json',M);write(O/'source_pins.json',pins)
 for r in out:
  print(r['current'],len(r['diffs']));print(r['diffs'][:20])
