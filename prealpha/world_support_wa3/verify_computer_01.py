"""Independently bind the coordinated CO1 patch to its single approved method."""
from pathlib import Path
from hashlib import sha256
import json
H=Path(__file__).resolve().parent
C=H.parent/'computer_overlay_co1/candidate_02'
old=C/'original/SetupNewTab.reds';new=C/'SetupNewTab.reds'
digest=lambda p:sha256(p.read_bytes()).hexdigest().upper()
def cut(data):
    marker=b'private func PopulateAtelierView()'
    assert data.count(marker)==1
    begin=data.index(marker);start=data.index(b'{',begin);depth=0
    for i in range(start,len(data)):
        if data[i]==ord('{'):depth+=1
        if data[i]==ord('}'):
            depth-=1
            if depth==0:return data[:start],data[start:i+1],data[i+1:]
    raise AssertionError('Unclosed method')
a=cut(old.read_bytes());b=cut(new.read_bytes())
assert a[0]==b[0] and a[2]==b[2],'Outside method bytes changed'
assert digest(old)=='14B651576CC6D1FCEDBC11A48A96D1A2AC79DD84FCCFB90097F4169057378F80'
assert digest(new)=='5743CDCD6F8CD46A58F9642002F75EBCA25D84BE340856C2E6D85B15DAD973F8'
body=b[1].decode()
for text in ['this.GetWidget(n"page")','this.GetWidget(n"Page")','this.GetRootCompoundWidget()','root.RemoveAllChildren();','this.SpawnFromExternal(root,']:
    assert text in body,text
assert body.index('root.RemoveAllChildren();')<body.index('this.SpawnFromExternal(root,')
out=H/'computer_independent_01.json';assert not out.exists()
result={'status':'PASS','scope':'Exactly PopulateAtelierView replacement; full native page body cleared before Atelier spawn, frame retained when page exists.','outside_method_bytes_unchanged':True,'selected_candidate':2,'game_writes':0,'save_writes':0,'runtime_verified':False,'pins':[{'path':str(p.resolve()),'sha256':digest(p)} for p in [old,new,Path(__file__)]]}
out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
print('CO1 exact-method scope PASS')
