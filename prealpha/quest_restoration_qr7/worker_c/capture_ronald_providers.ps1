param([string]$Output='ronald_current_providers_01')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$W=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
$O=Join-Path $PSScriptRoot $Output
if(Test-Path -LiteralPath $O){throw 'Fresh worker output required'}
. (Join-Path $W 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $W 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$depots=@('ep1\quest\main_quests\q302\phases\q302_ronald_tree.questphase','ep1\quest\main_quests\q302\phases\q302_msg_ronald_sts_ep1_01.questphase','ep1\quest\main_quests\q302\phases\q302_msg_ronald_sts_ep1_03.questphase','ep1\quest\main_quests\q302\phases\q302_msg_ronald_sts_ep1_08.questphase','ep1\quest\main_quests\q302\phases\q302_msg_ronald_sts_ep1_12.questphase')
$targets=@{}
foreach($d in $depots){$targets[[string][WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($d)]=$d}
$game='C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077'
$archives=@(Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc') -Filter '*.archive' -Recurse -File|Sort-Object FullName)
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
[IO.Directory]::CreateDirectory($O)|Out-Null
$inventory=@();$rows=@();$i=0
foreach($f in $archives){
 $before=@($f.Length,$f.LastWriteTimeUtc.Ticks);$a=$null
 $read=([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($f.FullName,$hs,[ref]$a)
 if($read.ToString() -ne 'NoError'){throw ('Unreadable provider '+$f.FullName)}
 $found=@()
 foreach($key in $targets.Keys){
  if(-not $a.Files.ContainsKey([uint64]$key)){continue}
  $depot=$targets[$key];$found+=,$depot;$i++
  $raw=Join-Path $O ('resource_'+$i+[IO.Path]::GetExtension($depot));$json=$raw+'.json'
  $mem=[IO.MemoryStream]::new()
  try{$a.Files[[uint64]$key].Extract($mem);[IO.File]::WriteAllBytes($raw,$mem.ToArray())}finally{$mem.Dispose()}
  $r=@{depot=$depot;key=$key;provider=$f.FullName;provider_metadata=$before;raw=$raw;raw_sha256=(Get-FileHash -LiteralPath $raw).Hash}
  try{Export-Cr2wJson (Read-Cr2wFile $raw) $json;$r.json=$json;$r.json_sha256=(Get-FileHash -LiteralPath $json).Hash;$r.status='DECODED'}
  catch{$r.status='OPAQUE';$r.error=$_.Exception.Message}
  $rows+=,$r
 }
 $f.Refresh();if($f.Length -ne $before[0] -or $f.LastWriteTimeUtc.Ticks -ne $before[1]){throw 'Provider changed while reading'}
 $inventory+=,@{path=$f.FullName;metadata=$before;index_entries=$a.Files.Count;matches=$found}
}
@{status='READ_ONLY_RONALD_NATIVE_PROVIDER_CAPTURE';targets=$depots;resources=$rows;archive_index_inventory=$inventory;code_sha256=(Get-FileHash -LiteralPath $PSCommandPath).Hash;limits=@('Provider payloads pinned; provider file metadata verified during read.','No provider precedence is guessed from lexical order. Identical bytes across colliding providers need no winner decision.','Only these five native Ronald owner/message resource providers are covered.')}|ConvertTo-Json -Depth 30|Set-Content -LiteralPath (Join-Path $O 'manifest.json') -Encoding utf8NoBOM
@{archive_indexes=$inventory.Count;matches=$rows.Count;opaque=@($rows|Where-Object status -eq 'OPAQUE').Count;output=$O}|ConvertTo-Json -Compress
