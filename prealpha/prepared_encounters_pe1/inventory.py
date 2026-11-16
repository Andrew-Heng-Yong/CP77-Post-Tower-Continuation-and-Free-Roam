"""Inventory every installed phase and script admission table for PE1 review."""
from pathlib import Path
from collections import defaultdict
import hashlib
import json
import re

HERE=Path(__file__).resolve().parent
WS=HERE.parents[1]
BASE=WS/'prealpha/kold_mirage_km1/candidate_01'
INSTALLED=WS/'prealpha/kold_mirage_km1/deployment_01/installed_manifest_01.json'
CACHE=WS/'diagnostics/vanilla_parity_20261029_01/analysis_02/model_inventory.json'


def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def sha(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest().upper()


def write(p,v):
    with Path(p).open('x',encoding='utf-8',newline='\n') as f:
        json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')


def function_bodies(text):
    """Read REDscript function bodies while respecting quoted strings/comments."""
    out={}
    for m in re.finditer(r'\bfunc\s+(\w+)\s*\([^\n]*?\)[^{\n]*\{',text):
        start=m.end();at=start;depth=1;quoted=False
        while at<len(text) and depth:
            c=text[at]
            if quoted:
                if c=='\\':at+=2;continue
                if c=='"':quoted=False
            elif c=='"':quoted=True
            elif text.startswith('//',at):
                at=text.find('\n',at)
                if at<0:break
                continue
            elif c=='{':depth+=1
            elif c=='}':depth-=1
            at+=1
        if depth:raise ValueError(('Unclosed function',m.group(1)))
        if m.group(1) not in out:out[m.group(1)]=text[start:at-1]
    return out


def indexed_literals(body):
    if body is None:return {}
    found={}
    pattern=r'if\s+i\s*==\s*(\d+)\s*\{\s*return\s+(\[[^\n]*?\]|"(?:\\.|[^"\\])*")\s*;'
    for m in re.finditer(pattern,body):
        found[int(m.group(1))]=json.loads(m.group(2))
    return found


def literal(body):
    if body is None:return None
    m=re.fullmatch(r'\s*return\s+(\[[^\n]*?\]|"(?:\\.|[^"\\])*"|\d+)\s*;\s*',body)
    return json.loads(m.group(1)) if m else None


def script_tables(path):
    text=path.read_text(encoding='utf-8-sig')
    classes=list(re.finditer(r'(?m)^(?:public |private )?(?:abstract )?class\s+(\w+)[^{\n]*\{',text))
    out=[]
    for at,m in enumerate(classes):
        chunk=text[m.start():classes[at+1].start() if at+1<len(classes) else len(text)]
        if not ('Data' in m.group(1) or 'Facts' in chunk):continue
        methods=function_bodies(chunk)
        arrays={k:literal(v) for k,v in methods.items() if isinstance(literal(v),list)}
        ids=indexed_literals(methods.get('ID'))
        titles=indexed_literals(methods.get('Title'))
        if isinstance(arrays.get('IDs'),list):ids=dict(enumerate(arrays['IDs']))
        if isinstance(arrays.get('Titles'),list):titles=dict(enumerate(arrays['Titles']))
        range_rows=[]
        variants=defaultdict(dict)
        for key in ['FactNames','FactMin','FactMax','Paths','Classes','StatesA','StatesB','Facts','TerminalFacts']:
            for index,values in indexed_literals(methods.get(key)).items():variants[index][key]=values
            for name,values in arrays.items():
                tail=name[len(key):] if name.startswith(key) else None
                if tail is not None and tail.isdigit():variants[int(tail)][key]=values
        for i,row in sorted(variants.items()):
            range_rows.append({'index':i,'id':ids.get(i),'title':titles.get(i),**row})
        if range_rows:
            out.append({'file':str(path),'file_sha256':sha(path),'class':m.group(1),'count':literal(methods.get('Count')),'rows':range_rows})
    return out


def main():
    output=HERE/'inventory_01.json';assert not output.exists()
    installed=read(INSTALLED);manifest=read(BASE/'package_manifest.json')
    for row in installed['core_files']+installed['required_files']:
        assert sha(Path(installed['game_root'])/row['path'])==row['sha256'],row['path']
    cache=read(CACHE)
    resources=[];fresh=[]
    for depot,h in manifest['source_resources'].items():
        if not depot.endswith(('.questphase','.quest')):continue
        p=BASE/'archive_source'/depot
        assert sha(p)==h,depot
        match=cache.get(depot)
        if match and match['resource_sha256']==h:
            row={'depot':depot,'sha256':h,'raw':str(p),'model':match['normalized_model'],'model_sha256':match['normalized_sha256'],'source_json':match['source_json'],'reuse':'EXACT_RAW_HASH_MATCH'}
            assert sha(row['model'])==row['model_sha256'],row['model']
        else:
            row={'depot':depot,'sha256':h,'raw':str(p),'reuse':'FRESH_EXPORT_REQUIRED'}
            fresh.append(row)
        resources.append(row)
    tables=[]
    for p in sorted((BASE/'package/r6/scripts/PTFR_Consolidated').glob('*.reds')):tables.extend(script_tables(p))
    checkpoint={'schema':1,'status':'AUDITING_GLOBAL_PREPARED_ENTRY_POLICY','authorization':'User: apply the new marker and encounter policy to everything.','baseline':str(INSTALLED),'baseline_sha256':sha(INSTALLED),'scope':'All installed restored quest/phase owners, gigs, side jobs, scanner and ambient encounter admissions; retain selected content boundaries and existing progress/ownership protections.','phase_resources':len(resources),'current_build_installed':False,'next_action':'Complete exact-source models, classify every zero-gated setup flag by source stage and owner lifecycle, then implement consistent native/script admission and native marker/wait setup without resets.'}
    write(output,{'schema':1,'status':'ALL_INSTALLED_PHASES_AND_SCRIPT_TABLES_INVENTORIED','installed_manifest':str(INSTALLED),'installed_manifest_sha256':sha(INSTALLED),'baseline_package':str(BASE/'package_manifest.json'),'baseline_package_sha256':sha(BASE/'package_manifest.json'),'resources':resources,'fresh_exports':fresh,'script_tables':tables,'game_writes':0,'save_writes':0})
    write(HERE/'checkpoint.json',checkpoint)
    print(json.dumps({'resources':len(resources),'reused_models':len(resources)-len(fresh),'fresh_exports':len(fresh),'data_classes':len(tables),'table_rows':sum(len(t['rows']) for t in tables)}))


if __name__=='__main__':
    main()
