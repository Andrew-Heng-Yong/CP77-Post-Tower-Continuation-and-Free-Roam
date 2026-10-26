param([Parameter(Mandatory=$true)][string]$List,[Parameter(Mandatory=$true)][string]$Revision)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$out=Join-Path $ws ('research/sidejobs_s29/'+$Revision)
if(Test-Path -LiteralPath $out){throw 'Immutable extraction exists'}
New-Item -ItemType Directory $out|Out-Null
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$wanted=@(Get-Content -LiteralPath (Join-Path $ws $List) -Raw|ConvertFrom-Json)
$keys=@{};foreach($d in $wanted){$keys[$d]=[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($d)}
$game='C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077/archive/pc'
$rows=@()
$archives=@(Get-ChildItem -LiteralPath (Join-Path $game 'content') -Filter '*.archive' -File)+@(Get-ChildItem -LiteralPath (Join-Path $game 'ep1') -Filter '*.archive' -File)
foreach($archiveFile in $archives){
 $file=$archiveFile.FullName;$arc=$null
 if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($file,$hs,[ref]$arc).ToString() -cne 'NoError'){throw ('Unreadable archive '+$file)}
 foreach($dep in $wanted){
  if(!$arc.Files.ContainsKey($keys[$dep])){continue}
  $raw=Join-Path $out ([IO.Path]::GetFileNameWithoutExtension($file)+'/raw/'+$dep);$json=Join-Path $out ([IO.Path]::GetFileNameWithoutExtension($file)+'/json/'+$dep+'.json')
  New-Item -ItemType Directory -Force (Split-Path $raw),(Split-Path $json)|Out-Null
  $stream=[IO.File]::Create($raw);try{$arc.Files[$keys[$dep]].Extract($stream)}finally{$stream.Dispose()}
  Export-Cr2wJson (Read-Cr2wFile $raw) $json
  $rows+=,@{depot=$dep;archive=$file;raw=[IO.Path]::GetRelativePath($ws,$raw).Replace('\','/');json=[IO.Path]::GetRelativePath($ws,$json).Replace('\','/');sha256=(Get-FileHash $raw).Hash;json_sha256=(Get-FileHash $json).Hash}
 }
}
$missing=@($wanted|Where-Object {$_ -cnotin $rows.depot})
$result=[ordered]@{status='CURRENT_OFFICIAL_SOURCE_EXTRACTION';rows=$rows;missing=$missing;list=$List;list_sha256=(Get-FileHash (Join-Path $ws $List)).Hash;script_sha256=(Get-FileHash $PSCommandPath).Hash;game_writes=0;save_writes=0}
[IO.File]::WriteAllText((Join-Path $out 'inventory.json'),($result|ConvertTo-Json -Depth 30),[Text.UTF8Encoding]::new($false))
@{resources=$rows.Count;missing=$missing;output=$out}|ConvertTo-Json
if($missing.Count){throw 'Missing source resources recorded'}
