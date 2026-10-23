"""New selection/dispatcher artefacts. Not a claim of new native gig adapters."""
import json
from catalog_gig_batch_b4 import ROOT,OUT
from catalog_gig_rollout_r2 import read,sha

def main():
    assert not (OUT/'install_receipt.json').exists(),'Installed evidence pinned'
    review=read(OUT/'source_review.json');rows=[]
    for job in review['jobs']:
        row={'id':job['id'],'title':job['selected_title'],'path':job['journal_path'],
             'legacy_history':job['legacy_history'],'terminal_facts':job.get('terminal_markers',[]),'source_disposition':job['disposition']}
        if job['current_adapter']:row['adapter_mode']='resume'
        rows.append(row)
    target=ROOT/'diagnostics/PTFR_GigBatchB4/catalogue.json';target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps({'schema':1,'fingerprint':'PTFR_B4_CAST72_R1','count':72,'runtime_adapter_count':3,'jobs':rows},indent=2)+'\n',encoding='utf-8')
    assert len(rows)==72 and sum(bool(j.get('adapter_mode')) for j in rows)==3
    result={'status':'B4_BATCH_DISPATCHER_PREPARED_NOT_ALL_GIG_RESTORATION','source_review_sha256':sha(OUT/'source_review.json'),
            'catalogue_sha256':sha(target),'selected':72,'native_gig_adapters':3,'new_native_adapters':0,
            'pending_native_gig_adapters':69,'completed_replay_adapters':0,'game_writes':0,'direct_save_writes':0}
    (OUT/'manifest.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
