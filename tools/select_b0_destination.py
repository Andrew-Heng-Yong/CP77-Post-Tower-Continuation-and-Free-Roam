"""Static ordinary arrival support census; never reads/writes game state."""
import bisect
import hashlib
import json
import math
from pathlib import Path

from collect_handoff_targets import BASE, ROOT, load, value
from review_handoff_support import intersect, local_point, vector, quat, rotate

OUT = ROOT / 'research/phase2b_p4'
OTHER = OUT / 'normal_candidates/ep1_1_nightcity/json/base/worlds/03_night_city/_compiled/default'
COLL = OUT / 'destination_collision/ep1_1_nightcity/json/base/worlds/03_night_city/_compiled/default'
PATHS = {
    'wat_lch_dataterm_05': [BASE / 'exterior_-25_19_0_0.streamingsector.json', BASE / 'exterior_-13_9_0_1.streamingsector.json'],
    'wat_lch_dataterm_04': [OTHER / 'exterior_-23_16_0_0.streamingsector.json', COLL / 'exterior_-12_8_0_1.streamingsector.json'],
    'wat_lch_dataterm_11': [OTHER / 'exterior_-26_15_0_0.streamingsector.json', COLL / 'exterior_-13_7_0_1.streamingsector.json'],
}

def main():
    evidence = json.loads((OUT/'target_evidence.json').read_text())
    block = load(BASE/'blocks/all.streamingblock.json')
    report = []
    for key, paths in PATHS.items():
        marker = next(m for m in evidence['candidate_markers'] if m['ref'].endswith('/#'+key))
        point = marker['position']
        target = {'key':key,'marker':marker,'sectors':[]}
        for path in paths:
            sector = load(path)
            index, descriptor = next((i,d) for i,d in enumerate(block['descriptors']) if value(d['data']['DepotPath']).endswith('\\'+path.name[:-5]))
            variants = {v['rangeIndex']:v for v in descriptor['variants']}
            instances = {}
            terminals = []
            meshes = []
            for di,d in enumerate(sector['nodeData']['Data']):
                ri = bisect.bisect_right(sector['variantIndices'],di)-1
                inst = {'node_data':di,'range':ri,'variant':variants.get(ri)}
                instances.setdefault(d['NodeIndex'],[]).append(inst)
                n = sector['nodes'][d['NodeIndex']]['Data']
                if key in json.dumps(n):
                    terminals.append({'node':d['NodeIndex'],'instance':inst,'data':d,'definition':n})
                if n.get('$type') == 'worldStaticMeshNode' and math.dist(vector(d['Position']),point)<15:
                    meshes.append({'node':d['NodeIndex'],'instance':inst,'data':d,'definition':n})
            hits = []
            nearby = []
            for ni,wr in enumerate(sector['nodes']):
                n = wr['Data']
                if n.get('$type') != 'worldCollisionNode':continue
                for ai,a in enumerate(n['compiledData']['Data']['Actors']):
                    origin = tuple(a['Position'][k]['Bits']/131072 for k in 'xyz')
                    dist = math.dist(point,origin)
                    for si,sh in enumerate(a['Shapes']):
                        row = {'node':ni,'actor':ai,'shape':si,'instances':instances.get(ni),
                            'debug_name':value(n.get('debugName')),'source_prefab':n.get('sourcePrefabHash'),
                            'actor_origin':origin,'actor_data':a,'shape_data':sh}
                        if dist<15:nearby.append(row)
                        if sh['ShapeType'] != 'Box':continue
                        top,bottom = (*point[:2],point[2]+1),(*point[:2],point[2]-4)
                        t = intersect(local_point(top,a,sh),local_point(bottom,a,sh),vector(sh['Size']))
                        if t is not None:
                            row['hit_z'] = top[2]-5*t
                            row['feet_minus_hit_z'] = point[2]-row['hit_z']
                            hits.append(row)
            target['sectors'].append({'path':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                'descriptor_index':index,'descriptor':descriptor,'box_hits':hits,'nearby_collision':nearby,'nearby_meshes':meshes,'terminals':terminals})
            print(key,path.name,'boxhits',[(r['node'],r['actor'],r['shape'],r['hit_z'],r['instances']) for r in hits], 'nearby',len(nearby), 'meshes',len(meshes),'terminals',len(terminals))
        report.append(target)
    (OUT/'destination_support_evidence.json').write_text(json.dumps(report,indent=2)+'\n')
    selected = next(r for r in report if r['key']=='wat_lch_dataterm_11')
    sector = selected['sectors'][1]
    hit = sector['box_hits'][0]
    actor, shape = hit['actor_data'], hit['shape_data']
    matched = [m for m in sector['nearby_meshes'] if math.dist(vector(m['data']['Position']),hit['actor_origin'])<0.00001
        and m['data']['Orientation']==actor['Orientation']]
    assert len(matched)==1
    mesh = matched[0]
    point=selected['marker']['position']
    corners=[]
    for x,z in ((-1.5,-1.5),(1.5,-1.5),(1.5,1.5),(-1.5,1.5)):
        p = rotate(quat(shape['Rotation']),(x,shape['Size']['Y'],z))
        p = tuple(v+o for v,o in zip(p,vector(shape['Position'])))
        p = tuple(v*s for v,s in zip(p,vector(actor['Scale'])))
        p = rotate(quat(actor['Orientation']),p)
        corners.append(tuple(v+o for v,o in zip(p,hit['actor_origin'])))
    clearance_samples=[]
    for i in range(8):
        x,y = point[0]+.4*math.cos(i*math.pi/4),point[1]+.4*math.sin(i*math.pi/4)
        top,bottom=(x,y,point[2]+1),(x,y,point[2]-4)
        t=intersect(local_point(top,actor,shape),local_point(bottom,actor,shape),vector(shape['Size']))
        clearance_samples.append({'xy':[x,y],'hit_z':None if t is None else top[2]-5*t})
    term=selected['sectors'][0]['terminals'][0]
    chunk=term['definition']['instanceData']['Data']['buffer']['Data']['Chunks'][0]
    compact = {'selected':selected['key'],'marker':selected['marker'],
        'candidate_status':[{ 'key':r['key'],'position':r['marker']['position'],
            'scanned_sectors':[s['path'] for s in r['sectors']],
            'box_support_count':sum(len(s['box_hits']) for s in r['sectors']),
            'status':'Selected pending independent review' if r is selected else 'Not selected: exact support unresolved; no claim of a hole'} for r in report],
        'terminal':{'sector':selected['sectors'][0]['path'],'descriptor_index':selected['sectors'][0]['descriptor_index'],
            'node':term['node'],'instance':term['instance'],'position':term['data']['Position'],
            'entity':term['definition']['entityTemplate'],'linkedFastTravelPoint':chunk['linkedFastTravelPoint']},
        'collision':{'sector':sector['path'],'descriptor_index':sector['descriptor_index'],'descriptor':sector['descriptor'],**hit},
        'matching_visual':{'node':mesh['node'],'instance':mesh['instance'],'position':mesh['data']['Position'],
            'orientation':mesh['data']['Orientation'],'scale':mesh['data']['Scale'],
            'mesh':mesh['definition']['mesh'],'source_prefab':mesh['definition']['sourcePrefabHash'],
            'owner':mesh['data']['UkHash1'],'position_match_distance':math.dist(vector(mesh['data']['Position']),hit['actor_origin'])},
        'derived_geometry':{'method':'Unit quaternion actor * shape rotation; inverse local vertical-segment/Box half-extent intersection. FixedPoint Bits / 131072.',
            'center_hit_local':local_point((*point[:2],hit['hit_z']),actor,shape),
            'upward_normal':rotate(quat(actor['Orientation']),rotate(quat(shape['Rotation']),(0,1,0))),
            'top_face_world_corners':corners,'radius_0_4m_support_samples':clearance_samples},
        'limits':['Authored marker is 0.421 m above this sidewalk collision; retain native marker transform rather than inventing a corrected height.',
            'Box support is demonstrated, not an exhaustive highest-surface or live residency/navmesh/player-capsule-clearance guarantee.',
            'Static evidence does not prove fast-travel device interaction or registration currently works.']}
    (OUT/'destination_selection_evidence.json').write_text(json.dumps(compact,indent=2)+'\n')

if __name__ == '__main__':main()
