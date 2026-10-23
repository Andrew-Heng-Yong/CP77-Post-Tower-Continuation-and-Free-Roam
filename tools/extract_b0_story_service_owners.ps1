param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
# Source-only, bounded quest-owner extraction. No installation or game writes.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$out=Join-Path $WorkspaceRoot 'research\b0_story_services\quest_sources'
$found=[Collections.Generic.List[object]]::new()
foreach($rel in @('content\basegame_4_gamedata.archive','ep1\ep1_2_gamedata.archive')){
 $path=Join-Path 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc' $rel
 $archive=$null
 if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($path,$hs,[ref]$archive).ToString() -ne 'NoError'){throw 'Archive read failed'}
 $entries=@($archive.Files.Values|Where-Object {$_.Name -match '\\(mq023_bootleg_03_vendor|q302_caliente_persistent_content|q302_ronald_tree|bill_default)\.questphase$'})
 if($entries.Count -gt 10){throw 'Unexpected extraction scope'}
 foreach($e in $entries){
  $ms=[IO.MemoryStream]::new()
  try{
   $e.Extract($ms);$raw=Join-Path $out ('raw\'+$e.Name);$json=Join-Path $out ('json\'+$e.Name+'.json')
   New-Item -ItemType Directory -Force -Path (Split-Path $raw),(Split-Path $json)|Out-Null
   [IO.File]::WriteAllBytes($raw,$ms.ToArray());Export-Cr2wJson (Read-Cr2wFile $raw) $json
   $found.Add([pscustomobject]@{resource=$e.Name;sha256=(Get-FileHash $raw).Hash;archive=$path})
  }finally{$ms.Dispose()}
 }
}
if($found.Count -ne 4){throw "Expected four exact owners, found $($found.Count)"}
[IO.File]::WriteAllText((Join-Path $out 'inventory.json'),(ConvertTo-Json -InputObject $found.ToArray() -Depth 4))
$found|Select-Object resource
