from pathlib import Path
H=Path(__file__).resolve().parent;W=H.parent.parent
s=(W/'prealpha/startup_crash_sc1/build_02.ps1').read_text(encoding='utf-8-sig')
s=s.replace('native_source_02','native_source_01').replace('readback_02','readback_01').replace("'build_02.json'","'native_01.json'")
s=s.replace('E8F4F535A9A24B8C080360D68C8993B19EDE12366118284E5A9CE683A0CA523E','76A4DE057573AE13CB698AED6E757454A07D95DBC00A94F9D5F63DA484CBDA07')
s=s.replace("$prepared=Get-Content -LiteralPath (Join-Path $C 'prepared_01.json') -Raw|ConvertFrom-Json -Depth 100\nif($prepared.resources.Count -ne 9){throw 'Unexpected scene scope'}\n",'')
needle="New-Item -ItemType Directory -Path (Join-Path $C 'readback_01')|Out-Null"
assert needle in s
s=s.replace(needle,'''New-Item -ItemType Directory -Path (Join-Path $C 'native_before_01')|Out-Null
foreach($id in @('northside','japantown','glen','corpo')){
 $p=Join-Path $source ('towercontinued/housing_h1/native/'+$id+'_purchase.scene')
 Export-Cr2wJson (Read-Cr2wFile $p) (Join-Path $C ('native_before_01/'+$id+'_purchase.scene.json'))
}
& 'C:/Users/Ayong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' (Join-Path $PSScriptRoot 'prepare_native_01.py')
if($LASTEXITCODE -ne 0){throw 'Scene preparation failed'}
$prepared=Get-Content -LiteralPath (Join-Path $C 'prepared_native_01.json') -Raw|ConvertFrom-Json -Depth 100
if($prepared.resources.Count -ne 4){throw 'Unexpected scene scope'}
'''+needle)
s=s.replace('$unchanged -ne 8','$unchanged -ne 13').replace('BUILT_SC1_NATIVE_NOT_LIVE','BUILT_LC3_NATIVE_NOT_LIVE')
with (H/'native_01.ps1').open('x') as f:f.write(s)
