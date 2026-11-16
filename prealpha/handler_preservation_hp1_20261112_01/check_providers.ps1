# Validate selected resources against every installed archive provider, read-only.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$out=Join-Path $PSScriptRoot 'evidence_02'
if(Test-Path -LiteralPath $out){throw 'Fresh output required'}
$sources=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'analysis_01/sources.json') -Raw|ConvertFrom-Json
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$wanted=@{};foreach($row in $sources){$wanted[[uint64]$row.key]=$row.depot}
$files=@(foreach($rel in @('archive/pc','red4ext/plugins','mods')){
 $folder=Join-Path $game $rel
 if(Test-Path -LiteralPath $folder){Get-ChildItem -LiteralPath $folder -Recurse -Force -File -Filter '*.archive'}
})|Sort-Object FullName -Unique
$inventory=@();$providers=@()
foreach($file in $files){
 for($parent=$file;$null -ne $parent;){if($parent.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Linked archive refused'};$parent=if($parent -is [IO.FileInfo]){$parent.Directory}else{$parent.Parent}}
 $stamp=@($file.Length,$file.LastWriteTimeUtc.Ticks);$archive=$null
 if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($file.FullName,$hs,[ref]$archive).ToString() -cne 'NoError'){throw 'Archive parse failed'}
 foreach($key in $wanted.Keys){
  if($archive.Files.ContainsKey($key)){
   $entry=$archive.Files[$key];$memory=[IO.MemoryStream]::new()
   try{$entry.Extract($memory);$hash=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($memory.ToArray()))}finally{$memory.Dispose()}
   $providers+=@{archive=$file.FullName;depot=$wanted[$key];key=$key.ToString();sha256=$hash}
  }
 }
 $file.Refresh();if($file.Length -ne $stamp[0] -or $file.LastWriteTimeUtc.Ticks -ne $stamp[1]){throw 'Archive changed during read'}
 $inventory+=@{path=$file.FullName;bytes=$stamp[0];mtime_ticks=$stamp[1]}
}
foreach($row in $sources){
 $matches=@($providers|Where-Object {$_.archive -ceq $row.archive -and $_.key -ceq $row.key})
 if($matches.Count -ne 1 -or $matches[0].sha256 -cne $row.sha256){throw "Provider drift: $($row.depot)"}
}
New-Item -ItemType Directory -Path $out|Out-Null
@{status='SELECTED_PROVIDERS_MATCH_CURRENT_BYTES';sources_checked=$sources.Count;archives=$inventory;providers=$providers;game_writes=0;save_writes=0;tool_sha256=(Get-FileHash -LiteralPath $PSCommandPath).Hash;limits='All matching providers are retained; effective override choices must be reviewed separately.'}|ConvertTo-Json -Depth 10|Set-Content -LiteralPath (Join-Path $out 'providers.json') -Encoding utf8NoBOM
Write-Output "Checked $($sources.Count) sources across $($files.Count) archives; $($providers.Count) matching providers."
