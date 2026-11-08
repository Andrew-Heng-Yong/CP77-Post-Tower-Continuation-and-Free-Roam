"""Verify fresh current providers against every approved CVI native donor byte."""
from pathlib import Path
import sys,collections
H=Path(__file__).resolve().parent;W=H.parents[2];sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
def run(o):
 assert not o.exists();mp=H/'current_native_donors_01/manifest.json';m=read(mp);T=[]
 def ck(n,b,e=None):T.append({'name':n,'pass':bool(b),'evidence':e});assert b,n
 ck('approved proposal plan still exact',sha(Path(m['approved_plan']))==m['approved_plan_sha256']);ck('all six requested depots have at least one extracted current provider',set(m['depots'])=={x['depot']for x in m['providers']}and len(m['depots'])==6);ck('all current archive indexes read successfully',len(m['archive_index_inventory'])==134 and all(x['read_status']=='NoError'for x in m['archive_index_inventory']));rows=[]
 for x in m['providers']:
  current=Path(x['raw']);donor=Path(x['approved_raw']);ck('fresh current payload pin '+x['depot'],sha(current)==x['raw_sha256']);ck('approved native donor pin '+x['depot'],sha(donor)==x['approved_raw_sha256']);ck('full actual current payload equals approved raw donor '+x['depot'],current.read_bytes()==donor.read_bytes()and x['raw_sha256']==x['approved_raw_sha256']);rows.append({k:x[k]for k in ['depot','provider','raw','raw_sha256','approved_raw','approved_raw_sha256']})
 ck('no current source collisions for these exact native donor keys',all(n==1 for n in collections.Counter(x['depot']for x in rows).values()));ck('no differing provider silently ignored',m['all_current_matches_approved_donors']and all(x['matches_approved_donor']for x in m['providers']));ck('no runtime or candidate writes',m['game_writes']==m['candidate_writes']==m['save_writes']==0)
 write(o/'tests.json',T);write(o/'evidence.json',{'status':'PASS_SIX_CURRENT_NATIVE_DONORS_BYTE_IDENTICAL_TO_APPROVED_CVI_INPUTS','checks':len(T),'capture':str(mp),'capture_sha256':sha(mp),'current_provider_count':len(rows),'queried_depots':6,'archive_indexes_consulted':134,'providers':rows,'semantic_reexport_required':False,'reason':'Each of the six approved donor resources has exactly one current archive provider, and every newly extracted complete payload is byte-identical to its approved raw donor. Existing native graph/scene/ancestor source analyses therefore apply without a new semantic comparison. This equality gate is separate from the current world-provider packed-layout repair evidence.','limits':['Only the six exact native donor depots queried; no full quest census repeated.','Does not certify engine call delivery, rendering, interruption/reload, private proposal integration or final archive/package validation.'],'runtime_changes':[]});print({'checks':len(T),'evidence':str(o/'evidence.json')})
if __name__=='__main__':
 import argparse
 a=argparse.ArgumentParser();a.add_argument('--output',required=True);run(Path(a.parse_args().output))
