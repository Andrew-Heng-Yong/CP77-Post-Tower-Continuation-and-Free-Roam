"""QR4 focused before/after native-continuation and preservation regression.

Read only binaries/JSON. Writes a fresh evidence directory. The separate worker
review uses independent binary exports and a second raw socket traversal.
"""
from pathlib import Path
import argparse, collections, copy, sys
W=Path(__file__).resolve().parents[2]; O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,walk
from model import Resource

def run(out):
 assert not out.exists(),'Use a fresh output directory'
 c=O/'candidate_01'; cap=c/'repair_mq007'; patch=read(cap/'patch.json')
 epoch=read(O/'source_epoch_00.json'); proposal=read(O/'groups/G08/regina_proposal_01/proposal.json')
 review=O/'groups/G10/reviews/MQ007_serialized/verification_01/review.json'
 checks=[]; mutations=[]; controls=[]
 def check(name,ok,evidence):
  checks.append({'name':name,'status':'PASS' if ok else 'FAIL','evidence':evidence})
  assert ok,name
 native=Resource(read(cap/'native_bugfix.json')).normalize()
 tree={p[len('root/14'):]:g for p,g in native['graphs'].items() if p=='root/14' or p.startswith('root/14/')}
 def parity(m):return all(m['graphs'].get('root/1202'+p)==g for p,g in tree.items())
 edges=[('1101','Out','1200','In'),('1200','True','1201','In'),('1201','Out','1202','In1'),('1202','Out1','1203','In')]
 def route(m):
  g=m['graphs']['root']; return parity(m) and all(e in map(tuple,g['edges']) for e in edges)
 r=read(review)
 check('independent actual serialized review approved',r['status'].startswith('APPROVED_SERIALIZED'),{'path':str(review),'sha256':sha(review),'checks':r['checks']})
 for row in patch['resources']:
  tag=row['prefix']; before=Resource(read(cap/(tag+'_before.json'))).normalize(); doc=read(cap/(tag+'_after.json')); after=Resource(doc).normalize()
  prop=next(x for x in proposal['resources'] if x['resource']==row['depot'])
  check(tag+' exact predecessor and successor binaries',sha(Path(epoch['candidate'])/'archive_source'/row['depot'])==row['before']==epoch['source_resources'][row['depot']] and sha(c/'archive_source'/row['depot'])==row['after'],row)
  check(tag+' missing original native consumer reproduces',not route(before),{'expected':'FAIL_MISSING_NATIVE_CONTINUATION','baseline':row['before']})
  check(tag+' repaired route exact native14 subtree',route(after),{'native_sha256':patch['native_sha256'],'paths':list(tree)})
  controls.append({'resource':row['depot'],'before':'EXPECTED_FAIL_MISSING_CONSUMER','after':'PASS_EXACT_NATIVE_CONTINUATION'})
  bg=before['graphs']['root']; ag=after['graphs']['root']
  check(tag+' every old root identity payload socket preserved',all(ag['nodes'].get(i)==n for i,n in bg['nodes'].items()),list(bg['nodes']))
  check(tag+' every old nested graph preserved',all(after['graphs'].get(p)==g for p,g in before['graphs'].items() if p!='root'),list(before['graphs']))
  check(tag+' only four local nodes and four edges added',set(ag['nodes'])-set(bg['nodes'])=={'1200','1201','1202','1203'} and collections.Counter(map(tuple,ag['edges']))==collections.Counter(map(tuple,bg['edges']))+collections.Counter(edges),edges)
  check(tag+' event-only ingress and no root termination',[e for e in ag['edges'] if e[2]=='1200']==[['1101','Out','1200','In']] and not any(n['type']=='questOutputNodeDefinition' for n in ag['nodes'].values()),'No root input/on-attach/poll or retroactive enrollment added')
  reads=ag['nodes']['1200']['reads']; want=prop['enrollment_guard']['facts_equal']
  check(tag+' exact AND equal guard',ag['nodes']['1200']['type']=='questConditionNodeDefinition' and ag['nodes']['1200']['payload']['condition']['operation']=='AND' and {x['factName']:x['value'] for x in reads}==want and all(x['comparisonType']=='Equal' for x in reads),want)
  def accepts(f,event=True):return event and all(f.get(x['factName'],0)==x['value'] for x in reads)
  check(tag+' future event accepted and old receipt alone not polled',accepts(want) and not accepts(want,False),{'event_required':True})
  for key,value in want.items():check(tag+' changed guard rejected '+key,not accepts(want|{key:1-value}),{'fact':key,'expected':value})
  check(tag+' absent positive provenance rejected',all(not accepts({k:v for k,v in want.items() if k!=key}) for key,value in want.items() if value==1),'Fixture models absent scalar facts as0; absent expected0 is NOT rejected or treated as history proof')
  check(tag+' no container lease and exact recursive helper',not ag['nodes']['1202']['prefabs'] and after['graphs']['root/1202']['nodes']['3']['prefabs']==['#mq007_pr_gun_re_acquiring'] and not any('#mq007_pr_gun_return' in n['prefabs'] for g in after['graphs'].values() for n in g['nodes'].values()),'Helper lease differs from persistent world container')
  # Actual decoded-resource mutations, renormalized before testing.
  for name,ids,edit in [
   ('missing helper',[1202,3],lambda n,r:n.__setitem__('phaseInstancePrefabs',[])),
   ('wrong native timer',[1202,4],lambda n,r:next(x for x in walk(r.d(n['condition'])) if x.get('$type')=='questGameTimeDelay_ConditionType').__setitem__('days',1)),
  ]:
   bad=copy.deepcopy(doc); rr=Resource(bad); g=rr.d(rr.root['graph'])
   for ident in ids:
    n=next(rr.d(h) for h in g['nodes'] if rr.d(h)['id']==ident)
    if 'phaseGraph'in n:g=rr.d(n['phaseGraph'])
   edit(n,rr); detected=not route(Resource(bad).normalize());mutations.append({'resource':tag,'fault':name,'detected':detected});check(tag+' mutation '+name,detected,mutations[-1])
  bad=copy.deepcopy(after);bad['graphs']['root']['edges'].remove(['1200','True','1201','In']);detected=not route(bad);mutations.append({'resource':tag,'fault':'remove enrollment-to-claim edge','detected':detected});check(tag+' mutation missing claim connection',detected,mutations[-1])
 expected=dict(epoch['source_resources']); expected.update({r['depot']:r['after'] for r in patch['resources']})
 actual={str(p.relative_to(c/'archive_source')):sha(p) for p in (c/'archive_source').rglob('*') if p.is_file()}
 check('entire successor source equals explicit two-resource allowlist',actual==expected,{'count':len(actual),'changed':[d for d in actual if actual[d]!=epoch['source_resources'].get(d)]})
 prior=read(W/'prealpha/quest_restoration_qr3/approved_changes_02.json')['resources']
 check('QR3 MQ030/MQ037 fixes remain exact',all(actual[r['depot']]==r['after'] for r in prior),prior)
 if (c/'package_manifest.json').exists():
  manifest=read(c/'package_manifest.json');rebuilt=read(c/'rebuild_01.json')
  check('final package50otherfiles unchanged and archive matches readback',all(sha(c/'package'/p['path'])==p['sha256'] for p in epoch['package_files'] if not p['path'].replace('\\','/').endswith('/zzzz_PTFR_Combined.archive')) and sha(c/'package/archive/pc/mod/zzzz_PTFR_Combined.archive')==manifest['archive_sha256']==rebuilt['archive_sha256'],{'paths':len(epoch['package_files']),'manifest_sha256':sha(c/'package_manifest.json')})
 else:
  check('all51 precursor package files unchanged before rebuild',all(sha(c/'package'/p['path'])==p['sha256'] for p in epoch['package_files']),{'paths':len(epoch['package_files'])})
 inputs=[Path(__file__),O/'source_epoch_00.json',O/'groups/G08/regina_proposal_01/proposal.json',cap/'patch.json',cap/'native_bugfix.json',review]+[cap/(t+s+'.json') for t in ['fresh','resume'] for s in ['_before','_after']]
 report={'status':'PASS_FOCUSED_STATIC_REPAIR_AND_PRESERVATION','checks':len(checks),'tests':checks,'mutations':mutations,'before_after':controls,'input_pins':{str(x):sha(x) for x in inputs},'independent_review':{'path':str(review),'sha256':sha(review)},'limits':['Absent expected0 predicates are satisfied in the scalar fixture; receipt/provenance comes from required positive guards, not universal missing-fact rejection. Engine execution is not simulated.','Only future1101 signals before native done/reacquired enroll. Old already-entered/returned owners are deferred, not retroactively adopted.','Native11/51/95 admission seam and opaque sector loot remain unresolved. Actual scheduler, timers, reload and pickup require gameplay verification.'],'game_writes':0,'save_writes':0}
 write(out/'tests.json',report);return {k:report[k] for k in ['status','checks','mutations']}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);a=ap.parse_args();print(run(Path(a.output).resolve()))
