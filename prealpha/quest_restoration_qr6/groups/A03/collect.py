from pathlib import Path
import sys
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent/'A01'));from source_lib import *
IDS=['mq017_streetkid','q003_stout','mq036_overload']
if __name__=='__main__':
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);O=Path(ap.parse_args().output);assert not O.exists();S=Store();selection={}
 for q in IDS:
  qr=QUEUE[q];deps=set(qr['restored_candidates']);deps|={d.split('\\native\\',1)[1]for d in list(deps)if '\\native\\'in d};deps|={d for d in qr['vanilla_candidates']if'\\versions\\'not in d};selection[q]=sorted(deps)
  for d in sorted(deps):
   try:S.load(d)
   except KeyError:pass
 write(O/'models.json',S.models);write(O/'source_pins.json',S.pins);write(O/'missing.json',S.missing);write(O/'selection.json',selection);print(dict(resources=len(S.models),missing=S.missing,nodes=sum(len(g['nodes'])for m in S.models.values()for g in m['graphs'].values())))
