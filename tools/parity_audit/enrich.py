"""Versioned correction of discovery only; does not replace protected baseline."""
from common import *
def enrich(w,o):
 cat=read(o/'catalogues.json');old=cat['held_ids']
 for r in cat['quests']:r['held']=bool(re.search(r'\b(?:hold|held)\b',r.get('reason','')+' '+r.get('requirements',''),re.I)) and r['decision']!='INCLUDE'
 cat['held_ids']=[r['id'] for r in cat['quests'] if r['held']];write(o/'catalogues.json',cat)
 q=read(o/'queries.json');n=0
 for p in sorted((w/'prealpha').glob('*/prepared_*/prepared.json')):
  j=read(p);q['metadata_sources'].append({'path':str(p),'sha256':sha(p)})
  for a,b in j.get('mapping',{}).items():
   if a.startswith(('base\\','ep1\\')) and b.startswith('towercontinued\\'):
    q['mapping_candidates'].append({'native':a,'private':b,'evidence':str(p)});n+=1
  for r in j.get('jobs',[]):
   if r.get('native'):
    q['quest_seeds'][r['id']]=sorted(set(q['quest_seeds'].get(r['id'],[]))|{r['native']})
 write(o/'queries.json',q);write(o/'discovery_corrections.json',{'held_before':old,'held_after':cat['held_ids'],'reason':'Word boundaries distinguish hold from placeholder/withhold; additional prepared.json schemas contain source identity mappings, not semantic authorization','added_identity_candidates':n})
if __name__=='__main__':
 import sys
 enrich(Path.cwd(),Path(sys.argv[1]))
