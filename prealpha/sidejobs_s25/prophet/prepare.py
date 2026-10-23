"""Fresh Prophet entry; catalogue is evidence, never an invented save history."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'prealpha/sidejobs_s23'))
from audit import graphs,walk,value

def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()

def main():
    dest=HERE/'contract.json'
    assert not dest.exists(), 'Immutable contract exists'
    capture='research/sidejobs_s23/live_20261016_01/capture.json'
    catalogue='research/sidejobs_s24/ep1/native_02/json/base/journal/cooked_journal.journal.json'
    parent='research/sidejobs_s2/sacrum_audit/native_01/raw/base/quest/minor_quests/minorquests.questphase'
    old='prealpha/sidejobs_s23/base_b/contract.json'
    job=next(j for j in read(ROOT/capture)['first']['jobs'] if j['id']=='mq026_conspiracy')
    prior=next(o for o in read(ROOT/old)['owners'] if o['key']=='MQ026')
    pins={p:sha(ROOT/p) for p in (capture,catalogue,parent,parent.replace('/raw/','/json/')+'.json',old,'prealpha/sidejobs_s25/prophet/prepare.py','prealpha/sidejobs_s23/audit.py')}
    facts={k:0 for k in prior['facts_equal']}
    closure=[];refs=set();writers=[]
    folder=ROOT/'research/sidejobs_s23/native_01/raw/base/quest/minor_quests/mq026'
    all_raw={p.relative_to(ROOT).as_posix().split('/raw/',1)[1].replace('/','\\'):p for p in folder.rglob('*') if p.is_file() and p.suffix in ('.questphase','.scene')}
    pending=['base\\quest\\minor_quests\\mq026\\mq026.questphase'];seen=set()
    while pending:
        depot=pending.pop()
        if depot in seen:continue
        assert depot in all_raw, ('Missing executable dependency',depot)
        seen.add(depot);raw=all_raw[depot]
        rel=raw.relative_to(ROOT).as_posix();jp=rel.replace('/raw/','/json/')+'.json'
        pins[rel]=sha(raw);pins[jp]=sha(ROOT/jp);closure.append(rel)
        for obj in walk(read(ROOT/jp)):
            name=value(obj.get('factName',''))
            if isinstance(name,str) and name.startswith(('mq026_','mq018_','mq027_50_prophet','mq027_5_prophet')):
                facts[name]=0
                if obj.get('$type')=='questSetVar_NodeType':writers.append({'source':jp,'fact':name,'value':obj.get('value'),'exact':obj.get('setExactValue')})
            if 'DepotPath' in obj:
                p=value(obj['DepotPath'])
                if isinstance(p,str) and p.startswith('base\\') and p.endswith(('.questphase','.scene')):
                    refs.add(p);pending.append(p)
    depot_map={p.split('/raw/',1)[1].replace('/','\\'):p for p in closure}
    assert refs<=depot_map.keys(), sorted(refs-depot_map.keys())
    # Stock root initializes both before the first local trigger or interaction.
    # They are passive startup state, not evidence of accepted dialogue.
    ranges={k:{'min':0,'max':1} for k in ('mq026_active','mq026_started')}
    for k in ranges: facts.pop(k)
    facts.update({'PTFRS23_MQ026_Issued':0,'PTFRS23_MQ026_Finished':0,'PTFRS23_MQ026_Fault':0})
    journals=[{'path':j['path'],'class':j['class'],'states':[1]} for j in job['journals']]
    owner={'id':'mq026_conspiracy','ids':['mq026_conspiracy'],'title':"The Prophet's Song",'key':'MQ026_FRESH','tag':'PTFRS25_MQ026_FRESH',
           'depot':'towercontinued\\sidejobs_s25\\prophet\\mq026_fresh.questphase',
           'facts_equal':dict(sorted(facts.items())),'fact_ranges':ranges,'journals':journals,
           'phone_dependencies':[],'contact_copy':None,'parent_nodes':[39],'parent_node':39,'parent_edges':[],
           'parent_start':1004,'issue_target':39,'native_depot':'base\\quest\\minor_quests\\mq026\\mq026.questphase',
           'native_source':prior['native_source'],'native_dependencies':closure,
           'old_owner_exclusion_required':{'tag':'PTFRS23_MQ026','new_fact':'PTFRS25_MQ026_FRESH_Issued','value':0},
           'scope':'Unstarted local entry only; every journal entry Inactive, all actual sermon/donation/combat/progress facts zero. Original parent path contains logical hubs only; original full per-job gameplay remains untouched.'}
    result={'schema':1,'status':'FRESH_CONTRACT_NOT_LIVE','capture_catalogue':capture,'source_pins':pins,'owners':[owner],
            'native_fact_writers':writers,'closure_resources':len(closure),'reference_closure_checked':sorted(refs),
            'limitations':['Earlier heard-sermon/donation progress is not reset; existing S23 remains authoritative for its supported stage.',
                           'Requires S25 policy resource gating old S23 unissued owner against fresh Issued1 before deployment.',
                           'Original Johnny presentation is handled by unchanged JV1; live voice/body check pending.']}
    dest.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'owners':1,'resources':len(closure),'facts':len(facts),'contract_sha256':sha(dest)}))

if __name__=='__main__':main()
