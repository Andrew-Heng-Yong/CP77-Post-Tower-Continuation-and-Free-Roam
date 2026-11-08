"""Independent final binary/approved-proposal semantic identity gate."""
from pathlib import Path
import sys,copy
H=Path(__file__).resolve().parent;W=H.parents[2];sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
from model import Resource
def run(o):
 assert not o.exists();capture=H/'reviews/nitro_serialized_01/manifest.json';pin=read(capture);assert sha(Path(pin['source']))==pin['source_sha256'];assert sha(Path(pin['json']))==pin['json_sha256'];actual=Resource(read(Path(pin['json']))).normalize();c=W/'prealpha/quest_restoration_qr7/worker_c/nitro_authority_03';proposal=Resource(read(c/'private_proposed_resource.json')).normalize();pins=read(c/'source_pins.json');entry=next(p for p in pins if 'mq060_nitro.questphase'in p['depot']);base=Resource(read(Path(entry['json']))).normalize();native=next(p for p in pins if p['depot']==r'base\quest\bugfixing\quest_bugfixing.questphase');n=Resource(read(Path(native['json']))).normalize()['graphs']['root/3'];T=[]
 def ck(name,b):T.append({'name':name,'pass':bool(b)});assert b,name
 ck('fresh actual binary semantic tree equals independently approved proposal',actual==proposal);ck('actual raw decoder has no structural errors',not actual['errors']);ck('same saved graph scope',set(actual['graphs'])==set(base['graphs']))
 for gp,g in actual['graphs'].items():
  b=base['graphs'][gp];ck('saved edges and entries '+gp,g['edges']==b['edges']and g['entries']==b['entries']);ck('saved node identities '+gp,set(g['nodes'])==set(b['nodes']))
  for i,v in g['nodes'].items():
   if gp=='root'and i in ['65003','65004']:continue
   ck('unaffected payload/socket '+gp+'/'+i,v['payload']==b['nodes'][i]['payload']and v['sockets']==b['nodes'][i]['sockets'])
 for i in ['65003','65004']:
  cnd=actual['graphs']['root']['nodes'][i]['payload']['condition'];ck('actual binary exact native appended pair '+i,cnd['conditions'][-2:]==[n['nodes']['93']['payload']['condition'],n['nodes']['104']['payload']['condition']])
 ck('candidate baseline still pinned, only successor examined',sha(Path(entry['raw']))==entry['raw_sha256']);write(o/'review.json',{'status':'APPROVED_INDEPENDENT_ACTUAL_BINARY_READBACK_PARITY','checks':len(T),'capture':str(capture),'capture_sha256':sha(capture),'candidate_raw_sha256':pin['source_sha256'],'approved_proposal_sha256':sha(c/'private_proposed_resource.json'),'prior_independent_source_review':str(H/'reviews/nitro_01/review.json'),'tests':T,'limits':'A focused static/serialized gate. Does not certify game delivery, global candidate packaging, deployment or already-issued owner migration.'});print({'checks':len(T),'review':str(o/'review.json')})
if __name__=='__main__':
 import argparse
 a=argparse.ArgumentParser();a.add_argument('--output',required=True);run(Path(a.parse_args().output))
