Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$wk=Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package'
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot $wk

function ReadJournalMetadata([string]$raw){
 $script:IgnoredJournalEnums=[Collections.Generic.List[object]]::new();$stream=[IO.File]::OpenRead($raw)
 try{
  $reader=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($stream)
  $reader.add_ParsingError([WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($e)
   if($e -is [WolvenKit.RED4.Types.InvalidEnumValueEventArgs] -and $e.EnumType -eq [WolvenKit.RED4.Types.Enums+gamedataMappinVariant] -and $e.StringValue -cin @('Zzz22_CityTourLandmark','Zzz21_ServicePointGlamdocVariant')){
    $script:IgnoredJournalEnums.Add(@{enum_type=$e.EnumType.FullName;original=$e.StringValue;metadata_placeholder=0;position=$reader.Position});$e.Value=[Enum]::ToObject($e.EnumType,0);return $true
   }
   throw ('Unapproved journal metadata parse event '+$e.GetType().FullName)
  })
  $file=$null;$result=$reader.ReadFile([ref]$file,$true);if($result.ToString() -cne 'NoError'){throw 'Journal metadata read failed'};return $file
 }finally{$stream.Dispose()}
}

$out=Join-Path $ws 'research/sidejobs_s28/journal_variants_05';if(Test-Path -LiteralPath $out){throw 'Immutable journal extraction exists'};New-Item -ItemType Directory $out|Out-Null
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$keys=@{};foreach($dep in @('base\journal\cooked_journal.journal','ep1\journal\cooked_journal.journal')){$keys[$dep]=[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($dep)}
$game='C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077/archive/pc';$files=@(Get-ChildItem -LiteralPath (Join-Path $game 'content') -File -Filter '*.archive')+@(Get-ChildItem -LiteralPath (Join-Path $game 'ep1') -File -Filter '*.archive');$rows=@();$archives=@()
foreach($file in $files){
 $arc=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($file.FullName,$hs,[ref]$arc).ToString() -cne 'NoError'){throw 'Official archive read failed'};$used=$false
 foreach($dep in $keys.Keys){
  if(!$arc.Files.ContainsKey($keys[$dep])){continue};$used=$true;$raw=Join-Path $out ($file.BaseName+'/raw/'+$dep);$json=Join-Path $out ($file.BaseName+'/json/'+$dep+'.json');New-Item -ItemType Directory -Force (Split-Path $raw),(Split-Path $json)|Out-Null
  $m=[IO.MemoryStream]::new();try{$arc.Files[$keys[$dep]].Extract($m);[IO.File]::WriteAllBytes($raw,$m.ToArray())}finally{$m.Dispose()};Export-Cr2wJson (ReadJournalMetadata $raw) $json
  $rows+=,@{depot=$dep;archive=$file.FullName;raw=[IO.Path]::GetRelativePath($ws,$raw).Replace('\','/');json=[IO.Path]::GetRelativePath($ws,$json).Replace('\','/');sha256=(Get-FileHash -LiteralPath $raw).Hash;json_sha256=(Get-FileHash -LiteralPath $json).Hash;ignored_enums=$script:IgnoredJournalEnums.ToArray();metadata_only=$true}
 }
 if($used){$archives+=,@{path=$file.FullName;length=$file.Length;last_write_utc=$file.LastWriteTimeUtc.ToString('o');sha256=(Get-FileHash -LiteralPath $file.FullName).Hash}}
}
foreach($dep in $keys.Keys){if(@($rows|Where-Object {$_.depot -ceq $dep}).Count -eq 0){throw ('Missing journal '+$dep)}}
$base=@($rows|Where-Object {$_.depot -ceq 'base\journal\cooked_journal.journal'});$ep1=@($rows|Where-Object {$_.depot -ceq 'ep1\journal\cooked_journal.journal'})
$result=[ordered]@{status='EXTRACTED_CURRENT_JOURNAL_PATH_CLASS_METADATA_ONLY';source=$base[0].raw;source_sha256=$base[0].sha256;depot='base\journal\cooked_journal.journal';variants=$base;ep1_variants=$ep1;archives=$archives;script='prealpha/sidejobs_s28/extract_journals_05.ps1';script_sha256=(Get-FileHash $PSCommandPath).Hash;tool_sha256=(Get-FileHash (Join-Path $wk 'WolvenKit.RED4.dll')).Hash;game_writes=0;save_writes=0;scope='Only path/class/tree metadata is authoritative. Two exact unknown mappin enum names decode using numeric0 placeholders; occurrence records retained. All other parsing events reject. Raw resources remain byte-exact; no full journal payload comparison, packing or override allowed.'}
[IO.File]::WriteAllText((Join-Path $out 'extraction.json'),($result|ConvertTo-Json -Depth 40),[Text.UTF8Encoding]::new($false));@{base_variants=$base.Count;ep1_variants=$ep1.Count;source=$result.source}|ConvertTo-Json
