"""Pin four native action environments and their previously decoded W3 locations."""
from pathlib import Path
from hashlib import sha256
import json
H=Path(__file__).resolve().parent;W=H.parents[2]
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
digest=lambda p:sha256(p.read_bytes()).hexdigest().upper()
cp=H.parent/'native_review/census_raw_01.json';mp=W/'prealpha/world_workspots_w2/manifest_03.json'
census=read(cp);manifest=read(mp);rows=[];pins=[cp,mp]
for group_id in (172,173,246,289):
    c=next(r for r in census['owners'] if r['id']==group_id)
    m=next(r for r in manifest['groups'] if r['id']==group_id)
    stem=Path(m['resource']).stem
    np=W/'diagnostics/world_npc_idle_20261026_02/families/decoded_02'/stem/'nodes.json'
    d=read(np);pins.append(np)
    points=[p['position'] for p in d['placements']]
    center=[sum(p[i] for p in points)/len(points) for i in range(3)]
    refs=sorted({r['value'] for p in c['phases'] for r in p['references'] if r['type']=='NodeRef' and 'cs_goons_shooting_env' in r['value']})
    assert refs
    prefixes={p.rsplit('/',1)[0] for p in refs if p.startswith('$/03_night_city/')}
    assert len(prefixes)==1
    context=set(refs)
    for prefix in prefixes:
        context.update(prefix+'/'+suffix for suffix in ['cs_goons_shooting_sec_system','cs_goons_shooting_sec_area'])
    rows.append({'id':group_id,'community_refs':m['community_refs'],'spawner_hashes':m['spawner_hashes'],
                 'center':center,'native_dependencies':refs,'context_refs':sorted(context),'location_source':str(np),
                 'native_source':c['source'],'native_source_sha256':digest(Path(c['source']))})
out=H/'inputs_01.json';assert not out.exists()
out.write_text(json.dumps({'status':'READ_ONLY_ENVIRONMENT_TARGETS','groups':rows,'pins':[{'path':str(p),'sha256':digest(p)} for p in pins]},indent=2)+'\n')
print(json.dumps([{'id':r['id'],'center':r['center'],'native_dependencies':len(r['native_dependencies'])} for r in rows]))
