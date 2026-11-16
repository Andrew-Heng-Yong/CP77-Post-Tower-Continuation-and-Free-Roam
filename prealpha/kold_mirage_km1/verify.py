"""Independently evaluate cooked guards and constrain the complete KM1 delta."""
from pathlib import Path
import copy
import json
import re
import sys
from prepare import HERE, BASE, OUT, ENTRY, SCRIPT, ARCHIVE, read, sha, write
sys.path.insert(0,str(HERE.parents[1]/'tools/parity_audit'))
from model import Resource,compare_graph
from common import walk


def normal(p):
    m=Resource(read(p)).normalize()
    assert not m['errors'],m['errors']
    return m


def eval_guard(c,facts,journals):
    kind=c['$type']
    if kind=='questLogicalCondition':
        values=[eval_guard(x,facts,journals) for x in c['conditions']]
        if c['operation']=='AND':return all(values)
        if c['operation']=='OR':return any(values)
        raise AssertionError(c['operation'])
    if kind=='questFactsDBCondition':
        t=c['type'];assert t['$type']=='questVarComparison_ConditionType'
        a=facts[t['factName']];b=t['value']
        return {'Equal':a==b,'Greater':a>b,'GreaterOrEqual':a>=b,'Less':a<b,'LessOrEqual':a<=b}[t['comparisonType']]
    if kind=='questJournalCondition':
        t=c['type'];assert t['$type']=='questJournalEntryState_ConditionType' and t['inverted']==0
        return journals[t['path']['realPath']]=={'Inactive':1,'Active':2,'Succeeded':3,'Failed':4}[t['state']]
    raise AssertionError(kind)


def expected_widen(c):
    if isinstance(c,list):return [expected_widen(x) for x in c]
    if not isinstance(c,dict):return c
    if c.get('$type')=='questFactsDBCondition' and c['type'].get('factName')=='mq016_active':
        assert c['type']['value']==0 and c['type']['comparisonType']=='Equal'
        other=copy.deepcopy(c);other['type']['value']=1
        return {'$type':'questLogicalCondition','operation':'OR','conditions':[copy.deepcopy(c),other]}
    return {k:expected_widen(v) for k,v in c.items()}


def main():
    output=HERE/'verification.json';assert not output.exists()
    plan=read(HERE/'input_01/plan.json')
    assert sha(plan['edited_json'])==plan['edited_json_sha256']
    cooked=read(HERE/'readback_01/manifest.json')
    assert sha(cooked['raw'])==cooked['sha256'] and sha(cooked['readback'])==cooked['readback_sha256']
    before=normal(plan['source_json']);after=normal(cooked['readback'])
    diffs=compare_graph(before,after)
    assert len(diffs)==2 and {(d['kind'],d['graph'],d['node']) for d in diffs}=={('NODE_PAYLOAD_CHANGED','root',str(i)) for i in [65003,65004]},diffs
    checks=[]
    def check(label,result):
        assert result,label
        checks.append({'name':label,'pass':True})
    for i in ['65003','65004']:
        old=before['graphs']['root']['nodes'][i]
        new=after['graphs']['root']['nodes'][i]
        expected=copy.deepcopy(old['payload']);expected['condition']=expected_widen(expected['condition'])
        check(i+' exact independent predicate transform',new['payload']==expected)
        check(i+' all 63 journal checks retained',len(old['journal_paths'])==len(new['journal_paths'])==63)
        facts={r['factName']:r['value'] for r in old['reads'] if r['$type']=='questVarComparison_ConditionType'}
        journals={r['path']['realPath']:1 for r in old['reads'] if r['$type']=='questJournalEntryState_ConditionType'}
        for value in [-2,-1,0,1,2,3]:
            f=facts|{'mq016_active':value}
            check(i+' active='+str(value)+' accepted only for 0/1',eval_guard(new['payload']['condition'],f,journals)==(value in [0,1]))
            check(i+' predecessor active='+str(value)+' fresh only',eval_guard(old['payload']['condition'],f,journals)==(value==0))
        prepared=facts|{'mq016_active':1}
        for name,value in facts.items():
            if name=='mq016_active':continue
            check(i+' protected fact '+name,not eval_guard(new['payload']['condition'],prepared|{name:value+1},journals))
        for path in journals:
            check(i+' active progress protected '+path,not eval_guard(new['payload']['condition'],prepared,journals|{path:2}))
        for state in [3,4]:
            check(i+' terminal quest state '+str(state)+' protected',not eval_guard(new['payload']['condition'],prepared,journals|{'quests/minor_quest/mq016_bartmoss':state}))
    check('All old graph nodes, edges, sockets and resource metadata retained',before['metadata']==after['metadata'] and all(before['graphs'][p]['edges']==after['graphs'][p]['edges'] and set(before['graphs'][p]['nodes'])==set(after['graphs'][p]['nodes']) for p in before['graphs']))
    script_before=(BASE/'package'/SCRIPT).read_bytes()
    script_after=(OUT/'package'/SCRIPT).read_bytes()
    check('Script has exactly one integer data change',script_after==script_before.replace(plan['script_literal_before'].encode(),plan['script_literal_after'].encode(),1))
    text=script_after.decode().split('public class SideJobsS30 ',1)[0]
    def data(name):
        return json.loads(re.search(r'func '+name+r'\(\).*?return (\[[^\]]*\])',text).group(1))
    names,mins,maxs=data('FactNames0'),data('FactMin0'),data('FactMax0')
    check('Script active range is precisely 0..1',mins[names.index('mq016_active')]==0 and maxs[names.index('mq016_active')]==1)
    check('All seven other protected script facts stay zero',all(a==b==0 for n,a,b in zip(names,mins,maxs) if n!='mq016_active'))
    baseline=read(BASE/'package_manifest.json')
    members={str(p.relative_to(OUT/'archive_source')).replace('/','\\'):sha(p) for p in (OUT/'archive_source').rglob('*') if p.is_file()}
    check('Exact existing archive inventory',set(members)==set(baseline['source_resources']) and len(members)==1581)
    changed=[d for d,h in members.items() if h!=baseline['source_resources'][d]]
    check('Only the one private entry changed',changed==[ENTRY])
    package_files={p.relative_to(OUT/'package').as_posix():p for p in (OUT/'package').rglob('*') if p.is_file()}
    original_files={r['path']:r for r in baseline['files']}
    check('Only archive is pending packing',set(package_files)==set(original_files)-{ARCHIVE})
    check('Only S29 changed among staged package files',[r for r,p in package_files.items() if sha(p)!=original_files[r]['sha256']]==[SCRIPT])
    providers=read(HERE/'source_01/providers.json')
    installed=read(plan['installed_baseline']);game=Path(installed['game_root'])
    current_archives={str(p) for p in (game/'archive/pc').rglob('*.archive') if p.is_file()}
    check('Provider inventory remains exact',current_archives=={r['path'] for r in providers['archives']})
    for row in providers['archives']:
        check('Archive provider stable '+Path(row['path']).name,Path(row['path']).stat().st_size==row['bytes'])
    xl='archive/pc/mod/zzzz_PTFR_Combined.archive.xl'
    check('XL registrations byte-identical',sha(game/xl)==sha(OUT/'package'/xl))
    compile_result=read(HERE/'compile_01/result.json')
    check('Complete registered-source compile passed',compile_result['status']=='PASS_CURRENT_REGISTERED_SOURCE_COMPILE' and compile_result['overlay']['sha256']==sha(OUT/'package'/SCRIPT))
    write(output,{'status':'PASS_KM1_TYPED_GUARDS_AND_COMPLETE_DELTA','plan_sha256':sha(HERE/'input_01/plan.json'),'cooked_sha256':sha(HERE/'readback_01/manifest.json'),'changes':diffs,'checks':checks,'changed_depots':changed,'archive_members':len(members),'retained_archive_members':len(members)-1,'new_depots':0,'new_ArchiveXL_phase_ids':0,'namespace_evidence':'Exact existing entry depot, all node IDs and graph edges retained; byte-identical XL; unique source provider across current archive inventory.','compile_result_sha256':sha(HERE/'compile_01/result.json'),'limits':'Predicate evaluation and source/byte verification; no engine scheduling or gameplay pass.','game_writes':0,'save_writes':0})
    print('PASS:',len(checks),'checks; exactly two guard payload changes, one script range value, and no other resource changes.')


if __name__=='__main__':
    main()
