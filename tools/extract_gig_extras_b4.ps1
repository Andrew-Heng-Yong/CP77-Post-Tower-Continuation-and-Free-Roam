param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -HelpersOnly
$root=Join-Path $WorkspaceRoot 'research\gig_restoration\batch_b4\extras'
$wanted=@(
 'base\open_world\street_stories\santo_domingo\rancho_corronado\sts_std_rcr_02\scenes\sts_std_rcr_02_scene.scene',
 'base\open_world\vendors\heywood\wellsprings\hey_spr_junk_01\hey_spr_junk_01.scene',
 'base\open_world\vendors\westbrook\charter_hill\wbr_hil_foodshop_02\wbr_hil_foodshop_02.scene',
 'base\open_world\voicesets\sts_characters\vset_anna_hamill.scene'
)
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$chosen=@{}
foreach($archivePath in @('C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc\content\basegame_4_gamedata.archive','C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc\ep1\ep1_2_gamedata.archive')){
 $archive=$null
 if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archivePath,$hs,[ref]$archive).ToString() -ne 'NoError'){throw 'Native archive read failed'}
 foreach($entry in $archive.Files.Values){if($entry.Name -in $wanted){$chosen[$entry.Name]=@{entry=$entry;archive=$archivePath}}}
}
$inventory=@()
foreach($name in $wanted){
 if(-not $chosen.ContainsKey($name)){$inventory+=,[ordered]@{resource=$name;missing=$true};continue}
 $item=$chosen[$name];$m=[IO.MemoryStream]::new()
 try{
  $item.entry.Extract($m);$bytes=$m.ToArray();$hash=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))
  $raw=Join-Path $root ('raw\'+$name);$json=Join-Path $root ('json\'+$name+'.json')
  New-Item -ItemType Directory -Force (Split-Path -Parent $raw),(Split-Path -Parent $json)|Out-Null
  if(Test-Path -LiteralPath $raw){if((Get-FileHash -LiteralPath $raw).Hash -ne $hash){throw 'Changed source'}}else{[IO.File]::WriteAllBytes($raw,$bytes)}
  if(-not (Test-Path -LiteralPath $json)){Export-Cr2wJson (Read-Cr2wFile $raw) $json}
  $inventory+=,[ordered]@{resource=$name;archive=$item.archive;raw_sha256=$hash;json_sha256=(Get-FileHash -LiteralPath $json).Hash}
 }finally{$m.Dispose()}
}
$target=Join-Path $root 'inventory.json';$data=$inventory|ConvertTo-Json -Depth 8
if(Test-Path -LiteralPath $target){if([IO.File]::ReadAllText($target) -ne $data){throw 'Inventory changed'}}else{[IO.File]::WriteAllText($target,$data,[Text.UTF8Encoding]::new($false))}
$inventory|Select-Object resource,missing|ConvertTo-Json
