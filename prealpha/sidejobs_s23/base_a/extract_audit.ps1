param([string]$Revision='native_01')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$WorkspaceRoot=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $WorkspaceRoot 'tools/build_phase2a.ps1') -HelpersOnly
if($Revision -cnotmatch '^native_\d{2}$'){throw 'Invalid revision'}
$out=Join-Path $WorkspaceRoot ('research/sidejobs_s23/base_a/'+$Revision)
if(Test-Path -LiteralPath $out){throw 'Immutable audit exists'}
New-Item -ItemType Directory -Path $out|Out-Null
$depots=@{};$inputs=@{}
$families=@('mq024','mq007','mq035','mq012','mq002','mq021','mq041','mq044')
foreach($family in $families){
 foreach($p in Get-ChildItem -LiteralPath (Join-Path $WorkspaceRoot ('research/activity_state_r3/native_sources/json/base/quest/minor_quests/'+$family)) -File -Recurse -Filter '*.json'){
  $inputs[$p.FullName]=(Get-FileHash -LiteralPath $p.FullName).Hash
  foreach($m in [regex]::Matches((Get-Content -LiteralPath $p.FullName -Raw),'"\$value"\s*:\s*"([^"]+\.scene)"')){
   $depot=('"'+$m.Groups[1].Value+'"')|ConvertFrom-Json
   if($depot.StartsWith('base\quest\minor_quests\'+$family+'\')){$depots[$depot]=$true}
  }
 }
}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$archive=$null
$official='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc\content\basegame_4_gamedata.archive'
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($official,$hs,[ref]$archive).ToString() -ne 'NoError'){throw 'Official archive unreadable'}
$rows=@();$missing=@()
foreach($depot in $depots.Keys|Sort-Object){
 $key=[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($depot)
 if(!$archive.Files.ContainsKey($key)){$missing+=,$depot;continue}
 $target=Join-Path (Join-Path $out 'raw') $depot
 New-Item -ItemType Directory -Path (Split-Path -Parent $target) -Force|Out-Null
 $stream=[IO.File]::Create($target);try{$archive.Files[$key].Extract($stream)}finally{$stream.Dispose()}
 $json=Join-Path (Join-Path $out 'json') ($depot+'.json');New-Item -ItemType Directory -Path (Split-Path -Parent $json) -Force|Out-Null;Export-Cr2wJson (Read-Cr2wFile $target) $json
 $rows+=,@{depot=$depot;raw=$target;sha256=(Get-FileHash -LiteralPath $target).Hash;json=$json;json_sha256=(Get-FileHash -LiteralPath $json).Hash}
}
[IO.File]::WriteAllText((Join-Path $out 'manifest.json'),(@{status='READ_ONLY_NATIVE_SCENE_EXTRACTION';extractor_sha256=(Get-FileHash -LiteralPath $PSCommandPath).Hash;official=$official;inputs=$inputs;scenes=$rows;missing=$missing}|ConvertTo-Json -Depth 10),[Text.UTF8Encoding]::new($false))
@{scenes=$rows.Count;output=$out}|ConvertTo-Json
