"""Independent algebra checks of instruction-derived CRC/receipt identities."""
from inspect_archivexl import HERE
from receipt_key import receipt,fnv32
import binascii,json,hashlib

def native_crc(data):
 c=65535
 for b in data:
  x=(c>>8)^b;x^=x>>4
  c=(((c^(x<<4))<<3)^x)&65535
  c=((c<<5)^x)&65535
 return c
def main():
 out=HERE/'identifier_algebra_01';out.mkdir(exist_ok=False)
 records=json.loads((HERE/'namespace_verification_01/registration_inventory.json').read_text())
 rows=[r for r in records if r'ep1\quest\ep1.quest' in r['expanded_parents']]
 keys=sorted({r['path']+':1' for r in rows});checks=[]
 for k in keys:
  assert native_crc(k.encode())==binascii.crc_hqx(k.encode(),65535)
 checks.append({'name':'instruction-derived optimized CRC equals independent binascii polynomial result on every observed target-root key','keys':len(keys),'pass':True})
 prefixes=[fnv32(i.to_bytes(2,'little')) for i in range(65536)]
 assert len(set(prefixes))==65536
 checks.append({'name':'all65536 uint16 node-ID prefixes have unique FNV1a32 hashes','pass':True,'algebra':'Receipt uint64 packs nodeID in low32 and rootPathHash in high32. After unique first2bytes, the common remaining6bytes are a composition of XOR and multiplication by odd0x01000193, each invertible modulo2^32. Thus same-parent distinctuint16IDs cannot collide for any actual rootPathHash.'})
 for i in [0,1,255,256,65535]:
  r=receipt(i);assert r['generated_phase_id']==19913 and r['receipt_FactID']==fnv32(bytes.fromhex(r['packed_QuestNodeKey_hex'])[::-1])
 checks.append({'name':'offline calculator agrees with explicit packed little-endian identifier encoding at five boundary indices','pass':True,'not_save_evidence':True})
 for i in [-1,65536]:
  try:receipt(i)
  except ValueError:pass
  else:raise AssertionError('invalid index accepted')
 checks.append({'name':'offline calculator rejects index outside actual uint16 ABI','pass':True})
 result={'status':'PASS_BOUNDED_IDENTIFIER_ALGEBRA','checks':checks,'keys':len(keys),'actual_saved_quest_index_observed':False,'limits':['No real receipt value or save serialization was observed.','Distinctparent root-path hashes share the global32-bit fact hash namespace; this proof covers same-parent nodeIDs only and is not a full native named-fact census.'],'checker_sha256':hashlib.sha256(__import__('pathlib').Path(__file__).read_bytes()).hexdigest().upper()}
 (out/'result.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
