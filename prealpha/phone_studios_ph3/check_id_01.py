from pathlib import Path
import json,binascii
W=Path.cwd();r=json.loads((W/'prealpha/phone_merge_ph2/id_proof_01.json').read_text());d=r'towercontinued\phone_studios_ph3\studio_support.questphase';i=binascii.crc_hqx((d+':1').encode(),65535);print(d,i);assert i not in r['native_ids']+[x['id'] for x in r['inventory']]+[r['new_id']]
