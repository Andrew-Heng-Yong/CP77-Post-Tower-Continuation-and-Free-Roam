"""Pin eight-contract applicability to the coordinator's authoritative checkpoint."""
from pathlib import Path
import argparse
from prepare import ROOT,HERE,read,write,sha

def main(out,explicit_epoch):
    assert not out.exists()
    q7=ROOT/'prealpha/quest_restoration_qr7';cp=q7/'WORKING_CHECKPOINT.json';baseline=read(HERE/'baseline_01/baseline.json')
    for _ in range(4):
        checkpoint=read(cp);epoch_path=explicit_epoch.resolve();epoch_pin=sha(epoch_path);epoch=read(epoch_path);candidate=Path(epoch['candidate'])
        resources=[]
        for old in baseline['source_pins']:
            d=old['depot'];p=candidate/'archive_source'/d.replace('\\','/');h=sha(p)
            assert h==epoch['source_resources'][d]
            if h!=old['sha256']:
                assert d==r'towercontinued\sidejobs_s29\entries\mq060_nitro.questphase' and h=='79FD3A440DFBCE6130AA5E5EA1D71E6E92BEAD27691C0AD0F59EFE7C94214784'
            resources.append({'depot':d,'path':str(p),'effective_sha256':h,'QR6_sha256':old['sha256'],'changed_from_QR6':h!=old['sha256']})
        scripts=[]
        for row in baseline['scripts']:
            p=candidate/'package/r6/scripts/PTFR_Consolidated'/Path(row['path']).name
            assert sha(p)==row['sha256'];scripts.append({'path':str(p),'sha256':row['sha256']})
        if sha(epoch_path)==epoch_pin:break
    else:raise RuntimeError('Canonical epoch changed repeatedly; no mixed-epoch scope report emitted')
    natives=[]
    for row in baseline['current_game_read_only_inputs']:
        assert sha(row['path'])==row['sha256'];natives.append(row)
    assert sum(x['changed_from_QR6'] for x in resources)==1
    units=[
      ('eight_contract_dispositions',HERE/'results_01/contract_updates.json','Eight assigned rows; three Nitro authority gaps repaired prospectively, five residual UNKNOWNs.'),
      ('eight_contract_peer',q7/'worker_a/reviews/unknowns_final_01/review.json','Independent A84 assertions plus actual native Cuckoo endpoint mutation; unchanged bounded dispositions approved.'),
      ('nitro_authority',HERE/'nitro_authority_03/evidence.json','Positive current registered game-root proof and private source proposal;109 assertion events/80 fixtures.'),
      ('nitro_current_donors',HERE/'nitro_current_providers_01/gate.json','Four native donor hashes equal unique current providers across134 archive indexes.'),
      ('career_native_journal',HERE/'journal_proof_02/result.json','Exact current native equality guard and actual graph dispatch;23 checks/two controls.'),
      ('career_native_peer',q7/'worker_a/reviews/career_journal_01/review.json','Independent native-bytecode/trackQuest0 peer; old saved-owner limit retained.'),
      ('remaining_unknown_properties',HERE/'remaining_01/result.json','Cuckoo/Voodoo exact evidence;88 assertions with named unresolved inputs/engine behavior.'),
      ('remaining_raw_mutants',HERE/'remaining_controls_01/result.json','Four actual raw-resource and one actual native-field byte mutation rejected; no gameplay fixtures.'),
      ('ronald_source_peer',HERE/'reviews/ronald_01/verification_02/review.json','Independent owner04 source/serialized/packed review:306 assertions/64 case fixtures/four controls.'),
      ('ronald_contact_metadata',HERE/'reviews/ronald_01/verification_02/native_contact_and_metadata_pins.json','Current generic Contact Active native predicate and explicit preserved sourcePrefabHash boundary.'),
      ('reproduction_commands',HERE/'REPRODUCE.md','Exact reusable fresh-output commands, expected bounded outputs and one-shot capture limits.'),
    ]
    write(out/'applicability.json',{'status':'PASS_EIGHT_CONTRACT_TARGETED_APPLICABILITY','checkpoint':str(cp),'authority':'Explicit canonical epoch assigned by coordinator; checkpoint may lag','canonical_epoch':str(epoch_path),'canonical_epoch_sha256':epoch_pin,
        'effective_source_epoch':epoch['epoch_key'],'candidate':str(candidate),'targeted_resources':resources,'managed_script_pins':scripts,'unchanged_native_inputs':natives,
        'contracts':8,'changed_targeted_resources':1,'limits':['Only these25 target resources and three supporting scripts are rehashed here; whole successor/package checks belong to the coordinator.',
        'Installed PH3 is separate and was never changed by Worker C.','This does not promote the five UNKNOWNs or certify live behavior.']})
    write(out/'evidence_inventory.json',{'status':'REUSABLE_TARGETED_EVIDENCE_INDEX','units':[{'id':i,'path':str(p),'sha256':sha(p),'scope':s} for i,p,s in units],
        'scripts':[{'path':str(p),'sha256':sha(p)} for p in sorted(HERE.glob('*.py'))],
        'applicability':str(out/'applicability.json'),'applicability_sha256':sha(out/'applicability.json'),
        'counting_rule':'Do not sum overlapping assertion, fixture, source-capture or review counts into quest coverage. Only the eight named contract rows are updated.',
        'runtime_changes_by_worker_c':[],'code_sha256':sha(__file__)})
    print({'effective_epoch':epoch['epoch_key'],'target_resources':len(resources),'evidence_units':len(units),'out':str(out)})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--epoch',type=Path,required=True);a=p.parse_args();main(a.output,a.epoch)
