"""Extract four already pinned native action objects; never opens a save."""
from pathlib import Path
import hashlib, json
HERE=Path(__file__).resolve().parent
WORKSPACE=HERE.parents[3]
out=HERE/'action_payloads_01.json'
assert not out.exists()
review=WORKSPACE/'prealpha/quest_restoration_qr15/runtime_probe_01/proposal_review_01/review.json'
prior=json.loads(review.read_text())
source=Path(prior['source_pins'][0]['json'])
data=source.read_bytes();sha=hashlib.sha256(data).hexdigest().upper()
assert sha==prior['source_pins'][0]['json_sha256']=='EE0E5F03FAA59148CB46C048E761F4D5B58263A46C2ED7F2A6ADD6B6EECA09B3'
value=json.loads(data);stack=[value];rows=[]
while stack:
    item=stack.pop()
    if isinstance(item,dict):
        if item.get('$type')=='questSpawnManagerNodeDefinition' and item.get('id') in (101,142,143,86):
            assert len(item['actions'])==1
            action=item['actions'][0]['type']['Data']
            rows.append({'id':item['id'],'definition_type':item['$type'],'action_payload':action})
        stack.extend(item.values())
    elif isinstance(item,list):stack.extend(item)
assert {r['id'] for r in rows}=={101,142,143,86} and len(rows)==4
rows.sort(key=lambda r:r['id'])
result={'source':{'path':str(source),'sha256':sha},'prior_review':{'path':str(review),'sha256':hashlib.sha256(review.read_bytes()).hexdigest().upper()},
    'four_source_objects':rows,'normalization':'Only retained exact action Data object from each existing Handle; no graph or action change',
    'game_api_calls':0,'runtime_changes':0,'save_reads':0}
out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
