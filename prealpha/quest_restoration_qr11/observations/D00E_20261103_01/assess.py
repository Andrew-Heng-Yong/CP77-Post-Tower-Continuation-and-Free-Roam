"""Assess frozen human D00E evidence; read-only inputs, fresh local outputs."""
from pathlib import Path
import collections,hashlib,json
H=Path(__file__).resolve().parent;Q11=H.parents[1];D=Q11/'d00e_01'
E=D/'evidence/D00_20261103T162157Z_52fee7'
FACT='phonecall_player_with_muamar_el_capitan_reyes'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(name,value):
    p=H/name;assert not p.exists();p.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
def main():
    s=read(E/'summary.json');capture=E/s['run_id'];rows=[json.loads(x)for x in capture.read_text().splitlines()]
    assert sha(capture)==s['capture_source']['sha256']=='EF31629E3BFE4A44C67A1CAB2BF312882BC3E4D032643F46E7B33217E9F10CE0'
    assert all(r['schema']==2 and r['profile']=='D00E'and r['module']=='PTFR_QR9_Diagnostics'and r['seq']==i+1 and r['run_id']==capture.name for i,r in enumerate(rows))
    events=collections.Counter(r['event']for r in rows)
    assert rows[0]['event']=='CAPTURE_START'and rows[-1]['event']=='CAPTURE_CLEANUP'
    assert rows[0]['data']['version']=='QR10D01'and rows[0]['data']['watch_facts']==[FACT]
    assert events['CAPTURE_START']==events['ATTACHED_BASELINE']==events['STOP']==events['CAPTURE_CLEANUP']==1
    assert not any(events[x]for x in('FACT_SAMPLE_ERROR','FACT_READ_FAILED','API_UNAVAILABLE','FACT_DELIVERY'))
    baseline=next(r for r in rows if r['event']=='ATTACHED_BASELINE')['data']['facts'][FACT]
    changes=[r for r in rows if r['event']=='FACT_SAMPLE_CHANGE'];sequence=[baseline];previous=baseline
    for r in changes:
        x=r['data'];v=x['current_sample'];assert x['fact']==FACT and x['previous_sample']==previous and previous!=v
        assert isinstance(v,(int,float))and v%1==0 and -2147483648<=v<=2147483647 and not x['gap_contained_read_error']
        assert x['previous_success_elapsed_s']<=x['detected_elapsed_s']==r['wall_elapsed_s']
        previous=v;sequence.append(v)
    assert len(changes)==3 and sequence==[0,1,2,0]
    stop=next(r for r in rows if r['event']=='STOP');cleanup=rows[-1]['data']
    assert stop['data']['reason']=='D00E_DONE'and stop['data']['sampled_changes']==len(changes)
    assert stop['data']['fact_getter_calls']==46 and stop['data']['sample_rounds']==45 and stop['wall_elapsed_s']==92
    assert cleanup['sampling_disabled']is True and cleanup['native_subscriptions_created']==0
    states=[r for r in rows if r['event']in('ATTACHED_STATE','BOUNDED_STATE_CHANGE')]
    assert [r['data']['phone_active']for r in states]==[False,True,False]
    assert all(not r['data']['errors']for r in states)
    m=read(D/'diagnostics_manifest_01.json')
    expected={r['path']:r.get('after',r.get('sha256'))for r in m['files']+m['required_files']}
    measured={r['path']:r['sha256']for r in s['installed_current_hashes']}
    assert len(expected)==len(measured)==60 and measured==expected and not s['issues']and not s['errors']
    assert all(r['matches']and r['expected']==expected[r['path']]for r in s['installed_current_hashes'])
    receipt=Path(s['installation_receipt']['path']);assert sha(receipt)==s['installation_receipt']['sha256']
    original=Path(s['capture_source']['path']);assert sha(original)==sha(capture)
    inputs=[{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size}for p in E.iterdir()if p.is_file()]
    for t in s['log_tails']:
        if 'output'in t:assert sha(E/t['output'])==t['sha256']
    broad=(E/'tail_scripting.log').read_text(encoding='utf-8',errors='replace')
    native_lines=[line for line in broad.splitlines()if FACT in line]
    result={'status':'PASS','test':'D00E_NATURAL_GETTER_DIFFERENCE_VALIDATION','capture':str(capture),'capture_sha256':sha(capture),
        'user_confirmation':{'prompt':'Did the El Capitan call connect or show dialogue and end normally? Also confirm whether you loaded ManualSave-24 (2 Nov, 4:37 PM), and mention any unexpected behavior.',
            'answer':'yes','accepted_scope':'User confirmation of normal call and requested working slot; no specific anomaly reported. No engine save-ID measurement.'},
        'observed':{'sampled_sequence':sequence,'changes':[{'seq':r['seq'],'utc':r['utc'],**r['data']}for r in changes],
            'phone_active_sequence':[r['data']['phone_active']for r in states],'duration_wall_s':92,'sample_rounds':45,'fact_getter_calls':46,
            'stop_reason':'D00E_DONE','capture_rows':len(rows),'errors':[],'cleanup':'sampling disabled; reported zero native quest subscriptions by design'},
        'installed_hashes_matching':60,'source_binding_limit':'Post-run current hashes + prior verified deployment and capture declaration; not retrospective executed-byte or engine-owner proof.',
        'native_callbacks':'UNSUPPORTED_NOT_TESTED','actual_graph_listener_controller_ownership':'NOT_OBSERVED',
        'broader_fact_log':{'matching_lines':native_lines,'meaning':'No matching entry in supplied tail is not a negative gameplay result; this PASS uses actual sampled getters + phone getter + human confirmation.'},
        'coverage':'One ordinary El Capitan call validates bounded sampling. No precise native-write ordering, numeric phone-state enum, all-fact/event coverage or quest restoration certification.',
        'not_repeated':['Wilson','Bullets','Zane','Cynthia','completed-state reload tests'],
        'next':'Do not repeat this passed test. No additional quest fixture currently qualified; preserve existing holds and unknowns.',
        'assessment_actions':{'game_launch':0,'CUA':0,'runtime_or_save_edits':0},'inputs':inputs}
    write('result.json',result)
    write('coverage.json',{'D00_Regina':'NOT_TESTABLE_CONTACT_UNAVAILABLE','D00E_ElCapitan':'PASS_BOUNDED_NATURAL_SAMPLER_FIXTURE',
        'native_callback_delivery':'UNSUPPORTED_NOT_TESTED','new_qualified_quest_tests':[],
        'rule':'One diagnostic test, separate from QR9 planned quest alternatives/functional observations; no blanket runtime PASS.'})
    print({'status':'PASS','sequence':sequence,'duration_s':92,'getter_errors':0,'matching_current_hashes':60,'native_callbacks':'UNSUPPORTED_NOT_TESTED'})
if __name__=='__main__':main()
