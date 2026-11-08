"""Offline receipt calculation from an externally observed real parent quest index.

Does not access a game process or save. Never assume an index for an actual save.
"""
import argparse,json,struct,binascii
OWNER=r'towercontinued\quest_restoration_qr7\ronald_news_future.questphase'
def fnv32(data):
 n=0x811c9dc5
 for b in data:n=((n^b)*0x1000193)&0xffffffff
 return n
def receipt(index):
 if not 0<=index<=65535:raise ValueError('Observed quest index must fit native uint16')
 node=binascii.crc_hqx((OWNER+':1').encode(),65535)
 phasehash=fnv32(struct.pack('<H',index))
 key=(phasehash<<32)+node
 return {'externally_observed_parent_quest_index':index,'parent_depot':r'ep1\quest\ep1.quest','generated_phase_id':node,'root_path_hash':phasehash,'packed_QuestNodeKey_hex':f'{key:016X}','receipt_FactID':fnv32(struct.pack('<Q',key)),'fact_store':1,'classification':'DERIVED_IDENTIFIER_ONLY_NOT_AN_OBSERVED_FACT_OR_SAVE_STATE'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--observed-quest-index',type=int,required=True);a=p.parse_args();print(json.dumps(receipt(a.observed_quest_index),indent=2))
