import json,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from catalog_gig_rollout_r2 import read,sha,walk,value,handles,deref
from test_rite_g2 import SafeResource
from audit_activity_batches_b1 import flatten,references
from prepare_gig_family_b7 import ancestors,descendants

def index():
    result={}
    for directory in ['native_01','native_03','discovery_01','discovery_02']:
        p=ROOT/f'research/sidejobs_s29/{directory}/inventory.json'
        if not p.exists():continue
        for row in read(p)['rows']:
            if row['depot'] in result: assert result[row['depot']]['sha256']==row['sha256'],row['depot']
            result[row['depot']]=row
    return result
INDEX=index()
def load(dep):return read(ROOT/INDEX[dep]['json'])
def graphset(dep):
    obj=load(dep);r=SafeResource(obj)
    return {g['path']:g for g in flatten(r,obj['Data']['RootChunk'])}
def write(name,data):
    p=ROOT/'research/sidejobs_s29'/name
    assert not p.exists(),p
    p.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def closure(seeds):
    queue=list(seeds);seen=set();missing=set()
    while queue:
        dep=queue.pop(0)
        if dep in seen:continue
        if dep not in INDEX:missing.add(dep);continue
        seen.add(dep);root=load(dep)['Data']['RootChunk']
        for field in ['phaseResource','sceneFile']:queue+=references(root,field)
    return sorted(seen),sorted(missing)
def metadata():
    out={}
    for dep in ['ep1_2_gamedata/json/base/journal/cooked_journal.journal.json','ep1_2_gamedata/json/ep1/journal/cooked_journal.journal.json']:
        d=read(ROOT/'research/sidejobs_s28/journal_variants_05'/dep);h=handles(d)
        def visit(w,path):
            n=deref(w,h);p=path+([n['id']] if n.get('id') else [])
            out['/'.join(p)]=n.get('$type')
            for c in n.get('entries',[]):visit(c,p)
        visit(d['Data']['RootChunk']['entry'],[])
    return out
