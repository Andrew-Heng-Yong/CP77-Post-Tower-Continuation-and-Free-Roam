"""Repair dense actor indices in nine current H1 scenes; preserve all other data."""
from pathlib import Path
import copy,hashlib,json
H=Path(__file__).resolve().parent;W=H.parent.parent;C=H/'candidate_01';A=C/'scene_audit_01'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def walk(x,path=()):
 if isinstance(x,dict):
  yield path,x
  for k,v in x.items():yield from walk(v,path+(k,))
 elif isinstance(x,list):
  for i,v in enumerate(x):yield from walk(v,path+(i,))
def repair(obj):
 result=copy.deepcopy(obj);root=result['Data']['RootChunk'];defs=root['actors']+root['playerActors'];ids=[x['actorId']['id'] for x in defs]
 assert len(set(ids))==len(ids) and ids!=list(range(len(ids)))
 mapping=dict(zip(ids,range(len(ids))));removed=[];operations=[]
 symbols=root['debugSymbols']['performersDebugSymbols'];kept=[]
 for i,s in enumerate(symbols):
  p=s['performerId']['id']
  if p&255==1 and p>>8 not in mapping:removed.append({'index':i,'symbol':s})
  else:kept.append(s)
 root['debugSymbols']['performersDebugSymbols']=kept
 for path,v in walk(root):
  typ=v.get('$type');old=v.get('id');new=old
  if typ=='scnActorId' and old!=0xffffffff:
   assert old in mapping,('undefined actor',path,old);new=mapping[old]
  elif typ=='scnPerformerId' and old&255==1:
   assert old>>8 in mapping,('undefined performer',path,old);new=(mapping[old>>8]<<8)|1
  if old!=new:v['id']=new;operations.append({'path':list(path)+['id'],'before':old,'after':new})
 assert [x['actorId']['id'] for x in root['actors']+root['playerActors']]==list(range(len(ids)))
 return result,{'mapping':mapping,'removed_debug_symbols':removed,'id_changes':operations}
def main():
 out=C/'prepared_01';out.mkdir(exist_ok=False);audit=read(A/'audit.json');rows=[]
 selected=[r for r in audit['non_dense'] if r['archive']=='00000000_TowerContinued_Housing_H1.archive'];assert len(selected)==9
 for row in selected:
  raw=Path(row['raw']);assert sha(raw)==row['sha256'];src=Path(str(raw)+'.json');original=read(src);fixed,changes=repair(original)
  p=out/(raw.name+'.json');p.write_text(json.dumps(fixed,indent=2)+'\n')
  rows.append(dict(depot=row['depot'],raw=str(raw),raw_sha256=sha(raw),source=str(src),source_sha256=sha(src),prepared=str(p),prepared_sha256=sha(p),**changes))
 result={'status':'PREPARED_DENSE_ACTOR_REPAIR','resources':rows,'audit_sha256':sha(A/'audit.json'),'builder_sha256':sha(Path(__file__)),'untouched_non_dense_legacy':[r['depot'] for r in audit['non_dense'] if r not in selected]}
 (C/'prepared_01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'scenes':len(rows),'id_changes':sum(len(r['id_changes']) for r in rows),'removed_stale_debug_symbols':sum(len(r['removed_debug_symbols']) for r in rows)}))
if __name__=='__main__':main()
