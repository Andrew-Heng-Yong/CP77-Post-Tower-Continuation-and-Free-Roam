param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -HelpersOnly
$root=Join-Path $WorkspaceRoot 'research\activity_batches_b1\gig_sources'
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$archive=$null
$archivePath='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc\content\basegame_4_gamedata.archive'
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archivePath,$hs,[ref]$archive).ToString() -ne 'NoError'){throw 'Native archive read failed'}
$entries=@($archive.Files.Values|Where-Object {
 ($_.Name -match '^base\\open_world\\street_stories\\watson\\northside_industrial_district\\sts_wat_nid_05\\' -or
  $_.Name -match '^base\\open_world\\street_stories\\watson\\kabuki\\sts_wat_kab_(101|102|107)\\') -and
 $_.Extension -in @('.scene','.community') -and $_.Name -notmatch '\\(test|versions)\\'
}|Sort-Object Name)
if($entries.Count -lt 9){throw 'Missing expected selected scenes'}
$inventory=@()
foreach($entry in $entries){
 $raw=Join-Path $root ('raw\'+$entry.Name);$json=Join-Path $root ('json\'+$entry.Name+'.json')
 New-Item -ItemType Directory -Force (Split-Path -Parent $raw),(Split-Path -Parent $json)|Out-Null
 $m=[IO.MemoryStream]::new()
 try{
  $entry.Extract($m);$bytes=$m.ToArray();$hash=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))
  if(Test-Path -LiteralPath $raw){
   if((Get-FileHash -LiteralPath $raw).Hash -ne $hash){throw 'Changed source; preserve B1 evidence'}
  }else{[IO.File]::WriteAllBytes($raw,$bytes)}
  $decodeError=$null;$jsonHash=$null
  if(-not (Test-Path -LiteralPath $json)){
   try{Export-Cr2wJson (Read-Cr2wFile $raw) $json}
   catch{
    # Preserve the undecoded native bytes and make the gap explicit. Never
    # bypass a reader validation error or treat this as empty community data.
    if($_.Exception.Message -notlike '*Invalid default val for*communityCommunityTemplateData.entries*'){throw}
    $decodeError='WolvenKit 8.20.0: Invalid default val for communityCommunityTemplateData.entries'
   }
  }
  if(Test-Path -LiteralPath $json){$jsonHash=(Get-FileHash -LiteralPath $json).Hash}
  $inventory+=,[ordered]@{resource=$entry.Name;archive=$archivePath;raw_sha256=$hash;json_sha256=$jsonHash;decode_error=$decodeError}
 }finally{$m.Dispose()}
}
$inventoryPath=Join-Path $root 'inventory.json';$data=($inventory|ConvertTo-Json -Depth 6)
if(Test-Path -LiteralPath $inventoryPath){
 if([IO.File]::ReadAllText($inventoryPath) -ne $data){throw 'Changed inventory; preserve B1 evidence'}
}else{[IO.File]::WriteAllText($inventoryPath,$data,[Text.UTF8Encoding]::new($false))}
[ordered]@{extracted=$entries.Count;decode_gaps=@($inventory|Where-Object {$null -ne $_.decode_error}).Count;game_writes=0;save_writes=0;inventory=$inventoryPath}|ConvertTo-Json
