"""Seal the derived narrow resource-array decoding contract without reading saves."""
import json,struct,hashlib
from pathlib import Path
from inspect_lock import Image,HERE

def main():
    out=HERE/'resource_array_schema_01.json';assert not out.exists()
    im=Image()
    cases=[('quest_system',0x73929c,0x7392bc),('prior_child',0x7384a0,0x7384c0),('next_child',0x1921b08,0x1921b28)]
    names={}
    for label,begin,lea in cases:
        f=im.disasm(begin);r=next(r for r in f['instructions'] if int(r['rva'],16)==lea)
        b=bytes.fromhex(r['bytes']);dest=lea+len(b)+struct.unpack('<i',b[-4:])[0]
        off=im.off(dest);end=im.data.index(0,off)
        name=im.data[off:end].decode('ascii')
        names[label]={'name':name,'name_literal_rva':hex(dest),'name_getter_rva':hex(begin)}
    result={'exe_sha256':im.sha,'result':'SOURCE_CONFIRMED_SERIALIZATION_SCHEMA_NO_SAVE_READ',
       'native_names':names,
       'runtime_array':'QuestsSystem+0xA8; QuestContext+0x18 points at this array',
       'native_load_version_gate':{'version_query_virtual_offset':'0x48','minimum':139,'branch':'RVA0x739619 cmp eax,0x8B; lower versions use old child format; actual fixture version must be pinned'},
       'placement':'Untagged parent bytes immediately after FactsDB child is closed and before QuestNodeHash child is opened; derive exact span from verified parsed/decompressed node offsets, not string search',
       'encoding':{'count':'signedVLQ; reject negative/overflow/unbounded count',
           'first_byte':{'magnitude_mask':63,'continuation_mask':64,'sign_mask':128},
           'subsequent_bytes':{'magnitude_mask':127,'continuation_mask':128,'magnitude_shifts':[6,13,20,27]},
           'elements':'count consecutive little-endian UInt64 canonical ResourcePath hashes; no per-element length or marker'},
       'root_index_use':'RVA0x1266558 searches this saved array for the quest resource path and returns its zero-based ordinal; RootPhase ExecutePath0xBEA3D0 indexes Children by path[0]',
       'requirements':['Same one pinned save body hash before/after extraction','Actual decompressed offsets plus absolute parent/FactsDB end/next-child bounds','Actual native stream/save version >=0x8B','Bounded canonical VLQ decoding and exact consumed-byte readback','Array hash comparison to exact provider-pinned .quest resource depots','Do not infer missing path/owner from a candidate-key miss','No root ordinal guessed from gamedef order'],
       'not_established':['Exact saved ordinal without extracting the target body','Native pending/handler liveness from this array','External world lease retirement','Safety of a manual live inspector during lifecycle transitions'],
       'save_reads':0,'game_api_calls':0,'runtime_changes':0}
    # Put the resolved name into the placement text, avoiding an assumed marker label.
    result['placement']=result['placement'].replace('QuestNodeHash',names['next_child']['name'])
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(result)

if __name__=='__main__':main()
