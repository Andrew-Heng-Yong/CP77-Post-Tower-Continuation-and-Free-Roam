"""Reproducible bounded JV1 source applicability, no live rendering claim."""
from pathlib import Path
import sys,argparse
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H));import source_inputs as I
def run(out):
 assert not out.exists();M=I.read(H/'inspection_01/models.json');rel='r6/scripts/PTFR_Consolidated/PTFR_JohnnyVoiceJV1.reds';p=I.C/'package'/rel;s=p.read_text();h=next(x['sha256']for x in I.E['package_files']if x['path']==rel);hits=[]
 for d,m in M.items():
  if any(q in d for q in I.Q)and d.endswith('.scene')and any(x.get('$type')=='TweakDBID'and x.get('$value')=='Character.Silverhand'for x in I.walk(m['metadata'])):hits.append({'depot':d,'actor_record':'Character.Silverhand','metadata_sha256':m['metadata_sha256']})
 tests=[{'name':'current package JV1 pin','status':'PASS'if I.sha(p)==h else'FAIL','evidence':{'path':str(p),'sha256':h}},{'name':'five exact native actor-record bindings','status':'PASS'if len(hits)==5 else'FAIL','evidence':hits},{'name':'record-specific visual mechanism and no fact writes','status':'PASS'if 'actor.GetRecordID() != t"Character.Silverhand"'in s and'visual.TemporaryHide(true)'in s and'SetFact('not in s and'SetFactStr('not in s else'FAIL','evidence':'Genuine Tower guard, voice/timing actor kept, independent props not covered.'}]
 assert all(x['status']=='PASS'for x in tests);I.write(out,{'status':'SOURCE_APPLICABLE_VISUAL_ONLY_POLICY_LIVE_UNPROVEN','tests':tests,'checks':3,'source':str(p),'source_sha256':h,'actors':hits,'limits':['Source predicate applies to five pinned Character.Silverhand declarations; live visual hiding/streaming/independent props unproved.','Informer Johnny text alone is not proof of a corresponding active actor.'],'code_sha256':I.sha(__file__),'runtime_changes':[]});print({'checks':3,'actor_declarations':len(hits)})
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);run(Path(ap.parse_args().output).resolve())
