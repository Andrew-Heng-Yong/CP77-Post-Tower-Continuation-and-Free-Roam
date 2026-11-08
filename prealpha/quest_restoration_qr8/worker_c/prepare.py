"""QR8 Worker C: five exact UNKNOWNs, pinned inputs and bounded new targets."""
from pathlib import Path
import json,hashlib,argparse,collections

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
Q7=ROOT/'prealpha/quest_restoration_qr7'
GAME=Path('C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077')
_memo={}
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    p=Path(p);st=p.stat();key=(str(p.resolve()),st.st_size,st.st_mtime_ns)
    if key not in _memo:
        with p.open('rb') as f:_memo[key]=hashlib.file_digest(f,'sha256').hexdigest().upper()
    return _memo[key]
def write(p,data):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists(),p
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main(out):
    assert not out.exists()
    ep=Q7/'source_epoch_04.json';assert sha(ep)=='8B0D8249908A9D96CF5564C9581ED466C061350B96A4BEE767D744B01DE28A1F'
    e=read(ep);c=Path(e['candidate']);complete=read(Q7/'completion.json')
    assert complete['status']=='QR7_COMPLETE_TARGETED_STATIC_WORK_WITH_PARTIAL_REPAIR_AND_UNKNOWN_LIMITS'
    rows=[x for x in read(Q7/'worker_c/final_scope_03/contract_updates.json') if x['status']=='UNKNOWN']
    assert collections.Counter(x['quest_id'] for x in rows)=={'mws_wat_08_trauma_drama':1,'sts_std_rcr_02':1,'q304_splinter_stash':3}
    ps=[]
    for d,h in e['source_resources'].items():
        if any(x in d for x in ['mws_wat_08','sts_std_rcr_02','voodoo_boot']):
            p=c/'archive_source'/d.replace('\\','/');assert sha(p)==h;ps.append({'depot':d,'path':str(p),'sha256':h})
    native=[]
    for rel in ['bin/x64/Cyberpunk2077.exe','r6/cache/final.redscripts','r6/cache/tweakdb.bin','r6/cache/tweakdb_ep1.bin']:
        p=GAME/rel;st=p.stat();native.append({'path':str(p),'sha256':sha(p),'size':st.st_size,'mtime_ns':st.st_mtime_ns})
    prior=read(Q7/'worker_c/baseline_01/baseline.json')['current_game_read_only_inputs']
    assert {p['path']:p['sha256'] for p in native}=={p['path']:p['sha256'] for p in prior}
    block=Q7/'shared/marker_providers_01/provider_1.streamingblock.json';b=read(block)['Data']['RootChunk'];matches=[]
    for i,d in enumerate(b['descriptors']):
        ref=d['questPrefabNodeRef'];s=ref.get('$value',ref)
        if str(s).endswith('/#q304_pr_slider_stash_quest'):matches.append({'descriptor_index':i,'descriptor':d})
    assert len(matches)==1
    descriptor=matches[0];sector=descriptor['descriptor']['data']['DepotPath']['$value']
    targets=[sector,r'base\quest\additional_game_elements.questphase',r'base\quest\minor_quests\minorquests.questphase',
        r'base\quest\bugfixing\additional_content_bugfixing.questphase',
        r'base\open_world\mini_world_stories\watson\mws_wat_08\mws_wat_08.questphase',
        r'ep1\quest\main_quests\q304\phases\q304_slider_stash.questphase',
        r'base\open_world\street_stories\santo_domingo\rancho_corronado\sts_std_rcr_02\phases\sts_std_rcr_02_phase.questphase',
        r'base\open_world\street_stories\santo_domingo\rancho_corronado\sts_std_rcr_02\scenes\sts_std_rcr_02_dixon.scene']
    write(out/'baseline.json',{'status':'PINNED_QR7_FINAL_FIVE_UNKNOWN_TARGETS','epoch':str(ep),'epoch_sha256':sha(ep),'candidate':str(c),
        'completion':str(Q7/'completion.json'),'completion_sha256':sha(Q7/'completion.json'),'targeted_sources':ps,'native_inputs':native,
        'root_baseline_gate':'Coordinator independently verified all1577payloads/51package paths, installedPH3 and Atelier before this work.',
        'limits':['No large archive file is hashed by Worker C preparation. Extracted payloads will be pinned; current-run large hash reuse requires stable metadata.','No runtime candidate, game, save, fact, package or release writes.']})
    write(out/'original_five_contracts.json',rows)
    write(out/'new_targets.json',{'targets':targets,'voodoo_descriptor':descriptor,'descriptor_input':{'path':str(block),'sha256':sha(block)},
        'career_search_bound':'Three new exact registered-main ancestry carrier candidates. Follow at most one newly proven direct carrier step, not a broad quest census.',
        'native_search_bound':'Only Inventory condition, DeviceManager/door binding, logical hub and specific Inject downstream implementation as needed. Stop at unobservable saved state.'})
    print({'unknown_rows':len(rows),'targeted_sources':len(ps),'new_capture_targets':len(targets),'out':str(out)})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);main(p.parse_args().output)
