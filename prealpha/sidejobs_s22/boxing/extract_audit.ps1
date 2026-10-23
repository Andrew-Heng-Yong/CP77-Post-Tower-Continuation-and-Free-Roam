param([string]$Revision='native_01')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$WorkspaceRoot=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $WorkspaceRoot 'tools/build_phase2a.ps1') -HelpersOnly
if($Revision -cnotmatch '^native_\d{2}$'){throw 'Invalid revision'}
$out=Join-Path $WorkspaceRoot ('research/sidejobs_s22/boxing/'+$Revision)
if(Test-Path -LiteralPath $out){throw 'Immutable audit exists'}
New-Item -ItemType Directory -Path $out|Out-Null
$depots=@{};$inputs=@{}
foreach($p in Get-ChildItem -LiteralPath (Join-Path $WorkspaceRoot 'research/activity_state_r3/native_sources/json/base/quest/minor_quests/mq025/phases') -File -Filter '*.json'){
 $inputs[$p.FullName]=(Get-FileHash -LiteralPath $p.FullName).Hash
 foreach($m in [regex]::Matches((Get-Content -LiteralPath $p.FullName -Raw),'"\$value"\s*:\s*"([^"]+\.scene)"')){
  $depot=('"'+$m.Groups[1].Value+'"')|ConvertFrom-Json
  if($depot.StartsWith('base\quest\minor_quests\mq025\scenes\')){$depots[$depot]=$true}
 }
}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$archive=$null
$official='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc\content\basegame_4_gamedata.archive'
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($official,$hs,[ref]$archive).ToString() -ne 'NoError'){throw 'Official archive unreadable'}
$rows=@()
foreach($depot in $depots.Keys|Sort-Object){
 $key=[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($depot)
 if(!$archive.Files.ContainsKey($key)){throw "Missing native scene: $depot"}
 $target=Join-Path (Join-Path $out 'raw') $depot
 New-Item -ItemType Directory -Path (Split-Path -Parent $target) -Force|Out-Null
 $stream=[IO.File]::Create($target);try{$archive.Files[$key].Extract($stream)}finally{$stream.Dispose()}
 $json=Join-Path (Join-Path $out 'json') ($depot+'.json');New-Item -ItemType Directory -Path (Split-Path -Parent $json) -Force|Out-Null;Export-Cr2wJson (Read-Cr2wFile $target) $json
 $rows+=,@{depot=$depot;raw=$target;sha256=(Get-FileHash -LiteralPath $target).Hash;json=$json;json_sha256=(Get-FileHash -LiteralPath $json).Hash}
}
[IO.File]::WriteAllText((Join-Path $out 'manifest.json'),(@{status='READ_ONLY_NATIVE_SCENE_EXTRACTION';extractor_sha256=(Get-FileHash -LiteralPath $PSCommandPath).Hash;official=$official;inputs=$inputs;scenes=$rows}|ConvertTo-Json -Depth 10),[Text.UTF8Encoding]::new($false))
@{scenes=$rows.Count;output=$out}|ConvertTo-Json
