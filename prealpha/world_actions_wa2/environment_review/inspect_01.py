"""Inspect freshly decoded exact environment references without changing candidates."""
from pathlib import Path
import json
H=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
inputs=read(H/'inputs_01.json');decoded=read(H/'decode_01/report_01.json')
extracted={Path(r['raw']).name:r for r in read(H/'extract_01/report_01.json')['hits']}
wanted={r for g in inputs['groups'] for r in g['context_refs']}
matches=[];near=[];failed=[]
for record in decoded['rows']:
    stem=Path(record['raw']).name
    if not record['parsed']:
        failed.append({'depot':extracted[stem]['depot'],'archive':Path(extracted[stem]['archive']).name,'error':record['error']})
        continue
    d=read(H/'decode_01'/(stem+'.placements.json'))
    definitions={r['node']:r for r in read(H/'decode_01'/(stem+'.nodes.json'))['nodes']}
    for p in d['placements']:
        ref=p['quest_ref']
        if ref in wanted or 'cs_goons_shooting' in ref:
            row={'depot':extracted[stem]['depot'],'archive':Path(extracted[stem]['archive']).name,
                 'raw':record['raw'],'placement':p,'node':definitions.get(p['node'])}
            if ref in wanted:matches.append(row)
            else:near.append(row)
result={'status':'ENVIRONMENT_REFERENCE_INSPECTION_NOT_APPROVAL','groups':[{'id':g['id'],'native_dependencies':g['native_dependencies'],
       'unmatched_native':[p for p in g['native_dependencies'] if not any(r['placement']['quest_ref']==p for r in matches)]} for g in inputs['groups']],
       'matches':matches,'related':near,'failed_sectors':failed}
out=H/'inspection_01.json';assert not out.exists();out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'groups':result['groups'],'matched_refs':len({r['placement']['quest_ref'] for r in matches}),'related_refs':sorted({r['placement']['quest_ref'] for r in near}),
                  'failed_sectors':[(r['archive'],r['depot'],r['error'].splitlines()[0]) for r in failed]},indent=2))
