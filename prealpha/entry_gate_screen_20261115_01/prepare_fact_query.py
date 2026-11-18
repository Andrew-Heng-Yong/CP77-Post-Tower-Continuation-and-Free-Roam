"""Select source-named facts and quest roots for a read-only paired-save projection."""
import json
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
sys.path.insert(0,str(ROOT/'prealpha/phone_support_ph1'))
from model import model,walk

def main():
    output=HERE/'fact_query.json'
    if output.exists():
        raise RuntimeError('Fresh output required')
    binding=json.loads((HERE/'trace_02/binding.json').read_bytes())
    names=set()
    for resource in binding['resources']:
        for node in walk(model(resource['json'])):
            if isinstance(node.get('factName'),str):
                names.add(node['factName'])
    for row in json.loads((HERE/'sources_01/inventory.json').read_bytes())['entries']:
        for suffix in ('Ready','Permit','Issued','Entered','Finished','Fault'):
            names.add(row['tag']+'_'+suffix)
    catalogue=json.loads((ROOT/'prealpha/installed_qualification_20261115_01/run_01/catalogue.json').read_bytes())
    ids={'sts_ep1_07','sts_ep1_12','q305_postcontent','mws_se5_07'}
    roots=[{'id':r['id'],'title':r['title'],'path':j['path']} for r in catalogue['entries'] if r['id'] in ids
           for j in r['journals'] if j['class']=='gameJournalQuest' and j['path'].endswith('/'+r['id'])]
    assert {r['id'] for r in roots}==ids
    output.write_text(json.dumps({'facts':sorted(names),'journals':roots},indent=2)+'\n',encoding='utf-8')
    print(len(names),'source-named facts;',json.dumps(roots))

if __name__=='__main__':
    main()
