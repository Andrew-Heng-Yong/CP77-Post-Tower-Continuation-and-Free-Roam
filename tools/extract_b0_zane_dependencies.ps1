param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
# Bounded source-only extraction to examine Bullets' consumers of service facts.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$archive=$null
$path='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc\content\basegame_4_gamedata.archive'
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($path,$hs,[ref]$archive).ToString() -ne 'NoError'){throw 'Archive read failed'}
$out=Join-Path $WorkspaceRoot 'research\b0_story_zane\quest_sources'
$entries=@($archive.Files.Values|Where-Object {$_.Name -match '\\mq030\\.*\.(quest|questphase)$'})
if(-not $entries.Count -or $entries.Count -gt 30){throw 'Unexpected extraction scope'}
$rows=foreach($e in $entries){
 $ms=[IO.MemoryStream]::new()
 try{
  $e.Extract($ms);$bytes=$ms.ToArray();$ms.Position=0
  $raw=Join-Path $out ('raw\'+$e.Name);$json=Join-Path $out ('json\'+$e.Name+'.json')
  New-Item -ItemType Directory -Force -Path (Split-Path $raw),(Split-Path $json)|Out-Null
  [IO.File]::WriteAllBytes($raw,$bytes)
  Export-Cr2wJson (Read-Cr2wFile $raw) $json
  [pscustomobject]@{resource=$e.Name;sha256=(Get-FileHash $raw).Hash;archive=$path}
 }finally{$ms.Dispose()}
}
[IO.File]::WriteAllText((Join-Path $out 'inventory.json'),(ConvertTo-Json -InputObject @($rows) -Depth 4))
$rows|Select-Object resource
