from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'decode_01.ps1').read_text(encoding='utf-8-sig')
s=s.replace('WA2EnvReadOnly01','WA2EnvReadOnly02').replace("'decode_01'","'decode_02'")
needle=' public class worldCookedCollisionNode'
assert needle in s
new=''
for name in ['worldCookedCableMeshNode','worldCookedFoliageDestructionNode']:
    new+=' public class '+name+' : worldNode, IDynamicClass {[RED("className")] public CName ClassName {get;set;}="'+name+'";}\n'
s=s.replace(needle,new+needle)
needle='foreach($entry in $types.GetEnumerator()) {'
add=''
for name in ['worldCookedCableMeshNode','worldCookedFoliageDestructionNode']:
    add+="$types['"+name+"']=[WA2EnvReadOnly02."+name+"]\n"
s=s.replace(needle,add+needle)
needle="foreach($rawFile in (Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot 'extract_01') -Filter '*.streamingsector')) {"
assert needle in s
s=s.replace(needle,"$failed=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'decode_01/report_01.json') -Raw|ConvertFrom-Json -Depth 15\nforeach($item in $failed.rows|Where-Object {!$_.parsed}) {\n $rawFile=Get-Item -LiteralPath $item.raw")
target=H/'decode_02.ps1';assert not target.exists();target.write_text(s,encoding='utf-8')
