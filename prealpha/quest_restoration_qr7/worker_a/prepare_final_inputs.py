"""Build an independent expected final-delta map from approved source proposals."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;W=H.parents[2];sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,walk
def run(epoch,approved,manifest,o):
 assert not o.exists();assert o.resolve().is_relative_to(H.resolve());e=read(epoch);a=read(approved);pack=read(manifest);assert e.get('archive_sha256')and pack.get('zip_sha256')and pack.get('zip'),'Final built archive/ZIP manifests are required';assert sha(manifest)==e['package_manifest_sha256'],'Package manifest is not pinned by final epoch';assert 'PREDECESSOR'not in e.get('package_state',''),'Stale predecessor package cannot be verified as final'
 baseline=W/'prealpha/quest_restoration_qr6/source_epoch_00.json';b=read(baseline);expected={}
 n=read(H/'reviews/nitro_serialized_01/manifest.json');expected[r'towercontinued\sidejobs_s29\entries\mq060_nitro.questphase']={'sha256':n['source_sha256'],'proposal_json':n['json'],'approval':'Independent MQ060 source and actual serialized review'}
 c=read(H/'proposal_readback_04/manifest.json');expected[r'towercontinued\native_gigs_u9\sts_pac_cvi_02_entry.questphase']={'sha256':c['raw_sha256'],'proposal_json':c['readback_json'],'approval':'CVI04 independently accepted source-specific listener/idle proposal'}
 ownerplan=W/'prealpha/quest_restoration_qr7/worker_b/experiments/future_owner_04/NOT_FOR_INTEGRATION.json';op=read(ownerplan);markers=read(Path(op['markers']));expected[op['intended_depot']]={'sha256':op['raw_sha256'],'proposal_json':op['json'],'approval':'Frozen Ronald04 independent C review'}
 for p in op['arming_producers']:expected[p['intended_depot']]={'sha256':p['raw_sha256'],'proposal_json':p['json'],'approval':'Frozen Ronald04 future arming producer'}
 for d,sh,j in [(markers['intended_sector_depot'],markers['raw_sha256'],markers['json']),(markers['intended_block_depot'],markers['block_raw_sha256'],markers['block_json'])]:expected[d]={'sha256':sh,'proposal_json':j,'approval':'Frozen Ronald04 two-trigger private world source'}
 old=b['source_resources'];new=e['source_resources'];changed={d for d in old if d in new and old[d]!=new[d]};added=set(new)-set(old);deleted=set(old)-set(new);assert not deleted;assert changed|added==set(expected),(changed,added,set(expected))
 for d,p in expected.items():assert new[d]==p['sha256'],(d,'Final bytes differ from independently approved source proposal')
 declarations=[x for x in walk(a)if 'depot'in x and 'after'in x]
 for d in expected:assert any(x['depot']==d and x['after']==new[d]for x in declarations),(d,'Missing exact final approved-change declaration')
 candidate=Path(e['candidate']);source=candidate/'archive_source';package=candidate/'package';archive=package/'archive/pc/mod/zzzz_PTFR_Combined.archive';assert sha(archive)==e['archive_sha256'];assert sha(Path(pack['zip']))==pack['zip_sha256']
 spy=next(p for p in op['arming_producers']if p['quest_id']=='sts_ep1_08')['source']
 pin={'epoch':str(epoch.resolve()),'epoch_sha256':sha(epoch),'approved':str(approved.resolve()),'approved_sha256':sha(approved),'final_manifest':str(manifest.resolve()),'final_manifest_sha256':sha(manifest),'baseline':str(baseline),'baseline_sha256':sha(baseline),'candidate':str(candidate),'source':str(source),'package':str(package),'archive':str(archive),'archive_sha256':sha(archive),'zip':pack['zip'],'zip_sha256':pack['zip_sha256'],'canonical_resources':new,'expected_proposal_delta':expected,'changed':sorted(changed),'added':sorted(added),'deleted':sorted(deleted),'inherited':b['inherited_repair_resources'],'spy_before_source':spy,'baseline_package':b['package_files'],'registration_plan':str(W/'prealpha/quest_restoration_qr7/worker_b/registration_plan_01.json'),'namespace_review':str(H/'reviews/ronald_namespace_03/evidence.json'),'baseline_XL':str(Path(b['candidate'])/'package/archive/pc/mod/zzzz_PTFR_Combined.archive.xl'),'final_XL':str(package/'archive/pc/mod/zzzz_PTFR_Combined.archive.xl')}
 write(o/'inputs.json',pin);print({'expected_members':len(new),'changed':len(changed),'added':len(added),'inputs':str(o/'inputs.json')})
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--epoch',type=Path,required=True);p.add_argument('--approved',type=Path,required=True);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();run(a.epoch,a.approved,a.manifest,a.output)
