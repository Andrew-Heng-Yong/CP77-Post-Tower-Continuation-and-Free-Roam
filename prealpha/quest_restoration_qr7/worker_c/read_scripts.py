"""Read-only analysis representation for the old decompiler's fixed 104-byte reader.

The derived file is never an engine/compiler/runtime input. Original definition
payloads and string pools remain byte-identical; only descriptor/payload offsets
are relocated after removing the extra header descriptor. The seventh table is
retained as uninterpreted bytes. This does not establish safe cache writing.
"""
from pathlib import Path
import sys, struct, zlib, subprocess
from prepare import ROOT,HERE,sha,write
sys.path.insert(0,str(ROOT/'research/redscript_2_5/binary_reader_01'))
import diagnose_01 as diag

def main():
    out=HERE/'native_scripts_02'
    assert not out.exists()
    out.mkdir()
    cache=diag.CURRENT
    original=sha(cache)
    b,info,pools,defs=diag.parse(cache)
    assert original=='B78043064AE90FB80861B0D885D1C8DBCD22070F1DB71F20664D19F2D83C4AAC'
    assert info['tables']['string_data']['offset']==116
    tool=ROOT/'research/finalboards_dismissal/tooling/redscript-cli.exe'
    first=subprocess.run([str(tool),'decompile','-i',str(cache),'-o',str(out/'direct.script')],capture_output=True,text=True)
    write(out/'direct_attempt.json',{'command':first.args,'returncode':first.returncode,'stdout':first.stdout,'stderr':first.stderr,
        'tool_sha256':sha(tool),'input_sha256':original})
    derived=bytearray(b[:104]+b[116:])
    for i in range(6):
        oldoffset,count,crc=struct.unpack_from('<III',b,32+12*i)
        struct.pack_into('<I',derived,32+12*i,oldoffset-12)
    table=info['tables']['definitions']
    for d in defs:
        if d['offset']:
            struct.pack_into('<I',derived,table['offset']-12+20*d['index']+8,d['offset']-12)
    dtab=bytes(derived[table['offset']-12:table['end']-12])
    struct.pack_into('<I',derived,32+4*12+8,zlib.crc32(dtab))
    header=bytearray(derived[:104]);struct.pack_into('<I',header,24,0xDEADBEEF)
    struct.pack_into('<I',derived,24,zlib.crc32(header))
    analysis=out/'fixed_reader_analysis_only.redscripts'
    analysis.write_bytes(derived)
    db,di,dp,dd=diag.parse(analysis)
    assert pools==dp
    assert len(defs)==len(dd)
    same=0
    for d,d2 in zip(defs,dd):
        assert (d['index'],d['parent'],d['type'],d['name'],d['size'])==(d2['index'],d2['parent'],d2['type'],d2['name'],d2['size'])
        assert b[d['offset']:d['offset']+d['size']]==db[d2['offset']:d2['offset']+d2['size']]
        same+=1
    seventh_offset,seventh_count,seventh_crc=struct.unpack_from('<III',b,104)
    assert b[seventh_offset:seventh_offset+12*seventh_count]==db[seventh_offset-12:seventh_offset-12+12*seventh_count]
    result=subprocess.run([str(tool),'decompile','-i',str(analysis),'-o',str(out/'all.script')],capture_output=True,text=True)
    assert sha(cache)==original
    write(out/'result.json',{'status':'ANALYSIS_ONLY_FIXED_READER_DERIVATION','input':str(cache),'input_sha256':original,
        'tool':str(tool),'tool_sha256':sha(tool),'analysis_input':str(analysis),'analysis_sha256':sha(analysis),
        'definition_payloads_byte_equal':same,'all_known_string_pools_equal':True,'uninterpreted_seventh_table_bytes_preserved':True,
        'definitions':defs,'decompile_command':result.args,'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr,
        'output_sha256':sha(out/'all.script') if (out/'all.script').exists() else None,
        'input_unchanged':True,'runtime_writes':0,'limitations':['Read-only analysis of existing bytecode, never an engine-valid cache claim.',
        'Unknown seventh-table semantics not interpreted. Native function declarations carry no implementation.',
        'Decompiled code is a representation; particular properties require exact bytecode or original graph validation.']})
    print({'definitions':same,'decompile_returncode':result.returncode,'out':str(out)})

if __name__=='__main__': main()
