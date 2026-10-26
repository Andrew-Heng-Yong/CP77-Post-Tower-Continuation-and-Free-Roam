Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$inventory=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'inventory_archives_01.json') -Raw|ConvertFrom-Json
$collisions=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'external_collisions_01.json') -Raw|ConvertFrom-Json
if($inventory.status -cne 'CURRENT_INSTALLED_PTFR_ARCHIVE_INVENTORY_READ_ONLY' -or $inventory.archive_count -ne 25 -or $inventory.unique_member_count -ne 1153 -or $collisions.collisions.Count -ne 0){throw 'Archive source inventory changed'}
$out=Join-Path $PSScriptRoot 'candidate_01';$source=Join-Path $out 'archive_source';$archive=Join-Path $out 'package/archive/pc/mod/zzzz_PTFR_Combined.archive'
if(Test-Path -LiteralPath $source -or Test-Path -LiteralPath $archive){throw 'Archive candidate exists; use successor'}
New-Item -ItemType Directory -Path $source,(Split-Path $archive -Parent) -Force|Out-Null
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$winners=@{};$rows=[Collections.Generic.List[object]]::new()
foreach($row in $inventory.archives){
 $path=$row.archive;if((Get-FileHash -LiteralPath $path).Hash -cne $row.sha256){throw ('Installed archive drift '+$path)}
 $a=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($path,$hs,[ref]$a).ToString() -cne 'NoError' -or $a.Files.Count -ne $row.members.Count){throw ('Archive read/count changed '+$path)}
 $map=@{};foreach($m in $row.members){$map[$m.key]=$m}
 foreach($e in $a.Files.Values){
  $key=$e.Key.ToString();$prior=$map[$key];if($null -eq $prior -or $e.Name -cne $prior.depot){throw ('Archive name/key changed '+$path)}
  if([IO.Path]::IsPathRooted($e.Name) -or $e.Name.Contains(':') -or @($e.Name.Replace('\','/').Split('/')) -contains '..'){throw ('Unsafe depot path '+$e.Name)}
  if([WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($e.Name).ToString() -cne $key){throw ('Hash/name mismatch '+$e.Name)}
  $dest=Join-Path $source $e.Name;New-Item -ItemType Directory -Path (Split-Path $dest -Parent) -Force|Out-Null
  $m=[IO.MemoryStream]::new();try{$e.Extract($m);$bytes=$m.ToArray();$hash=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))}finally{$m.Dispose()}
  if($hash -cne $prior.sha256){throw ('Archive content drift '+$e.Name)}
  [IO.File]::WriteAllBytes($dest,$bytes)
  $winners[$key]=@{depot=$e.Name;sha256=$hash;source_archive=$path}
 }
 $rows.Add(@{archive=$path;sha256=$row.sha256;members=$row.members.Count})
}
if($winners.Count -ne 1153){throw 'Merged winner count changed'}
$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Merged archive writer failed'}}finally{$stream.Dispose()}
$packed=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -cne 'NoError' -or $packed.Files.Count -ne 1153){throw 'Merged archive readback count mismatch'}
foreach($e in $packed.Files.Values){$expected=$winners[$e.Key.ToString()];if($null -eq $expected -or $e.Name -cne $expected.depot){throw ('Merged archive member mismatch '+$e.Name)};$m=[IO.MemoryStream]::new();try{$e.Extract($m);$hash=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($m.ToArray()))}finally{$m.Dispose()};if($hash -cne $expected.sha256){throw ('Merged archive payload drift '+$e.Name)}}
$proof=[ordered]@{status='PTFR_25_ARCHIVES_TO_1_WINNING_PAYLOAD_READBACK_PASS';archive=$archive;sha256=(Get-FileHash -LiteralPath $archive).Hash;source_archives=$rows.ToArray();original_member_entries=1190;effective_members=1153;intentional_collisions=37;external_collisions=0;game_writes=0;save_writes=0}
$dest=Join-Path $out 'build_archive_01.json';[IO.File]::WriteAllText($dest,($proof|ConvertTo-Json -Depth 30),[Text.UTF8Encoding]::new($false))
@{status=$proof.status;effective_members=$proof.effective_members;sha256=$proof.sha256}|ConvertTo-Json
