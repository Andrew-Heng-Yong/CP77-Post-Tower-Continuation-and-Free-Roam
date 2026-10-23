"""Successor admission contract adds exact per-gig Quest-item contradictions."""
import copy,json,sys,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools'))
from catalog_gig_rollout_r2 import read,sha,walk
HERE=ROOT/'research/gigs_u10/native'
ITEMS={
 'sts_hey_gle_03':[('Items.sts_hey_gle_03_guitar',119514713847)],
 'sts_hey_gle_05':[('Items.sts_hey_gle_05_scandium_cores',151969226370)],
 'sts_wat_nid_07':[('Items.sts_wat_nid_07_recording',131344880361)],
 'sts_wbr_hil_06':[('Items.sts_wbr_hil_06_bootleg',122115122821),('Items.sts_wbr_hil_06_keys',110626352110)],
 'sts_wbr_jpn_12':[('Items.sts_wbr_jpn_12_corpo_cracker',146850840587)]}

def main():
    target=HERE/'contracts_02.json';assert not target.exists()
    old=read(HERE/'contracts_01.json');doc=copy.deepcopy(old);plan=read(HERE/'build_plan_01.json');witness=[]
    dbpath='research/gigs_u10/presentation/item_records_01.json';db=read(ROOT/dbpath)
    for owner in doc['owners']:
        owner['inventory_zero']=[];owner['inventory_native']=[]
        job=next(j for j in plan['jobs'] if j['id']==owner['id'])
        for record,hashvalue in ITEMS.get(owner['id'],[]):
            assert (zlib.crc32(record.encode())|(len(record)<<32))==hashvalue
            dbrow=next(r for r in db['records'] if r['hash']==hashvalue)
            assert dbrow['type']=='gamedataItem_Record'
            matches=[]
            for resource in job['resources']:
                for graph in resource['graphs']:
                    for node in graph['nodes']:
                        for obj in walk(node):
                            if obj.get('$type')=='questInventory_ConditionType' and obj.get('itemID',{}).get('hash')==hashvalue:
                                assert obj['isPlayer']==1 and obj['quantity']==1
                                matches.append(dict(raw=resource['raw'],embedded_index=resource['binding']['embedded_index'],graph=graph['path'],node=node['id'],source_condition=node['condition']))
            assert matches,(record,'no exact authored inventory witness')
            spec=dict(record=record,hash=str(hashvalue),**matches[0]);owner['inventory_zero'].append(dict(record=record,hash=str(hashvalue)));owner['inventory_native'].append(spec)
            witness.append(dict(id=owner['id'],record=record,hash=str(hashvalue),native_matches=matches,action='Read-only player quantity must be exactly zero; nonzero/unknown defers, no item removal or reward replay.'))
    doc['source_pins']={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in [HERE/'contracts_01.json',HERE/'build_plan_01.json',ROOT/dbpath,Path(__file__)]}
    target.write_text(json.dumps(doc,indent=2)+'\n',encoding='utf-8')
    (HERE/'inventory_guard_02.json').write_text(json.dumps(dict(status='SOURCE_BOUND_UNIQUE_ITEM_FRESHNESS_GUARDS',contract=str(target.relative_to(ROOT)).replace('\\','/'),contract_sha256=sha(target),witnesses=witness,changed_existing_fields=False,game_writes=0),indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(owners=len(doc['owners']),quest_items=len(witness),contract_sha256=sha(target))))

if __name__=='__main__':main()
