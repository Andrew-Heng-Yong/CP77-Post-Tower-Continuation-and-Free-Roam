"""Compose fresh candidate; preserve the compiled script-only candidate unchanged."""
import argparse
import binascii
import re
import shutil
import sqlite3
from common import HERE, REGISTRY, baseline, plain, read, sha, write

DEPOT = r'towercontinued\resume_rd1\mq007_delivery_boot.questphase'
XL = 'archive/pc/mod/zzzz_PTFR_Combined.archive.xl'
ARCHIVE = 'archive/pc/mod/zzzz_PTFR_Combined.archive'


def crc(data):
    value=65535
    for byte in data:
        value^=byte<<8
        for _ in range(8):
            value=((value<<1)^0x1021 if value&32768 else value<<1)&65535
    return value


def registrations(text, source):
    # Deliberately bounded parser: unknown quest YAML shape is a hard failure.
    text=text.replace('\r\n','\n')
    sections=re.findall(r'(?ms)^quest:\s*\n(.*?)(?=^\S|\Z)',text)
    if not sections:return []
    assert len(sections)==1,source
    section=sections[0]
    assert re.match(r'^  phases:\s*\n',section),source
    blocks=re.split(r'(?m)^    - path: *',section)[1:]
    assert blocks and section.count('- path:')==len(blocks),source
    result=[]
    for block in blocks:
        path=block.splitlines()[0].strip()
        parent_match=re.search(r'^      parent: (.+)$',block,re.M)
        assert parent_match,('missing parent',source,path)
        if parent_match[1].strip()!=r'ep1\quest\ep1.quest':
            result.append({'path':path,'parent':parent_match[1].strip(),'source':source,
                'binding':block,'generated_id':None,'scope':'Different parent; no ID comparison with the new EP1-root injection.'})
            continue
        pattern=r'([^\n]+)\n      parent: ([^\n]+)\n      input:\n        node: \[([^\]]+)\]\n        socket: ([^\n]+)\s*'
        match=re.fullmatch(pattern,block)
        assert match,('unsupported quest binding',source,block[:250])
        parent=match[2].strip();nodes=[int(x.strip()) for x in match[3].split(',')]
        # Formula is qualified only for root/[1] injection.
        assert nodes==[1],('unreviewed input identity formula',source,path,nodes)
        key=(path+':1').encode();generated=crc(key)
        assert generated==binascii.crc_hqx(key,65535)
        result.append({'path':path,'parent':parent,'node':nodes,'socket':match[4].strip(),
                       'generated_id':generated,'source':source})
    return result


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);args=parser.parse_args()
    out=HERE/args.out;assert out.parent==HERE and not out.exists()
    manifest,game=baseline()
    scripts=HERE/'candidate_02';compiled=read(HERE/'compile_02/result.json');assert compiled['status']=='PASS'
    native=HERE/'archive_04';packed=read(native/'readback.json')
    assert sha(native/'zzzz_PTFR_Combined.archive')==packed['archive_sha256']
    before=(scripts/'package'/XL).read_bytes();newline=b'\r\n' if b'\r\n' in before else b'\n'
    entry=('    - path: '+DEPOT+'\n      parent: ep1\\quest\\ep1.quest\n      input:\n        node: [1]\n        socket: Out\n').encode().replace(b'\n',newline)
    marker=b'streaming:';assert before.count(marker)==1 and DEPOT.encode() not in before
    after=before.replace(marker,entry+marker,1)
    regs=[];xl_pins=[]
    for directory in (game/'archive',game/'mods'):
        if not directory.exists():continue
        plain(directory)
        for path in sorted(directory.rglob('*.xl')):
            plain(path);data=after if path==game/XL else path.read_bytes()
            xl_pins.append({'path':str(path),'sha256':sha(path)})
            regs+=registrations(data.decode('utf-8-sig'),str(path))
    parent=r'ep1\quest\ep1.quest'
    relevant=[r for r in regs if r['parent']==parent]
    ids=[r['generated_id'] for r in relevant]
    assert len(ids)==len(set(ids)),('generated ID collision',[(i,ids.count(i)) for i in set(ids) if ids.count(i)>1])
    conn=sqlite3.connect(REGISTRY.as_uri()+'?mode=ro',uri=True);conn.row_factory=sqlite3.Row
    root_ids={r[0] for r in conn.execute('select id from nodes where rid=13718 and graph=?',('root',))}
    assert not root_ids.intersection(ids)
    assert len([r for r in regs if r['path']==DEPOT])==1
    out.mkdir();package=out/'package';shutil.copytree(scripts/'package',package)
    shutil.copyfile(native/'zzzz_PTFR_Combined.archive',package/ARCHIVE)
    (package/XL).write_bytes(after)
    for rel,pin in read(scripts/'script_manifest.json')['changed_sources'].items():assert sha(package/rel)==pin
    files=[]
    for row in manifest['core_files']:
        path=package/row['path'];files.append({'path':row['path'],'bytes':path.stat().st_size,'sha256':sha(path),'unchanged':sha(path)==row['sha256']})
    assert len(files)==51 and sum(not r['unchanged'] for r in files)==5
    assert len([p for p in package.rglob('*') if p.is_file()])==51
    pins=[]
    for rid in (13718,14910,15166):
        row=dict(conn.execute('select * from resources where rid=?',(rid,)).fetchone())
        assert sha(row['export_path'])==row['export_sha256']
        pins.append({k:row[k] for k in ('rid','depot','key','archive','sha256','export_path','export_sha256')})
    write(out/'additional_sources.json',pins)
    write(out/'registration_inventory.json',{'status':'PASS_ID_INVENTORY_NATIVE_PROVIDER_CHECK_PENDING','registrations':regs,'xl_inputs':xl_pins,
        'new_id':next(r['generated_id'] for r in regs if r['path']==DEPOT),'native_root_ids':sorted(root_ids),'previous_xl_retained_byte_for_byte':after.replace(entry,b'')==before})
    write(out/'manifest.json',{'status':'COMPOSED_QUALIFICATION_PENDING','baseline_manifest':str(manifest.get('manifest','HS4')),
        'archive_source':str(native/'archive_source'),'core_files':files,'required_files':manifest['required_files'],
        'compile_result':'../compile_02/result.json','native_readback':'../archive_04/readback.json','installed':False})
    print(f'Composed {out.name}: 51 paths, five changed; new phase ID '+str(next(r['generated_id'] for r in regs if r['path']==DEPOT)))


if __name__=='__main__':main()
