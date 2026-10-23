Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
$wk=Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package'
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot $wk
$out=Join-Path $ws 'research/housing_h1/purchase/panam_world_01'
if(Test-Path -LiteralPath $out){throw 'Immutable output exists'}
New-Item -ItemType Directory $out|Out-Null
Add-Type -TypeDefinition @'
public static class H1PanamByteLookup {
 public static bool Has(byte[] data, ulong value) {
  var bytes=System.BitConverter.GetBytes(value);
  for(int i=0;i<=data.Length-8;i++) {
   if(data[i]!=bytes[0] || data[i+1]!=bytes[1]) continue;
   int j=2;for(;j<8;j++) if(data[i+j]!=bytes[j]) break;
   if(j==8)return true;
  }
  return false;
 }
}
'@
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$rows=[Collections.Generic.List[object]]::new();$archives=[Collections.Generic.List[object]]::new()
$handler=[WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($e) return ($e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs])}
foreach($rel in @('content/basegame_3_nightcity.archive','ep1/ep1_1_nightcity.archive')) {
 $path=Join-Path 'C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077/archive/pc' $rel
 $before=Get-Item -LiteralPath $path;$hash=(Get-FileHash -LiteralPath $path).Hash
 $arc=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($path,$hs,[ref]$arc).ToString() -ne 'NoError'){throw 'Archive read failed'}
 $scanned=0;$matches=0
 foreach($entry in $arc.Files.Values) {
  if($entry.Extension -ne '.streamingsector'){continue}
  $memory=[IO.MemoryStream]::new()
  try {
   $entry.Extract($memory);$bytes=$memory.ToArray();$scanned++
   $txt=[Text.Encoding]::UTF8.GetString($bytes)
   $named=$txt.Contains('nomad_camp_02_stash',[StringComparison]::OrdinalIgnoreCase) -or $txt.Contains('nomad_camp_01_stash',[StringComparison]::OrdinalIgnoreCase)
   $hashed=[H1PanamByteLookup]::Has($bytes,[uint64]13923238736166076723)
   if(-not($named -or $hashed)){continue};$matches++
   $row=@{archive=$path;archive_sha256=$hash;depot=$entry.Name;named_match=$named;node_id_match=$hashed;raw_sha256=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes));parsed=$false}
   if($entry.Name -like '*always_loaded*'){$row.existing_registry=$true;$rows.Add($row);continue}
   $stem=[IO.Path]::GetFileNameWithoutExtension($rel)+'_'+[IO.Path]::GetFileName($entry.Name)
   $raw=Join-Path $out ($stem);$json=$raw+'.json';[IO.File]::WriteAllBytes($raw,$bytes)
   $row.raw=[IO.Path]::GetRelativePath($ws,$raw).Replace('\','/')
   try {
    $memory.Position=0;$file=$null;$reader=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($memory);$reader.add_ParsingError($handler)
    if($reader.ReadFile([ref]$file,$true).ToString() -ne 'NoError'){throw 'Sector parse failed'}
    Export-Cr2wJson $file $json;$row.parsed=$true;$row.json=[IO.Path]::GetRelativePath($ws,$json).Replace('\','/');$row.json_sha256=(Get-FileHash -LiteralPath $json).Hash
   } catch {$row.error=$_.Exception.Message}
   $rows.Add($row)
  } finally {$memory.Dispose()}
 }
 $after=Get-Item -LiteralPath $path
 if($before.Length -ne $after.Length -or $before.LastWriteTimeUtc -ne $after.LastWriteTimeUtc){throw 'Archive changed during lookup'}
 $archives.Add(@{path=$path;sha256=$hash;scanned=$scanned;matched=$matches;length=$after.Length;last_write_utc=$after.LastWriteTimeUtc.ToString('o')})
 Write-Output "$rel scanned=$scanned matched=$matches"
}
$proof=@{status='CURRENT_TARGETED_PANAM_STASH_LOOKUP';rows=$rows.ToArray();archives=$archives.ToArray();extractor_sha256=(Get-FileHash $PSCommandPath).Hash;tool_sha256=(Get-FileHash (Join-Path $wk 'WolvenKit.RED4.dll')).Hash;game_writes=0}
[IO.File]::WriteAllText((Join-Path $out 'inventory.json'),($proof|ConvertTo-Json -Depth 20),[Text.UTF8Encoding]::new($false))
