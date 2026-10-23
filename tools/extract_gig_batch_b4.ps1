param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -HelpersOnly
$root=Join-Path $WorkspaceRoot 'research\gig_restoration\batch_b4\sources'
$catalogue=Get-Content (Join-Path $WorkspaceRoot 'research\gig_restoration\batch_b4\catalogue.json') -Raw|ConvertFrom-Json
$ids=@($catalogue.jobs.id);$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$chosen=@{}
foreach($archivePath in @('C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc\content\basegame_4_gamedata.archive','C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc\ep1\ep1_2_gamedata.archive')){
 $archive=$null
 if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archivePath,$hs,[ref]$archive).ToString() -ne 'NoError'){throw 'Native archive read failed'}
 foreach($entry in $archive.Files.Values){
  if($entry.Extension -notin @('.scene','.questphase','.community') -or $entry.Name -match '\\(test|tests|versions|debug)\\'){continue}
  $match=$false
  foreach($id in $ids){if($entry.Name.Contains('\'+$id+'\') -or $entry.Name.Contains('\'+$id+'_') -or $entry.Name.EndsWith('\'+$id+'.questphase')){$match=$true;break}}
  if($match){$chosen[$entry.Name]=@{entry=$entry;archive=$archivePath}}
 }
}
$inventory=@()
foreach($name in @($chosen.Keys|Sort-Object)){
 $item=$chosen[$name];$m=[IO.MemoryStream]::new()
 try{
  $item.entry.Extract($m);$bytes=$m.ToArray();$hash=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))
  $raw=Join-Path $root ('raw\'+$name);$json=Join-Path $root ('json\'+$name+'.json')
  New-Item -ItemType Directory -Force (Split-Path -Parent $raw),(Split-Path -Parent $json)|Out-Null
  if(Test-Path -LiteralPath $raw){if((Get-FileHash -LiteralPath $raw).Hash -ne $hash){throw 'Changed official source'}}else{[IO.File]::WriteAllBytes($raw,$bytes)}
  $errorText=$null;$jsonHash=$null
  if(-not (Test-Path -LiteralPath $json)){
   try{Export-Cr2wJson (Read-Cr2wFile $raw) $json}catch{$errorText=$_.Exception.Message}
  }
  if(Test-Path -LiteralPath $json){$jsonHash=(Get-FileHash -LiteralPath $json).Hash}
  $inventory+=,[ordered]@{resource=$name;archive=$item.archive;raw_sha256=$hash;json_sha256=$jsonHash;decode_error=$errorText}
 }finally{$m.Dispose()}
}
$target=Join-Path $root 'inventory.json';$data=$inventory|ConvertTo-Json -Depth 8
if(Test-Path -LiteralPath $target){if([IO.File]::ReadAllText($target) -ne $data){throw 'Preserve existing inventory; use separate revision'}}else{[IO.File]::WriteAllText($target,$data,[Text.UTF8Encoding]::new($false))}
[ordered]@{resources=$inventory.Count;decode_gaps=@($inventory|Where-Object {$null -ne $_.decode_error}).Count;game_writes=0;direct_save_writes=0}|ConvertTo-Json
