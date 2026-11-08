"""Coordinator-only immutable shared-evidence registration."""
from pathlib import Path
import sys,argparse
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
a=argparse.ArgumentParser();a.add_argument('--id',required=True);a.add_argument('--path',required=True);a.add_argument('--applies',required=True);x=a.parse_args()
p=Path(x.path).resolve();assert p.is_file();r=read(O/'shared_evidence_registry.json');assert x.id not in {z['id']for z in r['items']}
r['items'].append({'id':x.id,'path':str(p),'sha256':sha(p),'applies_to':x.applies,'review':'Original source checks only; independent group applicability/peer review required'})
write(O/'shared_evidence_registry.json',r);print({'id':x.id,'sha256':sha(p)})
