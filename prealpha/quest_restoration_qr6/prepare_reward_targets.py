"""Four new exact native reward definitions, not a repeat of QR5 bulk capture."""
from pathlib import Path
import sys
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,walk,value
from model import Resource
dest=O/'shared/reward_targets_01/targets.json';assert not dest.exists()
rows=read(O/'groups/B02/raw_exports_01/manifest.json');by={r['depot']:r for r in rows if r.get('status')=='EXPORTED'}
spec=[('mws_wat_08_trauma_drama',r'base\open_world\mini_world_stories\watson\mws_wat_08\mws_wat_08.questphase','64','145696460765'),('mws_se5_07',r'base\open_world\mini_world_stories\badlands\se5\mws_se5_07\mws_se5_07.questphase','108','146854820111'),('mq003_orbitals',r'base\quest\minor_quests\mq003\phases\mq003_homeless.questphase','130','150894402697'),('mq003_orbitals',r'base\quest\minor_quests\mq003\phases\mq003_orbital_pod.questphase','66','155544231233')]
uses=[]
for qid,d,i,tid in spec:
 r=by[d];assert sha(r['raw'])==r['raw_sha256']and sha(r['json'])==r['json_sha256'];m=Resource(read(r['json'])).normalize();n=m['graphs']['root']['nodes'][i]
 assert n['reward']and any(str(value(x))==tid for x in walk(n['payload'])if x.get('$type')=='TweakDBID'),(d,i,tid)
 uses.append({'quest_id':qid,'depot':d,'graph':'root','node':i,'record':tid,'payload':n['payload'],'raw':r['raw'],'raw_sha256':r['raw_sha256'],'json':r['json'],'json_sha256':r['json_sha256'],'applicability':'Exact native occurrence; current private body identity and actual entry/outcome route must be bound by B02 findings/peer review. Definition presence alone is not reward execution.'})
write(dest,{'targets':sorted({x['record']for x in uses}),'uses':uses,'scope':'Four newly requested direct reward IDs absent QR5stock1200capture. Stock separate definitions and bounded descendants only, no live merged winner/amount/receipt claim.'})
s=(W/'prealpha/quest_restoration_qr5/read_vehicle_record_02.ps1').read_text(encoding='utf-8-sig').replace("'shared/tdb_vehicle_target_02/targets.json'","'shared/reward_targets_01/targets.json'").replace('QR5FlatHash','QR6FlatHash')
out=O/'read_reward_records.ps1';assert not out.exists();out.write_text(s,encoding='utf-8')
print({'targets':len(uses),'source_nodes_verified':len(uses)})
