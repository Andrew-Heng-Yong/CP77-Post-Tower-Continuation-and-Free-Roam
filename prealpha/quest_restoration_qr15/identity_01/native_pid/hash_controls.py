"""Pure arithmetic controls for the pinned native hash instructions, no game execution."""
from pathlib import Path
import json,sys
HERE=Path(__file__).resolve().parent
out=HERE/'hash_controls_01.json'
assert not out.exists()
value=json.loads((HERE/'native_05.json').read_text())
f=next(f for f in value['functions'] if f['begin_rva']=='0x409010')
rows=f['instructions'];by_addr={int(r['rva'],16):n for n,r in enumerate(rows)}
MASK=(1<<64)-1;MAGIC=0xC6A4A7935BD1E995

def sdk_formula(entity,component):
    if not component:return entity
    product=(MAGIC*component)&MASK
    mixed=(MAGIC*(product^(product>>47)))&MASK
    return (MAGIC*(entity^mixed))&MASK

def native_arithmetic(entity,component):
    # Interpret only the14 retained arithmetic/branch instructions as data.
    # No native bytes are mapped executable or called.
    regs={};zero=False;pc=0;steps=0
    def read(v):
        if v=='qword ptr [rcx + 8]':return component
        if v=='qword ptr [rcx]':return entity
        if v in regs:return regs[v]
        return int(v,0)
    while True:
        r=rows[pc];m=r['mnemonic'];parts=r['operands'].split(', ');steps+=1
        assert steps<=20
        if m in ('mov','movabs'):regs[parts[0]]=read(parts[1])
        elif m=='test':zero=(read(parts[0])&read(parts[1]))==0
        elif m=='je':
            if zero:pc=by_addr[int(parts[0],16)-0x140000000];continue
        elif m=='imul':regs[parts[0]]=(read(parts[0])*read(parts[1]))&MASK
        elif m=='shr':regs[parts[0]]=read(parts[0])>>read(parts[1])
        elif m=='xor':regs[parts[0]]=read(parts[0])^read(parts[1])
        elif m=='ret':return regs['rax']
        else:raise AssertionError('Unreviewed instruction '+str(r))
        pc+=1

def cname(value):
    result=0xCBF29CE484222325
    for b in value.encode():result=((result^b)*0x100000001B3)&MASK
    return 0 if value in ('','None') else result

inputs=[(0,0),(1,0),(10229047,0),(0,1),(1,1),(MASK,MASK),(1<<63,1<<63),
        (0xFFFFFFFF,0xFFFFFFFF),(0x1000000,0x18B8DE5B56F6D021)]
for s in ('controller','VehicleController'):
    inputs.append((10229047,cname(s)))
c=cname('controller');p=(MAGIC*c)&MASK;e=(MAGIC*(p^(p>>47)))&MASK
inputs.append((e,c)) # Nonzero pair whose exact arithmetic hash is zero.
controls=[]
for e,c in inputs:
    a=native_arithmetic(e,c);b=sdk_formula(e,c);assert a==b
    controls.append({'entity_u64':str(e),'component_cname_u64':str(c),'native_instruction_arithmetic':str(a),
                     'sdk_formula_u64':str(b),'pass':a==b})
assert native_arithmetic(10229047,cname('controller'))==6695448052237678836
assert native_arithmetic(10229047,cname('VehicleController'))==15311582179580628726
assert e and c and native_arithmetic(e,c)==0
result={'method':'Pure integer interpretation of14 pinned disassembled arithmetic instructions versus independent SDK formula; no native execution',
    'native_helper_rva':'0x409010','exe_sha256':value['exe_sha256'],'magic_u64':str(MAGIC),'mask_bits':64,
    'component_names':{s:str(cname(s)) for s in ('controller','VehicleController','None','')},
    'controls':controls,'control_count':len(controls),'all_pass':True,
    'limits':'Arithmetic identity only; these inputs do not establish the associated saved ID namespace, component existence, dynamic eligibility or PS existence',
    'game_api_calls':0,'runtime_changes':0,'save_reads':0}
out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='controls'},indent=2))
