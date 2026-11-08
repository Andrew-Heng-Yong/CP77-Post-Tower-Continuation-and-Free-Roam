"""Link already captured stock targets; no duplicate database probe."""
from pathlib import Path
import sys,zlib
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
p=O/'shared/tdb_records_01/records.json';r=read(p);by={x['id']:(i,x)for i,x in enumerate(r['records'])}
rows=[]
for name in ['Items.money','QuestRewards.sts_ep1_06_money_reward_micheal_maldonaldo']:
 ident=str((len(name.encode())<<32)|zlib.crc32(name.encode()));i,record=by[ident]
 rows.append({'alias':name,'id':ident,'capture_index':i,'exists':record['exists'],'database_definitions':record['database_definitions'],'record_references':record['record_references']})
out=O/'shared/G16_target_links_01.json';assert not out.exists()
write(out,{'status':'EXISTING_STOCK_CAPTURE_TARGET_LINKS_REQUIRES_NATIVE_ROUTE_APPLICABILITY','records':rows,'capture':str(p),'capture_sha256':sha(p),'Rinder_existing_applicability':str(O/'shared/tdb_applicability_02/wst_ep1_04.json'),'limits':r['limits']})
print({'linked_targets':len(rows),'fresh_database_probes':0})
