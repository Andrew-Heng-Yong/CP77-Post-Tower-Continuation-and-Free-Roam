"""Prepare a fresh PE1 successor with consistent Boolean setup admission."""
from pathlib import Path
from collections import defaultdict
import copy
import json
import re
import shutil
import sys
from inventory import HERE,WS,BASE,INSTALLED,read,sha,write
sys.path[:0]=[str(WS/'tools/parity_audit'),str(WS/'prealpha/quest_restoration_qr13')]
from resource_edit import Edit
from model import Resource

OUT=HERE/'candidate_02'
ARCHIVE='archive/pc/mod/zzzz_PTFR_Combined.archive'
HISTORY='r6/scripts/PTFR_Consolidated/PTFR_HistorySnapshotHS1.reds'
ACTIVITY='r6/scripts/PTFR_Consolidated/PTFR_ActivityStateR3.reds'


def class_span(text,name):
    starts=list(re.finditer(r'(?m)^(?:public |private )?(?:abstract )?class\s+(\w+)[^{\n]*\{',text))
    at=next(i for i,m in enumerate(starts) if m.group(1)==name)
    return starts[at].start(),starts[at+1].start() if at+1<len(starts) else len(text)


def replace_once(text,old,new):
    assert text.count(old)==1,old[:180]
    return text.replace(old,new,1)


def main():
    assert not OUT.exists() and not (HERE/'input_02').exists()
    decisions=read(HERE/'decisions_01.json');rules=decisions['rules']
    providers=read(HERE/'providers_01/manifest.json')
    assert providers['status']=='PASS_CURRENT_PHASE_AND_NATIVE_PREFIX_PROVIDERS' and not providers['issues']
    baseline_path=BASE/'package_manifest.json';baseline=read(baseline_path)
    installed=read(INSTALLED);game=Path(installed['game_root'])
    for row in installed['core_files']+installed['required_files']:
        assert sha(game/row['path'])==row['sha256'],row['path']
    for d,h in baseline['source_resources'].items():assert sha(BASE/'archive_source'/d)==h,d
    OUT.mkdir();shutil.copytree(BASE/'archive_source',OUT/'archive_source')
    for row in baseline['files']:
        p=BASE/'package'/row['path'];assert sha(p)==row['sha256']
        if row['path']==ARCHIVE:continue
        dest=OUT/'package'/row['path'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
    inp=HERE/'input_02';inp.mkdir()
    fresh={r['depot']:r for r in read(HERE/'fresh_01/manifest.json')['resources']}
    inventory=read(HERE/'inventory_02.json');resources={r['depot']:r for r in inventory['resources']}
    edits=[]
    for rule in rules:
        if not rule['native_guards']:continue
        d=rule['entry'];r=resources[d]
        source=fresh[d]['json'] if r['reuse']=='FRESH_EXPORT_REQUIRED' else r['source_json']
        source=Path(source);doc=read(source);original_model=Resource(doc).normalize()
        assert not original_model['errors']
        editor=Edit(copy.deepcopy(doc));changes=[]
        for guard in rule['native_guards']:
            graph=editor.graph(guard['graph']);node=editor.node(graph,int(guard['node']))
            wanted=set(guard['flags']);found=[]
            def widen(handle):
                data=editor.r.d(handle)
                if not isinstance(data,dict):return handle
                if data.get('$type')=='questFactsDBCondition':
                    c=editor.r.d(data['type'])
                    if c.get('factName') in wanted and c.get('comparisonType')=='Equal' and c.get('value')==0:
                        found.append(c['factName'])
                        return editor.logic('OR',[editor.clone(handle,editor.r),editor.fact(c['factName'],1)])
                if data.get('$type')=='questLogicalCondition':data['conditions']=[widen(h) for h in data['conditions']]
                return handle
            node['condition']=widen(node['condition'])
            assert set(found)==wanted,(d,guard,found)
            changes.append(guard|{'comparison_occurrences':len(found)})
        edited=inp/(str(len(edits)).zfill(2)+'.json');write(edited,editor.ordered())
        edits.append({'depot':d,'id':rule['id'],'source_json':str(source),'source_json_sha256':sha(source),'source_raw_sha256':r['sha256'],'edited_json':str(edited),'edited_json_sha256':sha(edited),'guards':changes})
    script_text={}
    for rule in rules:
        if rule['family']!='SIDE':continue
        rel=rule['script'];text=script_text.get(rel,(BASE/'package'/rel).read_bytes().decode('utf-8'))
        a,b=class_span(text,rule['class']);chunk=text[a:b]
        pattern=r'(func FactMax'+str(rule['index'])+r'\([^\n]*?\)[^\n]*?\{\s*return )(\[[^\n]*?\])(;)'
        matches=list(re.finditer(pattern,chunk));assert len(matches)==1,(rel,rule['id'])
        match=matches[0];values=json.loads(match.group(2))
        table=next(t for t in inventory['script_tables'] if t['class']==rule['class'])
        row=next(r for r in table['rows'] if r['index']==rule['index'])
        for flag in rule['flags']:
            i=row['FactNames'].index(flag);assert values[i]==0;values[i]=1
        chunk=chunk[:match.start(2)]+json.dumps(values)+chunk[match.end(2):]
        text=text[:a]+chunk+text[b:]
        script_text[rel]=text
    # A new initialized=1 admission needs an accepted Inactive baseline. This is
    # a read-only query of existing history, never a rewrite or new certificate.
    families={r['class']:r['script'] for r in rules if r['family']=='SIDE'}
    for data_cls,rel in families.items():
        text=script_text[rel];owner_cls=data_cls.replace('SideJobData','SideJobs')
        a,b=class_span(text,owner_cls);chunk=text[a:b]
        anchor='    if jm.HasAnyDelayedStateChanges() { sample.valid = false; sample.reason = "Journal changed during observation; waiting."; }'
        note='''    if !PreparedEntryPolicyPE1.BaselineAllows(this.GetGameInstance(), DATA.ID(i)) {
      sample.valid = false; sample.reason = "Prepared encounter requires an accepted Inactive baseline; progress preserved.";
    }
'''.replace('DATA',data_cls)
        chunk=replace_once(chunk,anchor,note+anchor)
        script_text[rel]=text[:a]+chunk+text[b:]
    activity=(BASE/'package'/ACTIVITY).read_bytes().decode('utf-8')
    old='    let a=NativeGigDataU9.Facts(i);k=0;while k<ArraySize(a) { if this.Fact(a[k])!=0 { return false; };k+=1; }'
    new='''    let a=NativeGigDataU9.Facts(i);k=0;while k<ArraySize(a) { if !PreparedEntryPolicyPE1.Allows(NativeGigDataU9.ID(i),a[k],this.Fact(a[k])) { return false; };k+=1; }
    if !PreparedEntryPolicyPE1.BaselineAllows(this.GetGameInstance(),NativeGigDataU9.ID(i)) { return false; }'''
    activity=replace_once(activity,old,new);script_text[ACTIVITY]=activity
    history=(BASE/'package'/HISTORY).read_bytes().decode('utf-8')
    old='''    indices=SnapshotDataHS1.U9FactIndices(i);k=0;
    while k<ArraySize(indices) { if this.rows[i].facts[indices[k]]!=0 { return false; };k+=1; }return true;'''
    new='''    indices=SnapshotDataHS1.U9FactIndices(i);k=0;
    let names=SnapshotDataHS1.Facts(i);let prepared=false;
    while k<ArraySize(indices) {
      let value=this.rows[i].facts[indices[k]];
      if !PreparedEntryPolicyPE1.Allows(id,names[indices[k]],value) { return false; }
      if value==1 { prepared=true; }
      k+=1;
    }
    if prepared && this.rows[i].states[0]!=1 { return false; }
    return true;'''
    if old not in history:
        old=old.replace('\n','\r\n');new=new.replace('\n','\r\n')
    history=replace_once(history,old,new)
    helper='''

// PE1: source-reviewed Boolean setup receipts. No fields, cache/schema changes,
// native writes, forced pins, owner restart, or interpretation of stage counters.
public abstract class PreparedEntryPolicyPE1 {
  public static func Facts(id: String) -> array<String> {
FACTS
    return [];
  }
  public static func BaselineIDs(id: String) -> array<String> {
BASELINES
    return [];
  }
  public static func Allows(id: String,fact: String,value: Int32) -> Bool {
    if value==0 { return true; }
    if value!=1 { return false; }
    let names=PreparedEntryPolicyPE1.Facts(id);let k=0;
    while k<ArraySize(names) { if Equals(names[k],fact) { return true; };k+=1; }
    return false;
  }
  public static func BaselineAllows(game: GameInstance,id: String) -> Bool {
    let qs=GameInstance.GetQuestsSystem(game);if !IsDefined(qs) { return false; }
    let names=PreparedEntryPolicyPE1.Facts(id);let k=0;let prepared=false;
    while k<ArraySize(names) { if qs.GetFactStr(names[k])==1 { prepared=true; };k+=1; }
    if !prepared { return true; }
    let snapshot=SnapshotStateHS1.Get(game);if !IsDefined(snapshot) { return false; }
    let ids=PreparedEntryPolicyPE1.BaselineIDs(id);if ArraySize(ids)==0 { return false; };k=0;
    while k<ArraySize(ids) { if !snapshot.FreshS29(ids[k]) { return false; };k+=1; }
    return true;
  }
}
'''
    helper=helper.replace('FACTS','\n'.join('    if Equals(id,'+json.dumps(r['id'])+') { return '+json.dumps(r['flags'])+'; }' for r in rules))
    helper=helper.replace('BASELINES','\n'.join('    if Equals(id,'+json.dumps(r['id'])+') { return '+json.dumps(r['baseline_ids'])+'; }' for r in rules))
    assert 'PreparedEntryPolicyPE1' not in (BASE/'package'/HISTORY).read_text(encoding='utf-8-sig')
    script_text[HISTORY]=history+helper
    script_edits=[]
    for rel,text in sorted(script_text.items()):
        dest=OUT/'package'/rel;dest.write_bytes(text.encode('utf-8'))
        script_edits.append({'path':rel,'before':sha(BASE/'package'/rel),'after':sha(dest)})
    plan={'schema':1,'epoch':'PE1','predecessor':'KM1','authorization':'User requested the new marker and encounter policy across all post-Tower content.','baseline_package':str(baseline_path),'baseline_package_sha256':sha(baseline_path),'installed_baseline':str(INSTALLED),'installed_baseline_sha256':sha(INSTALLED),'decisions':str(HERE/'decisions_01.json'),'decisions_sha256':sha(HERE/'decisions_01.json'),'providers':str(HERE/'providers_01/manifest.json'),'providers_sha256':sha(HERE/'providers_01/manifest.json'),'candidate':str(OUT),'resources':edits,'scripts':script_edits,'rules':rules,'archive_payloads':1581,'new_depots':0,'new_ArchiveXL_phase_ids':0,'saved_fields_or_schema_changes':0,'native_runtime_writes_added':0,'game_writes':0,'save_writes':0,'installed':False}
    write(inp/'plan.json',plan)
    checkpoint=read(HERE/'checkpoint.json');checkpoint.update(status='PREPARED_PENDING_COOK_COMPILE_AND_VERIFICATION',inventory='inventory_02.json',decisions='decisions_01.json',plan='input_02/plan.json',candidate='candidate_02',next_action='Cook/read back the 12 private entry resources, verify exact guard and script changes, compile the complete registered source set, then package and test a guarded successor transaction.')
    (HERE/'checkpoint.json').write_text(json.dumps(checkpoint,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'resources':len(edits),'guard_nodes':sum(len(e['guards']) for e in edits),'scripts':len(script_edits),'entries':len(rules),'setup_flags':sum(len(r['flags']) for r in rules)}))


if __name__=='__main__':
    main()
