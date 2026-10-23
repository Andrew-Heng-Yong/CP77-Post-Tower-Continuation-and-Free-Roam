"""Narrow exact two-archive Arroyo variant proof; no blanket normalization."""
import argparse,copy,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools'))
from catalog_gig_rollout_r2 import read,sha
from test_rite_g2 import SafeResource
from audit_activity_batches_b1 import flatten
DEPOT=r'base\open_world\street_stories\santo_domingo\arroyo\sts_std_arroyo.questphase'
HASHES={'basegame_4_gamedata.archive':'F5C98432131AE1F0263BB82066096BC82DFDCFF98607871BE7055D854C185701','ep1_2_gamedata.archive':'9FF45BF261661EF607A9392CF1B04D155388C0ABD8C05BEBE4FB62199D0A7368'}

def rel(p):return Path(p).resolve().relative_to(ROOT).as_posix()
def fingerprint(obj):return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':')).encode()).hexdigest().upper()
def graphdoc(doc):return {g['path']:g for g in flatten(SafeResource(doc),doc['Data']['RootChunk'])}

def verify(output):
    assert not output.exists(),'Use a successor output path'
    pins={};checks=0
    def pin(p):p=Path(p);pins[rel(p)]=sha(p)
    def check(ok,label):
        nonlocal checks
        assert ok,label;checks+=1
    rp=ROOT/'research/gigs_u10/native/official_variants_01/report.json';report=read(rp);pin(rp)
    rows=[r for r in report['rows'] if r['depot']==DEPOT];check(len(rows)==2,'exactly known two variants')
    rows.sort(key=lambda r:Path(r['archive']).name)
    docs=[]
    for row in rows:
        p=Path(row['archive']);check(p.name in HASHES and row['actual']==HASHES[p.name],'fixed archive/hash identity')
        check(sha(row['raw'])==row['actual'],'raw byte witness');check(Path(row['raw']).is_relative_to(ROOT),'local witness')
        pin(row['raw']);pin(row['json']);docs.append(read(row['json']))
    a,b=docs
    check(a['Data']['RootChunk']==b['Data']['RootChunk'],'entire district root/context equality')
    check(len(a['Data']['EmbeddedFiles'])==len(b['Data']['EmbeddedFiles'])==15,'exact embedded resource set')
    normalized=copy.deepcopy(b['Data'])
    differences=[]
    for i in (5,10):
        check(a['Data']['EmbeddedFiles'][i]['Content']['cookingPlatform']=='PLATFORM_None','original cook metadata')
        check(b['Data']['EmbeddedFiles'][i]['Content']['cookingPlatform']=='PLATFORM_PC','EP1 cook metadata')
        check(a['Data']['EmbeddedFiles'][i]['FileName']==b['Data']['EmbeddedFiles'][i]['FileName'],'same embedded reference')
        normalized['EmbeddedFiles'][i]['Content']['cookingPlatform']='PLATFORM_None'
        differences.append(dict(path=f'Data.EmbeddedFiles[{i}].Content.cookingPlatform',base='PLATFORM_None',ep1='PLATFORM_PC',depot=a['Data']['EmbeddedFiles'][i]['FileName']['$value']))
    check(normalized==a['Data'],'no other Data payload differences of any kind')
    planpath=ROOT/'research/gigs_u10/native/build_plan_01.json';pin(planpath);plan=read(planpath);job=next(j for j in plan['jobs'] if j['id']=='sts_std_arr_03')
    check(job['parent']['binding']['parent']==DEPOT and job['parent']['binding']['graph']=='root','Race parent identity')
    source=ROOT/job['parent']['raw'];pin(source);sourcejson=ROOT/job['parent']['binding']['binding']['source'];pin(sourcejson)
    check(sha(source)==HASHES['basegame_4_gamedata.archive'],'selected source is exact official base variant')
    check(read(sourcejson)['Data']==a['Data'],'selected source complete data equals fresh official extraction')
    gs=[graphdoc(d) for d in docs];check(gs[0]==gs[1],'all root and nested graph node/edge equality')
    ids={n['id'] for n in job['parent']['ancestors']}|{job['parent']['child']['id']};check(ids=={0,2,8,78},'exact Race parent slice bound')
    payloads=[]
    for doc,g in zip(docs,gs):
        root=g['root'];selected=[n for n in root['nodes'] if n['id'] in ids]
        check(selected==sorted(job['parent']['ancestors']+[job['parent']['child']],key=lambda n:n['id']),'source parent payloads')
        edges=[e for e in root['edges'] if e[0] in ids and e[2] in ids];check(edges==job['parent']['edges'],'source parent edges')
        check(g['root/2']==job['parent']['nested'][0],'nested native gate exact')
        # No district-resource prefab context is inherited by the standalone
        # wrapper. Its copied phase node and every actual resource retain theirs.
        check(doc['Data']['RootChunk']['phasePrefabs']==[],'no omitted district root prefab context')
        payloads.append(dict(parent_nodes=selected,parent_edges=edges,nested=g['root/2'],district_resource_prefabs=doc['Data']['RootChunk']['phasePrefabs']))
    check(payloads[0]==payloads[1],'used parent payloads identical')
    collateral=[]
    for kind,items in [('map',plan['maps']),('credit',plan['credits'])]:
        for item in items:
            if item['id']!='sts_std_arr_03':continue
            p=ROOT/item['raw'];pin(p);jp=ROOT/(item['raw'].replace('/raw/','/json/')+'.json');pin(jp)
            check(item['raw']!=job['parent']['raw'],'map/credit comes from a separate byte-exact official resource')
            original=graphdoc(read(jp))[item['graph']];nodes={n['id']:n for n in original['nodes']}
            for n in item['nodes']:check(nodes[n['id']]==n,f'{kind} original payload')
            check(any(r['source']==item['raw'] and r['equal'] for r in report['rows']),f'{kind} official exact witness')
            check(not any(r['source']==item['raw'] and not r['equal'] for r in report['rows']),f'{kind} no variant mismatch')
            collateral.append(dict(kind=kind,raw=item['raw'],sha256=sha(p),graph=item['graph'],ids=item['ids']))
    for p in [Path(__file__),ROOT/'tools/catalog_gig_rollout_r2.py',ROOT/'tools/test_rite_g2.py',ROOT/'tools/test_gig_pilot_r1.py',ROOT/'tools/audit_activity_batches_b1.py']:pin(p)
    variants=[dict(archive=row['archive'],raw=rel(row['raw']),json=rel(row['json']),sha256=sha(row['raw']),json_sha256=sha(row['json']),used_payload_sha256=fingerprint(payloads[i]),used_checks=checks,payload_checks=checks) for i,row in enumerate(rows)]
    result=dict(status='PASS_USED_DISTRICT_PAYLOADS_ALL_VARIANTS',depot=DEPOT,source=rel(source),source_sha256=sha(source),variants=variants,source_pins=pins,verifier=rel(__file__),verifier_sha256=sha(__file__),scope={'job':'sts_std_arr_03','parent_graph':'root','node_ids':sorted(ids),'nested_graphs':['root/2'],'native_main_node':8,'map_credit_separate_exact_sources':collateral},known_non_graph_metadata_differences=differences,
                checks=checks,limits=['No whole-file byte equivalence claimed; both official variants remain byte-pinned independently.','Only exact known cookingPlatform metadata differences at embedded indexes5/10 are accepted. Unknown variants or any other source payload change fail.','This source proof does not claim live gameplay.'])
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(status=result['status'],checks=checks,output=rel(output))))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=ROOT/'research/gigs_u10/native/district_variants_01.json');args=p.parse_args();verify(args.output.resolve())
