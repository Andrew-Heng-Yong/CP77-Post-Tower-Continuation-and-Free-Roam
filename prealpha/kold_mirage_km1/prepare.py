"""Build a fresh JP1 successor accepting only active=0 or active=1."""
from pathlib import Path
import copy
import hashlib
import json
import shutil
import sys

HERE=Path(__file__).resolve().parent
WS=HERE.parents[1]
JP1=WS/'prealpha/johnny_dialogue_pilot_jp1'
BASE=JP1/'candidate_03'
OUT=HERE/'candidate_01'
ENTRY=r'towercontinued\sidejobs_s29\entries\mq016_bartmoss.questphase'
SCRIPT='r6/scripts/PTFR_Consolidated/PTFR_SideJobsS29.reds'
ARCHIVE='archive/pc/mod/zzzz_PTFR_Combined.archive'
sys.path[:0]=[str(WS/'tools/parity_audit'),str(WS/'prealpha/quest_restoration_qr13')]
from resource_edit import Edit
from model import Resource


def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def sha(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest().upper()


def write(p,v):
    with Path(p).open('x',encoding='utf-8',newline='\n') as f:
        json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')


def main():
    assert not OUT.exists() and not (HERE/'input_01').exists()
    review=read(HERE/'analysis_01.json')
    assert review['status']=='SOURCE_AND_HISTORICAL_OWNER_REVIEW_COMPLETE'
    baseline_manifest=BASE/'package_manifest.json'
    baseline=read(baseline_manifest)
    installed_path=JP1/'deployment_01/installed_manifest_01.json'
    installed=read(installed_path)
    game=Path(installed['game_root'])
    for r in installed['core_files']+installed['required_files']:
        assert sha(game/r['path'])==r['sha256'],r['path']
    provider_manifest=HERE/'source_01/providers.json'
    provider,=[r for r in read(provider_manifest)['resources'] if r['depot']==ENTRY]
    assert provider['sha256']==baseline['source_resources'][ENTRY]
    assert sha(provider['raw'])==provider['sha256'] and sha(provider['json'])==provider['json_sha256']
    expected=baseline['source_resources']
    members={str(p.relative_to(BASE/'archive_source')).replace('/','\\'):p for p in (BASE/'archive_source').rglob('*') if p.is_file()}
    assert set(members)==set(expected) and len(members)==1581
    for d,p in members.items():
        assert not p.is_symlink() and not (p.stat().st_file_attributes&0x400)
        assert sha(p)==expected[d],d
    OUT.mkdir()
    shutil.copytree(BASE/'archive_source',OUT/'archive_source')
    for r in baseline['files']:
        p=BASE/'package'/r['path']
        assert sha(p)==r['sha256']
        if r['path']==ARCHIVE:
            continue
        target=OUT/'package'/r['path']
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(p,target)
    inp=HERE/'input_01';inp.mkdir()
    document=read(provider['json'])
    editor=Edit(copy.deepcopy(document))
    root=editor.graph('root')
    changed=[]
    def widen(h):
        data=editor.r.d(h)
        if not isinstance(data,dict):
            return h
        if data.get('$type')=='questFactsDBCondition':
            condition=editor.r.d(data['type'])
            if condition.get('factName')=='mq016_active':
                assert condition['comparisonType']=='Equal' and condition['value']==0
                changed.append(True)
                return editor.logic('OR',[editor.clone(h,editor.r),editor.fact('mq016_active',1)])
        if data.get('$type')=='questLogicalCondition':
            data['conditions']=[widen(c) for c in data['conditions']]
        return h
    for node_id in [65003,65004]:
        node=editor.node(root,node_id)
        before=len(changed)
        node['condition']=widen(node['condition'])
        assert len(changed)==before+1
    edited=editor.ordered()
    assert not Resource(edited).normalize()['errors']
    edited_path=inp/'mq016_entry.json'
    write(edited_path,edited)
    source_script=BASE/'package'/SCRIPT
    original=source_script.read_bytes()
    text=original.decode('utf-8')
    before,tail=text.split('public class SideJobsS30 ',1)
    old='public static func FactMax0() -> array<Int32> { return [0, 0, 0, 0, 0, 0, 0, 0]; }'
    new='public static func FactMax0() -> array<Int32> { return [0, 1, 0, 0, 0, 0, 0, 0]; }'
    assert before.count(old)==1 and before.count(new)==0
    after=before.replace(old,new,1)+'public class SideJobsS30 '+tail
    (OUT/'package'/SCRIPT).write_bytes(after.encode('utf-8'))
    plan={
        'schema':1,'epoch':'KM1','predecessor':'JP1','authorization':'User explicitly requested marker/encounter repair and widening mq016_active to 0 or 1.',
        'baseline_package':str(baseline_manifest),'baseline_package_sha256':sha(baseline_manifest),
        'installed_baseline':str(installed_path),'installed_baseline_sha256':sha(installed_path),
        'candidate':str(OUT),'depot':ENTRY,'source_raw':provider['raw'],'source_raw_sha256':provider['sha256'],
        'source_json':provider['json'],'source_json_sha256':provider['json_sha256'],
        'edited_json':str(edited_path),'edited_json_sha256':sha(edited_path),
        'script':SCRIPT,'script_before':sha(source_script),'script_after':sha(OUT/'package'/SCRIPT),
        'script_literal_before':old,'script_literal_after':new,'graph_guard_nodes':[65003,65004],
        'behavior':'Allow precisely active=0 or active=1 while retaining all 63 Inactive journal checks, the seven other zero MQ016 facts, existing private receipts, original prerequisites and Tower/support/startup/profile/player checks. The native owner activates its POI and approach/scan wait.',
        'source_review':str(HERE/'analysis_01.json'),'source_review_sha256':sha(HERE/'analysis_01.json'),
        'review_plan_supersession':'The user selected a literal 0-or-1 widening. No extra debug prerequisite, alternate graph input, new node, reset, forced marker or native-resource override is introduced.',
        'unchanged':'All existing nodes, edges, receipts, identifiers, XL registrations, reward/pickup/cleanup, native debug branches and JP1 dialogue removals remain intact.',
        'game_writes':0,'save_writes':0,'installed':False
    }
    write(inp/'plan.json',plan)
    print('Prepared fresh KM1 candidate: one S29 range value and two equivalent 0-or-1 native guard alternatives; not installed.')


if __name__=='__main__':
    main()
