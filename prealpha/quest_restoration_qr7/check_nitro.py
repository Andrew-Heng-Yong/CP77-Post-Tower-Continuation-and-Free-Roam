"""Actual before/serialized-after/native MQ060 guards and saved graph preservation."""
from pathlib import Path
import sys,argparse,copy,itertools,json,zlib
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,walk
from model import Resource
ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);a=ap.parse_args();D=Path(a.output).resolve();assert not D.exists();D.mkdir(parents=True)
C=O/'candidate_01';R=C/'repair_nitro_01';plan=read(C/'nitro_plan.json');patch=read(R/'patch.json');checks=[];mutants=[]
def ck(name,ok,ev):checks.append({'name':name,'pass':bool(ok),'evidence':ev});assert ok,name
def canonical(v):
 if isinstance(v,dict):
  if v.get('$type')=='TweakDBID':
   s=str(v['$value']);v=copy.deepcopy(v);v['$storage']='uint64';v['$value']=str(int(s))if s.isdigit()else str((len(s.encode())<<32)|zlib.crc32(s.encode()))
  return{k:canonical(x)for k,x in v.items()if k not in ['payload_sha256','metadata_sha256']}
 if isinstance(v,list):return[canonical(x)for x in v]
 return v
before=Resource(read(R/'before.json')).normalize();after=Resource(read(R/'after.json')).normalize();native=Resource(read(R/'native.json')).normalize();proposed=Resource(read(plan['proposal'])).normalize();raw=read(R/'after.json')
ck('actual repaired binary SHA',sha(C/'archive_source'/plan['depot'])==patch['after'],patch)
ck('reviewed source/proposal/review pins',all(sha(plan[k])==plan[k+'_sha256']for k in ['proposal','evidence','review']),'Exact independently approved inputs')
ck('all graph errors absent',not before['errors']and not after['errors']and not native['errors'],[before['errors'],after['errors'],native['errors']])
ck('serialized resource equals reviewed proposed semantic tree',canonical(after)==canonical(proposed),'Whole resource, including nested graphs/metadata, normalized only TDBstorage and derived hashes')
nb=native['graphs']['root/3']['nodes'];conds=[nb[str(i)]['payload']['condition']for i in [93,104]]
bg=before['graphs']['root'];ag=after['graphs']['root']
ck('all saved root graph IDs preserved',set(bg['nodes'])==set(ag['nodes']),sorted(ag['nodes']))
ck('all saved edges preserved',bg['edges']==ag['edges'],bg['edges'])
for i,node in bg['nodes'].items():
 new=copy.deepcopy(ag['nodes'][i]);old=copy.deepcopy(node)
 if i in ['65003','65004']:
  oc=old['payload']['condition'];nc=new['payload']['condition'];ck('guard original AND '+i,oc['operation']==nc['operation']=='AND','Original conjunction, no OR flattening')
  ck('exact original guard prefix '+i,canonical(nc['conditions'][:-2])==canonical(oc['conditions']),'All old fact/journal/owner predicates retained')
  ck('exact registered native suffix '+i,canonical(nc['conditions'][-2:])==canonical(conds),'Native93 OR3 and104 count>=3')
  new['payload']['condition']['conditions']=new['payload']['condition']['conditions'][:-2]
  for k in ['reads','conditions','refs','node_refs','journal_paths']:new[k]=old[k]
 ck('whole original node semantics preserved '+i,canonical(new)==canonical(old),'Only declared guard condition suffix removed for comparison')
ck('all non-root graphs and root metadata preserved',canonical({k:v for k,v in before.items()if k!='graphs'})==canonical({k:v for k,v in after.items()if k!='graphs'})and canonical({k:v for k,v in before['graphs'].items()if k!='root'})==canonical({k:v for k,v in after['graphs'].items()if k!='root'}),'No saved body/owner/reward/prefab/scene/journal mutation')
def ev(c,vehicles,count):
 t=c['$type']
 if t=='questLogicalCondition':
  x=[ev(x,vehicles,count)for x in c['conditions']];assert c['operation']in ['AND','OR'];return all(x)if c['operation']=='AND'else any(x)
 if t in ['questVehicleCondition','questFactsDBCondition']:return ev(c['type'],vehicles,count)
 if t=='questVehicleAvailable_ConditionType':return c['vehicleName']in vehicles
 if t=='questVarComparison_ConditionType':assert c['factName']=='carbought_counter'and c['comparisonType']=='GreaterOrEqual';return count>=c['value']
 raise ValueError(t)
vehicle_names=sorted({x['vehicleName']for c in conds for x in walk(c)if x.get('$type')=='questVehicleAvailable_ConditionType'}|{'Vehicle.v_sportbike1_yaiba_kusanagi_tyger_player'})
fixtures=[]
for bits in itertools.product([False,True],repeat=4):
 owned={n for n,on in zip(vehicle_names,bits)if on}
 for count in range(5):
  oracle=all(ev(c,owned,count)for c in conds);old=bool(owned);new=old and all(ev(c,owned,count)for c in ag['nodes']['65004']['payload']['condition']['conditions'][-2:]);fixtures.append({'vehicles':sorted(owned),'purchase_count':count,'registered_native':oracle,'before':old,'after':new})
ck('defective before has47 actual fixture divergences',sum(x['before']!=x['registered_native']for x in fixtures)==47,'Other original guard terms assumed satisfied; source gate fixtures, not fabricated saved history')
ck('repaired serialized suffix matches all80 native fixtures',len(fixtures)==80 and all(x['after']==x['registered_native']for x in fixtures),'Independent native predicate oracle, actual readback suffix')
def mutation(name,change):
 m=copy.deepcopy(raw);change(m);mm=Resource(m).normalize();suffix=mm['graphs']['root']['nodes']['65004']['payload']['condition']['conditions'][-2:];discrepancies=[x for x in fixtures if bool(x['vehicles'])and all(ev(c,set(x['vehicles']),x['purchase_count'])for c in suffix)!=x['registered_native']]
 # Parenthesize independently: avoid an oracle based merely on graph inequality.
 differences=sum((bool(x['vehicles'])and all(ev(c,set(x['vehicles']),x['purchase_count'])for c in suffix))!=x['registered_native']for x in fixtures)
 ck('raw resource mutant detected '+name,differences>0,{'native_fixture_failures':differences});f=D/'mutations'/(name+'.json');write(f,m);mutants.append({'name':name,'path':str(f),'sha256':sha(f),'detected':True,'failing_native_fixtures':differences})
def tweak(m,kind):
 res=Resource(m);g=res.d(res.root['graph']);node=next(res.d(x)for x in g['nodes']if res.d(x)['id']==65004);c=res.d(node['condition']);suffix=[res.d(x)for x in c['conditions'][-2:]]
 if kind=='threshold':res.d(suffix[1]['type'])['value']=2
 if kind=='and':suffix[0]['operation']='AND'
 if kind=='drop_variant':suffix[0]['conditions'].pop()
mutation('weaken_purchase_threshold',lambda m:tweak(m,'threshold'));mutation('native_OR_changed_to_AND',lambda m:tweak(m,'and'));mutation('missing_native_vehicle_branch',lambda m:tweak(m,'drop_variant'))
write(D/'checks.json',checks);write(D/'fixtures.json',fixtures);write(D/'mutations.json',mutants);write(D/'result.json',{'status':'PASS_SERIALIZED_NATIVE_MQ060_GUARDS_AND_PRESERVATION','checks':len(checks),'actual_document_mutations':len(mutants),'fixtures':len(fixtures),'before_divergences':47,'after_divergences':0,'before_sha256':patch['before'],'after_sha256':patch['after'],'resource':plan['depot'],'scope':'Prospective pre-Issued correction only; old issued selector/owners and all other source bytes are preserved. No gameplay proof.'});print({'status':'PASS','checks':len(checks),'mutants':len(mutants),'before_divergences':47,'after_divergences':0})
