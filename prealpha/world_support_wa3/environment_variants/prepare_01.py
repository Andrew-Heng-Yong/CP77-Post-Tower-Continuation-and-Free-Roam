"""Review exact native environment variants omitted from four existing owners."""
from pathlib import Path
import json,hashlib
H=Path(__file__).resolve().parent;W=H.parents[2]
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
cp=W/'prealpha/world_actions_wa2/native_review/action_contracts_02.json'
mp=W/'prealpha/world_workspots_w2/manifest_03.json'
c=read(cp);m=read(mp);rows=[];pins=[cp,mp]
for gid in (200,202,210,461):
    r=next(x for x in c['review'] if x['group']==gid)
    g=next(x for x in m['groups'] if x['id']==gid)
    matches=list((W/'diagnostics/world_npc_idle_20261026_02/families').glob('decoded_*/'+Path(g['resource']).stem+'/nodes.json'))
    assert len(matches)==1,(gid,matches)
    np=matches[0]
    d=read(np);pins.append(np)
    points=[v['position'] for v in d['placements']]
    center=[sum(v[i] for v in points)/len(points) for i in range(3)]
    rows.append({'id':gid,'center':center,'operations':r['operations'],'native_binary':g['native_binary'],'native_binary_sha256':g['native_binary_sha256'],'node_path':g['node_path'],'community_refs':g['community_refs'],'spawner_hashes':g['spawner_hashes']})
out=H/'inputs_01.json';assert not out.exists()
out.write_text(json.dumps({'status':'READ_ONLY_ENVIRONMENT_VARIANT_TARGETS','groups':rows,'pins':[{'path':str(p),'sha256':digest(p)} for p in pins]},indent=2)+'\n',newline='\n')
for name in ['extract_01.ps1','decode_01.ps1']:
    text=(W/'prealpha/world_actions_wa2/environment_review'/name).read_text()
    if name=='decode_01.ps1':
        text=text.replace("if($type -match 'Entity|Device|Security|Community|Trigger|Area'){","if($true){")
        text=text.replace("$out=Join-Path $PSScriptRoot 'decode_01'", "$out=Join-Path $PSScriptRoot 'decode_01'")
    (H/name).write_text(text,encoding='utf-8',newline='\n')
print(json.dumps([{'id':r['id'],'center':r['center']} for r in rows]))
