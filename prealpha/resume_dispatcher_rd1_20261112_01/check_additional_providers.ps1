param([string]$Candidate='candidate_04')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$dir=Join-Path $PSScriptRoot $Candidate
$out=Join-Path $dir 'additional_providers.json'
if(Test-Path -LiteralPath $out){throw 'Fresh provider report required'}
$pins=Get-Content -LiteralPath (Join-Path $dir 'additional_sources.json') -Raw|ConvertFrom-Json
$inventory=(Get-Content -LiteralPath (Join-Path $PSScriptRoot 'archive_04/readback.json') -Raw|ConvertFrom-Json).archive_inventory
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$rows=[Collections.Generic.List[object]]::new()
foreach($file in $inventory){
 $item=Get-Item -LiteralPath $file.path
 if($item.Length -ne $file.bytes -or $item.LastWriteTimeUtc.Ticks -ne $file.mtime_ticks){throw 'Archive inventory changed'}
 $a=$null;$code=([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($file.path,$hs,[ref]$a)
 if($code.ToString() -cne 'NoError'){throw 'Unreadable archive'}
 foreach($p in $pins){if($a.Files.ContainsKey([uint64]$p.key)){
  $s=[IO.MemoryStream]::new();try{$a.Files[[uint64]$p.key].Extract($s);$hash=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($s.ToArray()))}finally{$s.Dispose()}
  if($file.path -cne $p.archive -or $hash -cne $p.sha256){throw "Provider changed: $($p.depot)"}
  $rows.Add(@{depot=$p.depot;archive=$file.path;sha256=$hash})
 }}
 $item.Refresh();if($item.Length -ne $file.bytes -or $item.LastWriteTimeUtc.Ticks -ne $file.mtime_ticks){throw 'Archive changed while reading'}
}
if($rows.Count -ne $pins.Count){throw 'Missing provider'}
@{status='PASS';providers=$rows.ToArray();archives_checked=$inventory.Count;game_writes=0}|ConvertTo-Json -Depth 5|Set-Content -LiteralPath $out -Encoding utf8NoBOM
Write-Output 'Native parent and both ambient owner providers match reviewed sources.'
