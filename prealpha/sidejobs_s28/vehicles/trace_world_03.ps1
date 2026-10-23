param([string]$Revision='world_03')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
$wk=Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package'
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot $wk
$out=Join-Path $ws ('research/sidejobs_s28/vehicles/'+$Revision)
if(Test-Path -LiteralPath $out){throw 'Immutable output exists'}
New-Item -ItemType Directory $out,(Join-Path $out 'raw'),(Join-Path $out 'json')|Out-Null
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$rows=[Collections.Generic.List[object]]::new();$errors=[Collections.Generic.List[object]]::new();$archives=[Collections.Generic.List[object]]::new()
$handler=[WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($e) return ($e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs])}
foreach($rel in @('content/basegame_3_nightcity.archive','ep1/ep1_1_nightcity.archive')){
 $path=Join-Path 'C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077/archive/pc' $rel;$arc=$null
 $before=Get-Item -LiteralPath $path
 if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($path,$hs,[ref]$arc).ToString() -ne 'NoError'){throw 'Archive read failed'}
 $scanned=0;$matches=0
 foreach($entry in $arc.Files.Values){
  if($entry.Extension -ne '.streamingsector'){continue}
  $stream=[IO.MemoryStream]::new()
  try{
   try{$entry.Extract($stream)}catch{$errors.Add(@{archive=$path;depot=$entry.Name;stage='extract';error=$_.Exception.Message});continue}
   $scanned++;$bytes=$stream.ToArray();$txt=[Text.Encoding]::UTF8.GetString($bytes)
   if(-not ($txt.Contains('mq029',[StringComparison]::OrdinalIgnoreCase) -or $txt.Contains('mq050',[StringComparison]::OrdinalIgnoreCase))){continue}
   $matches++;$stem=[IO.Path]::GetFileNameWithoutExtension($rel)+'_'+[IO.Path]::GetFileName($entry.Name)
   $raw=Join-Path $out ('raw/'+$stem);$json=Join-Path $out ('json/'+$stem+'.json')
   [IO.File]::WriteAllBytes($raw,$bytes)
   $row=@{archive=$path;depot=$entry.Name;raw=[IO.Path]::GetRelativePath($ws,$raw).Replace('\','/');raw_sha256=(Get-FileHash -LiteralPath $raw).Hash;parsed=$false}
   try{
    $stream.Position=0;$file=$null;$reader=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($stream);$reader.add_ParsingError($handler)
    if($reader.ReadFile([ref]$file,$true).ToString() -ne 'NoError'){throw 'Sector parse failed'}
    Export-Cr2wJson $file $json
    $row.parsed=$true;$row.json=[IO.Path]::GetRelativePath($ws,$json).Replace('\','/');$row.json_sha256=(Get-FileHash -LiteralPath $json).Hash
   }catch{$errors.Add(@{archive=$path;depot=$entry.Name;stage='parse';error=$_.Exception.Message})}
   $rows.Add($row)
  }finally{$stream.Dispose()}
 }
 $after=Get-Item -LiteralPath $path
 if($before.Length -ne $after.Length -or $before.LastWriteTimeUtc -ne $after.LastWriteTimeUtc){throw 'Archive changed during scan'}
 $archives.Add(@{path=$path;length=$after.Length;last_write_utc=$after.LastWriteTimeUtc.ToString('o');scanned=$scanned;matched=$matches})
 Write-Output "$rel scanned=$scanned matched=$matches errors=$($errors.Count)"
}
$result=@{status='READ_ONLY_WORLD_NODE_SOURCE_LOOKUP';rows=$rows.ToArray();errors=$errors.ToArray();archives=$archives.ToArray();tool_root=$wk;tool_sha256=(Get-FileHash -LiteralPath (Join-Path $wk 'WolvenKit.RED4.dll')).Hash;script_sha256=(Get-FileHash -LiteralPath $PSCommandPath).Hash;game_writes=0;save_writes=0}
[IO.File]::WriteAllText((Join-Path $out 'inventory.json'),($result|ConvertTo-Json -Depth 15),[Text.UTF8Encoding]::new($false))
