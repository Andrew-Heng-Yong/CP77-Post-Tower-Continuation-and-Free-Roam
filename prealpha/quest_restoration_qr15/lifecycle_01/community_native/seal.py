"""Seal concrete native conclusions and schema, preserving earlier captures."""
from pathlib import Path
import hashlib, json, struct
from capture import HERE, WORKSPACE, Image, capture

def main():
    # Run01 preserves a mistaken hand-counted string offset(50 vs51).
    # Corrected run02 is fresh and leaves the failing control intact.
    out = HERE / 'verification_02.json'
    extra_out = HERE / 'supplement_02.json'
    schema_out = HERE / 'schema_02.json'
    assert not any(p.exists() for p in (out, extra_out, schema_out))
    im = Image()
    extra_functions = {
        'signed_vlq_read': 0x27B824,
        'name_read_ascii_buffer': 0xB9E5A8,
        'name_read_unicode_branch': 0x2534246,
        'system_prepare_save': 0x2BD3C30,
        'spawner_prepare_save': 0x2BD3CDC,
        'spawner_to_saved_row': 0x2BCED84,
    }
    extra = {'exe_sha256': im.sha, 'game_calls': 0, 'save_writes': 0,
             'functions': {k: capture(im, v) for k, v in extra_functions.items()}}
    extra_out.write_text(json.dumps(extra, indent=2) + '\n', encoding='utf-8')
    checks = []
    def check(name, condition, evidence):
        checks.append({'name': name, 'pass': bool(condition), 'evidence': evidence})
    def raw(at, hx):
        expected = bytes.fromhex(hx)
        return im.data[im.off(at):im.off(at)+len(expected)] == expected
    def slot(v, o, a):
        return struct.unpack_from('<Q', im.data, im.off(v+o))[0] == im.base + a
    check('RTTI_ConstructCls_is_not_instance_table', slot(0x32DEB60, 0xD8, 0xC2DC74), 'metadata32DEB60+D8→C2DC74')
    for offset, rva in {0x260:0x38360C, 0x258:0x36E160, 0x1D8:0x36E344,
                        0x1E0:0x36E388, 0x1E8:0x2BCD5F8, 0x2C8:0x3840D4,
                        0x2E0:0x3842C8, 0x2E8:0xEE7044,
                        0x130:0x2BD3C30, 0x138:0x2BD3A48, 0x148:0xA5C5BC}.items():
        check('instance_slot_'+hex(offset), slot(0x30D3A18, offset, rva), hex(rva))
    check('ctor_ID_field_08', raw(0x384480, '48895108'), 'typed0xC0allocation→ctor384470')
    check('ctor_flags_field_10', raw(0x38449B, '6644897910'), 'clearword+10; not+08')
    check('ctor_returns_allocation_base', raw(0x3845D9, '498bc6'), 'R14=originalRCX; RAX=R14')
    check('shared_pair_keeps_pointer', raw(0x1F554A, '488911'), 'pair[0]=allocationbase')
    check('weak_getter_keeps_registry_pointer', raw(0x3836E0, '488b08') and raw(0x3836FE, '48890f'), 'registryvalue[0]→output[0]')
    check('weak_move_no_this_adjuster', raw(0x26117FC, '488b024c8b014889014c8902'), 'swaprawqwords only')
    guard = '4883ec2880791100741080791000750a488b01c6411001ff50384883c428c3'
    check('ordinary_Activate_complete_body', raw(0x9CEFB8, guard), 'initialized+11 AND inactive+10; then set+10,callv38')
    bad_guard = bytes.fromhex(guard).replace(bytes.fromhex('80791000'), bytes.fromhex('80790800'))
    actual_guard = im.data[im.off(0x9CEFB8):im.off(0x9CEFB8)+len(bytes.fromhex(guard))]
    check('mutation_wrong_active_offset_rejected', actual_guard != bad_guard, 'onebyteoffsetmutation+10→+08')
    check('quest_Activate_dispatch_slot', raw(0x36E11E, 'ff90d8010000'), 'enum1→v1D8')
    check('quest_Reactivate_deactivates_first', raw(0x36E10F, 'ff90e0010000'), 'enum3→v1E0 thenv1D8; keepdistinction')
    check('saved_active_from_actual_object', raw(0x2BCEDCD, '8a4110') and raw(0x2BCEDD4, '884246'), 'object+0x10→savedrow+0x46')
    check('count_transfer_is_fixed_U32', raw(0x3EAA6C, '488b0141b80400000048ff6010'), 'r8d=4;streamvirtual10')
    check('name_signed_vlq_first_payload', raw(0x2F60067, '80e23f'), 'firstmagnitude6bits')
    check('name_signed_vlq_sign_bit', raw(0x2F60074, '0c80'), 'negativeflag0x80')
    check('name_signed_vlq_continuation_bit', raw(0x2F6008F, '80c940'), 'firstcontinuation0x40')
    check('name_read_matches_sign_and_payload', raw(0x27B85C, '83e33f') and raw(0x27B85F, '4080e680'), 'independentdecoder+negativeASCIIlength')
    tail = WORKSPACE / 'prealpha/quest_restoration_qr15/lifecycle_01/save_community/capture_01/community_trailing.bin'
    data = tail.read_bytes()
    check('pinned_save_tail', hashlib.sha256(data).hexdigest().upper() == '89AC22512101B43DB36C9578606D9291F859654C1CE7AAC1CC79466C7A2F0469', 'capture_01fixedinput')
    check('actual_save_embeds_raw_name', data[51:59] == b'\x87default', 'fixedschemafirstrecordendsat51; signedlengthASCII')
    schema = {
        'scope': 'NativeCommunitySystem exactEXE; SaveVersion277 includesallversiongates. No save is modified.',
        'count_encoding': 'Fixed little-endian U32; arrays are raw packed entries. No varints for array counts.',
        'component': [
            'U32 outer_count; U64 outer_keys[outer_count] (WKit alreadyconsumedthese)',
            'for outer_count: U32 inner_count; U64 inner_keys[inner_count]; for inner_count: spawner_row then name',
            'U32 spawner_count; U64 spawner_keys[spawner_count]; spawner_row[spawner_count]',
            'U32 nA; for nA: raw8(memory+0x50),raw64(memory+0x10),raw4(memory+0x58),U32n,raw12[n]',
            'U32 nB; for nB: raw8,raw4',
            'U32 nC; for nC: name,raw1',
            'U32 nD; raw16[nD]',
        ],
        'spawner_row': [
            {'field':'array_00','encoding':'U32 count; U64[count]','version_min':0},
            {'field':'raw_42','encoding':'raw2','version_min':0},
            {'field':'active_46','encoding':'raw1','version_min':0,'meaning':'Actualspawneractivebyte+0x10 copiedduringpre-save; notinitialized,graphowner,orcurrentliveness'},
            {'field':'array_10','encoding':'U32 count; U64[count]','version_min':1,'binding':'filteredobjectspawnedEntityIDs+0x88'},
            {'field':'raw_40','encoding':'raw2','version_min':15},
            {'field':'raw_44','encoding':'raw2','version_min':143},
            {'field':'array_20','encoding':'U32 count; U64[count]','version_min':180,'binding':'objectreservedEntityIDs+0x98 plusfilteredIDs'},
            {'field':'array_30','encoding':'U32 count; raw16[count]','version_min':254},
        ],
        'name': {
            'dictionary_branch':'27A7C4 withstream+0x10nonnull transfersU16index; do notuseforrawsavednames',
            'actual_tail_branch':'No-dictionary name: signedVLQlength; negative=ASCIIbytecount, zero=empty, positive=Unicodebranch(requiresUTF16readerproof or failclosed)',
            'signed_vlq':'firstbyte magnitude&0x3F,negativebit0x80,continuationbit0x40; laterbytes magnitude&0x7F,continuationbit0x80; max5bytes',
            'proof':'27A7C4→2444600→2F60040(write);27A7C4→B9E560→27B824(read);actualtailoffset51=87default',
        },
        'raw_scalars':'Preserve rawbits; serializer itself does not establish signedness or meaning for0x40/0x42/0x44.',
        'limits': [
            'No currentexecutingownerproof frompersistedactiveboolean.',
            'A missinglivelookupdoesnotmeanthesavedspawnerhasnorecord.',
            'No blanketcarsimulation/destruction/dooridempotenceclaim.',
            'CurrentinstalledCodewarebinaryrequiresindependentbinding;localstalesource08/09isnotinstalledbugproof.',
        ],
    }
    schema_out.write_text(json.dumps(schema, indent=2)+'\n', encoding='utf-8')
    report = {'status': 'PASS' if all(x['pass'] for x in checks) else 'FAIL', 'checks': checks,
              'pins': {p.name: hashlib.sha256(p.read_bytes()).hexdigest().upper() for p in
                       (HERE/'capture.py', HERE/'capture_01.json', extra_out, schema_out)},
              'game_calls': 0, 'save_writes': 0, 'runtime_writes': 0}
    out.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'status': report['status'], 'checks':len(checks),
                      'failures':[x['name'] for x in checks if not x['pass']], 'path':str(out)}))

if __name__ == '__main__':
    main()
