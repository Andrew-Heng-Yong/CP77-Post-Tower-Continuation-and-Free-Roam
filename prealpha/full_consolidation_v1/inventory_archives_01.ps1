Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$mods='C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077/archive/pc/mod'
$files=[string[]]@(Get-ChildItem -LiteralPath $mods -Filter '*TowerContinued*.archive' -File|ForEach-Object FullName)
[Array]::Sort($files,[StringComparer]::OrdinalIgnoreCase)
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$rows=[Collections.Generic.List[object]]::new();$seen=@{};$collisions=[Collections.Generic.List[object]]::new();$unresolved=[Collections.Generic.List[object]]::new()
foreach($path in $files){
 $a=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($path,$hs,[ref]$a).ToString() -cne 'NoError'){throw ('Archive unreadable '+$path)}
 $members=[Collections.Generic.List[object]]::new()
 foreach($e in $a.Files.Values){
  $name=$e.Name
  if($name -notlike 'towercontinued\*'){$unresolved.Add(@{archive=$path;key=$e.Key.ToString();name=$name})}
  $m=[IO.MemoryStream]::new();try{$e.Extract($m);$hash=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($m.ToArray()))}finally{$m.Dispose()}
  $members.Add(@{depot=$name;key=$e.Key.ToString();sha256=$hash})
  if($seen.ContainsKey($e.Key.ToString())){$collisions.Add(@{depot=$name;old_archive=$seen[$e.Key.ToString()].archive;new_archive=$path;old_sha256=$seen[$e.Key.ToString()].sha256;new_sha256=$hash})}
  $seen[$e.Key.ToString()]=@{archive=$path;sha256=$hash;depot=$name}
 }
 $rows.Add(@{archive=$path;sha256=(Get-FileHash -LiteralPath $path).Hash;members=$members.ToArray()})
}
$proof=[ordered]@{status='CURRENT_INSTALLED_PTFR_ARCHIVE_INVENTORY_READ_ONLY';archive_count=$files.Count;source_member_count=@($rows|ForEach-Object {$_.members.Count}|Measure-Object -Sum).Sum;unique_member_count=$seen.Count;unresolved=$unresolved.ToArray();collisions=$collisions.ToArray();archives=$rows.ToArray();game_writes=0;save_writes=0}
$out=Join-Path $PSScriptRoot 'inventory_archives_01.json';if(Test-Path -LiteralPath $out){throw 'Inventory exists'}
[IO.File]::WriteAllText($out,($proof|ConvertTo-Json -Depth 50),[Text.UTF8Encoding]::new($false))
@{status=$proof.status;archives=$proof.archive_count;members=$proof.source_member_count;unique=$proof.unique_member_count;collisions=$collisions.Count;unresolved=$unresolved.Count}|ConvertTo-Json
