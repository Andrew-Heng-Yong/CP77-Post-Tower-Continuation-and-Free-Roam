# Read-only provider recheck immediately before preparing the HS3 deployment.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out=Join-Path $PSScriptRoot 'deployment_sources_01.json'
if(Test-Path -LiteralPath $out){throw 'Fresh source-check output required'}
$plan=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'evidence_01/plan.json') -Raw|ConvertFrom-Json
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$providers=[Collections.Generic.List[object]]::new();$archives=[Collections.Generic.List[object]]::new();$xl=[Collections.Generic.List[string]]::new()
foreach($rel in @('archive/pc','red4ext/plugins','mods')){
 $root=Join-Path $plan.game_root $rel;if(-not(Test-Path -LiteralPath $root)){continue}
 for($item=Get-Item -LiteralPath $root;$null -ne $item;$item=$item.Parent){if($item.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Linked provider root'}}
 $entries=@(Get-ChildItem -LiteralPath $root -Recurse -Force)
 foreach($entry in $entries){
  if($entry.Attributes -band [IO.FileAttributes]::ReparsePoint){if($entry.PSIsContainer -or $entry.Extension -in @('.archive','.xl')){throw 'Linked provider path'};continue}
  if($entry.PSIsContainer){continue}
  if($entry.Extension -ieq '.xl'){$xl.Add($entry.FullName)}
  if($entry.Extension -ine '.archive'){continue}
  $stamp=@($entry.Length,$entry.LastWriteTimeUtc.Ticks);$a=$null
  $code=([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($entry.FullName,$hs,[ref]$a)
  if($code.ToString() -cne 'NoError'){throw "Archive unreadable: $entry"}
  foreach($gate in $plan.gates){
   if($a.Files.ContainsKey([uint64]$gate.key)){
    $s=[IO.MemoryStream]::new();try{$a.Files[[uint64]$gate.key].Extract($s);$h=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($s.ToArray()))}finally{$s.Dispose()}
    if($entry.FullName -cne $gate.archive -or $h -cne $gate.sha256){throw "Unreviewed phase provider: $entry"}
    $providers.Add(@{depot=$gate.depot;archive=$entry.FullName;sha256=$h})
   }
  }
  $entry.Refresh();if($entry.Length -ne $stamp[0] -or $entry.LastWriteTimeUtc.Ticks -ne $stamp[1]){throw 'Provider changed during scan'}
  $archives.Add(@{path=$entry.FullName;bytes=$entry.Length;mtime_utc_ticks=$stamp[1]})
 }
}
if($providers.Count -ne 2){throw 'Missing exact native phase provider'}
$old=Get-Content -LiteralPath (Join-Path $ws 'prealpha/quest_resume_registry_20261112_01/evidence_01/registrations.json') -Raw|ConvertFrom-Json -Depth 100
$plugin=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'verification_07/plugin_providers.json') -Raw|ConvertFrom-Json -Depth 100
$expected=@($old.files)+@($plugin.xl_files)
if(@(Compare-Object @($expected.path|Sort-Object -Unique) @($xl.ToArray()|Sort-Object -Unique)).Count){throw 'XL registration inventory drift'}
foreach($file in $expected){if((Get-FileHash -LiteralPath $file.path).Hash -cne $file.sha256){throw 'XL registration bytes drift'}}
@{status='PASS_CURRENT_PROVIDERS_AND_REGISTRATIONS';providers=$providers.ToArray();archive_inventory=$archives.ToArray();xl_files=$expected;archive_count=$archives.Count;xl_count=$xl.Count;game_writes=0;save_writes=0;tool_sha256=(Get-FileHash -LiteralPath $PSCommandPath).Hash}|ConvertTo-Json -Depth 12|Set-Content -LiteralPath $out -Encoding utf8NoBOM
Write-Output "PASS: $($archives.Count) archives checked, exact 2 native providers, $($xl.Count) unchanged XL files."
