from pathlib import Path
O=Path(__file__).resolve().parent
p=O.parent/'quest_restoration_qr4/dispatch.py'
s=p.read_text(encoding='utf-8-sig').replace('if int(k[1:])<=8',"if v['scope']=='PRIMARY'").replace('if int(k[1:])>8',"if v['scope']=='STRETCH'")
assert not (O/'dispatch.py').exists()
(O/'dispatch.py').write_text(s,encoding='utf-8')
