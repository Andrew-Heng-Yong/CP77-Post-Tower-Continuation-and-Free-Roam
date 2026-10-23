"""Independent peer checks against the combined U9 generated resource graphs."""
import json
from catalog_gig_rollout_r2 import ROOT,read,sha,walk
from inspect_special_gigs_u9 import graphs
from test_special_gigs_u9_retaliation import check as check_retaliation

OUT=ROOT/'research/gig_restoration/special_gigs_u9'
NATIVE=ROOT/'research/gig_restoration/native_gigs_u9'

def main():
    nm=read(NATIVE/'manifest.json');sm=read(OUT/'manifest.json');rows=[]
    for ident in ('sts_ep1_06','sts_ep1_07'):
        rel='research/gig_restoration/native_gigs_u9/'+ident+'_entry.json'
        gs={g['path']:g for g in graphs(rel)};gate=gs['root/50/9']
        assert len(gate['nodes'])==3 and gate['edges']==[[0,'Out',2,'In'],[2,'Out',1,'In']]
        ns={n['id']:n for n in gate['nodes']}
        assert ns[2]['condition']['conditions'][0]['type']['factName']=='PTFRU9_EP1Tier3_Ready'
        assert not any(v.get('realPath')=='contacts/mr_hands/mr_hands_global_msg/new_sts_unlocked' for v in walk(gs))
        # Initial user admission arms Permit; original shared gate eligibility
        # still lives inside its native definition instead of becoming a forced tier.
        rows.append(dict(id=ident,gate='owned_ready_wait_only',native_unlock_message_copied=False))
    shared=graphs('research/gig_restoration/special_gigs_u9/ep1_tier3_gate.json')
    assert len([g for g in shared if g['path']=='root/50/9'])==1
    runtime=(ROOT/'redscript/PTFR_NativeGigsU9/NativeGigsU9.reds').read_text()
    assert 'PTFRU9_EP1Tier3_Ready' not in runtime
    assert '"ep1/points_of_interest/street_stories/"' in runtime or '"ep1/"' in runtime
    spy={g['path']:g for g in graphs('research/gig_restoration/native_gigs_u9/sts_ep1_08_entry.json')}['root/50']
    ns={n['id']:n for n in spy['nodes']}
    cleanup=[n['id'] for n in spy['nodes'] if 'sts_ep1_08_cleanup.questphase' in json.dumps(n)]
    assert len(cleanup)==1
    target=cleanup[0]
    assert [23,'Organitopia done',target,'Organitopia cleanup'] in spy['edges']
    assert [23,'Out1',target,'In1'] in spy['edges']
    assert [23,'Out1',65005,'In'] in spy['edges']
    assert [23,'Organitopia done',65005,'In'] not in spy['edges']
    assert not any(e[2]==65006 for e in spy['edges'])
    retaliation=check_retaliation()
    writers={'sts_cct_dtn_03':'animals','sts_std_arr_11':'6thstreet','sts_std_rcr_03':'6thstreet',
      'sts_wat_kab_07':'tygerclaws','sts_wat_lch_06':'tygerclaws','sts_wat_lch_01':'tygerclaws','sts_wat_lch_03':'tygerclaws',
      'sts_bls_ina_02':'wraiths','sts_bls_ina_03':'wraiths','sts_hey_gle_04':'valentinos',
      'sts_wat_kab_02':'maelstroms','sts_wat_nid_05':'maelstroms','sts_wbr_hil_07':'tygerclaws'}
    for ident,gang in writers.items():
        entry=graphs('research/gig_restoration/native_gigs_u9/'+ident+'_entry.json')
        conditions=[n['condition'] for g in entry for n in g['nodes'] if n.get('condition')]
        expected={'PTFRU9_Retaliation_Issued','PTFRU9_Retaliation_'+gang+'_Issued','PTFRU9_Retaliation_'+gang+'_Fault'}
        assert any(expected<={v.get('factName') for v in walk(c)} for c in conditions),(ident,'unguarded retaliation writer entry')
    assert 'this.Own(gangID,"Issued")==1' in runtime
    assert 'this.Own("Retaliation","Issued")==1' in runtime
    assert 'this.Fact("sts_"+gang+"_retaliation")==0' in runtime
    report=dict(status='PASS_SPECIAL_U9_PEER_INTEGRATION_NOT_ENGINE_PROOF',manifest_sha256=sha(OUT/'manifest.json'),native_manifest_sha256=sha(NATIVE/'manifest.json'),test_sha256=sha(__file__),
        consumers=rows,shared_gate_single_owner=True,initial_permit_not_waiting_on_ready=True,ep1_poi_namespace_correct=True,spy_cleanup_shared_native_instance=True,spy_interim_output_not_terminal=True,spy_cleanup_ack_not_invented=True,
        retaliation=retaliation,matching_gang_required_in_writer_entry=len(writers))
    (OUT/'integration_tests.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))

if __name__=='__main__':main()
