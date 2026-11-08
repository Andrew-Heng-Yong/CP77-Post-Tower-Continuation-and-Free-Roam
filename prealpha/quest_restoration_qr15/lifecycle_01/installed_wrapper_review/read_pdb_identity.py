"""Read two existing PDB MSF directories and identity stream only; no symbol downloads."""
from pathlib import Path
import hashlib, json, math, struct, sys, uuid
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from inspect_installed import Image, WORKSPACE, DLL
out=HERE/'pdb_identity_01.json'
assert not out.exists()
im=Image(); codeview=im.codeview()
rows=[]
for name in ('Codeware.pdb','compile.Codeware.pdb'):
    path=WORKSPACE/'build/windows/x64/release'/name
    data=path.read_bytes()
    assert data[:32]==b'Microsoft C/C++ MSF 7.00\r\n\x1aDS\0\0\0'
    page, free, total, length, unknown, root=struct.unpack_from('<IIIIII',data,32)
    assert 512<=page<=65536 and page&(page-1)==0 and total*page<=len(data)
    n=(length+page-1)//page
    assert n*4<=page and length<=16*1024*1024
    pages=struct.unpack_from('<'+'I'*n,data,root*page)
    directory=b''.join(data[p*page:(p+1)*page] for p in pages)[:length]
    stream_count=struct.unpack_from('<I',directory)[0]
    assert 1<stream_count<100000
    sizes=struct.unpack_from('<'+'I'*stream_count,directory,4)
    at=4+4*stream_count; streams=[]
    for size in sizes:
        count=0 if size==0xFFFFFFFF else (size+page-1)//page
        blocks=struct.unpack_from('<'+'I'*count,directory,at) if count else ()
        at+=4*count
        streams.append((size,blocks))
    size,blocks=streams[1]
    identity=b''.join(data[p*page:(p+1)*page] for p in blocks)[:size]
    version,signature,age=struct.unpack_from('<III',identity)
    guid=str(uuid.UUID(bytes_le=identity[12:28])).upper()
    rows.append({'path':str(path),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest().upper(),
        'MSF7':True,'block_bytes':page,'stream_count':stream_count,'identity_stream':1,
        'pdb_version':version,'signature':hex(signature),'age':age,'guid':guid,
        'matches_installed_codeview':any(guid==c['guid'] and age==c['age'] for c in codeview)})
baseline=WORKSPACE/'prealpha/quest_restoration_qr15/baseline.json'
base=json.loads(baseline.read_text(encoding='utf-8-sig'))
installed=base['installed']
pin=next(r for r in installed if Path(r['path'])==DLL)
assert pin['sha256']==im.sha
result={'dll_path':str(DLL),'dll_sha256':im.sha,'codeview':codeview,'local_pdb_identities':rows,
    'baseline':{'path':str(baseline),'sha256':hashlib.sha256(baseline.read_bytes()).hexdigest().upper(),
                'installed_pin_count':len(installed),'matched_dll_pin':pin},
    'search_scope':'Existing workspace recursive filename search for *Codeware*.pdb and *codeware*.pdb returned only these two root build files. Embedded D: CodeView path absent. No download/search outside workspace.',
    'runtime_changes':0,'game_api_calls':0,'save_reads':0}
out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
