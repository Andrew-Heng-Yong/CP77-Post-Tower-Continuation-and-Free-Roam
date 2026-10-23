param([ValidateSet('parents','encounters','support')][string]$Group='parents',[string]$Attempt='02')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly
if($Attempt -cnotmatch '^\d{2}$'){throw 'Invalid attempt'}
$out=Join-Path $ws ('research/ncpd_scanner_n1/'+$Group+'_'+$Attempt)
if(Test-Path $out){throw 'Extraction evidence exists; preserve it'}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$ap='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc\content\basegame_4_gamedata.archive'
$arc=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($ap,$hs,[ref]$arc).ToString() -ne 'NoError'){throw 'Archive read failed'}
$entries=@($arc.Files.Values|Where-Object {
 if($Group -eq 'parents'){
  $_.Extension -eq '.questphase' -and ($_.Name -match '^base\\open_world\\minor_activities\\.*minor_activities\.questphase$' -or $_.Name -eq 'base\open_world\open_world.questphase')
 }elseif($Group -eq 'encounters'){
  $_.Extension -eq '.questphase' -and $_.Name -match '^base\\open_world\\minor_activities\\' -and $_.Name -notmatch 'minor_activities\.questphase$'
 }else{
  ($_.Name -match '^base\\quest\\holocalls\\ncpd_dispatcher\\' -and $_.Extension -in @('.questphase','.scene')) -or $_.Name -eq 'base\open_world\open_world.questphase'
 }
}|Sort-Object Name)
if(!$entries.Count){throw 'No resources found'}
New-Item -ItemType Directory $out | Out-Null
$rows=@()
foreach($e in $entries){
 $m=[IO.MemoryStream]::new()
 try{
  $e.Extract($m);$bytes=$m.ToArray();$raw=Join-Path $out ('raw/'+$e.Name)
  New-Item -ItemType Directory -Force (Split-Path $raw -Parent)|Out-Null
  [IO.File]::WriteAllBytes($raw,$bytes)
  $json=Join-Path $out ('json/'+$e.Name+'.json')
  New-Item -ItemType Directory -Force (Split-Path $json -Parent)|Out-Null
  Export-Cr2wJson (Read-Cr2wFile $raw) $json
  $rows+=,@{resource=$e.Name;archive=$ap;raw_sha256=(Get-FileHash $raw).Hash;json_sha256=(Get-FileHash $json).Hash}
 }finally{$m.Dispose()}
}
[IO.File]::WriteAllText((Join-Path $out 'inventory.json'),($rows|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
@{group=$Group;resources=$rows.Count;game_writes=0;save_writes=0}|ConvertTo-Json
