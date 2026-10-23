param([string[]]$Strings=@('q307_city_scenes'),[string]$Output='research/phase2b_p4/extra_world_variant_referrers.json')
$ErrorActionPreference='Stop'
$wkPhysical='C:\Users\Ayong\Documents\WolvenKit-8.20.0'
foreach($a in @('WolvenKit.Core.dll','WolvenKit.Common.dll','WolvenKit.RED4.dll')){[void][Reflection.Assembly]::LoadFrom((Join-Path $wkPhysical $a))}
$hsPhysical=[WolvenKit.Common.Services.HashService]::new();$hsPhysical.Load()
$rootPhysical='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc'
$rowsPhysical=[Collections.Generic.List[object]]::new();$countsPhysical=@{}
foreach($rel in @('content/basegame_4_gamedata.archive','ep1/ep1_2_gamedata.archive')){
 $archivePath=Join-Path $rootPhysical $rel;$arc=$null
 [void]([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archivePath,$hsPhysical,[ref]$arc)
 $entries=@($arc.Files.Values|Where-Object{$_.Extension-in @('.quest','.questphase','.scene','.gamedef')})
 $countsPhysical[$rel]=$entries.Count
 foreach($entry in $entries){$stream=[IO.MemoryStream]::new();try{
  $entry.Extract($stream);$content=[Text.Encoding]::UTF8.GetString($stream.ToArray())
  foreach($s in $Strings){if($content.Contains($s,[StringComparison]::Ordinal)){$rowsPhysical.Add([pscustomobject]@{String=$s;Resource=$entry.Name;Archive=$archivePath})}}
 }finally{$stream.Dispose()}}
}
@{Counts=$countsPhysical;Matches=$rowsPhysical}|ConvertTo-Json -Depth 5|Set-Content -LiteralPath $Output -Encoding utf8NoBOM
$rowsPhysical|ConvertTo-Json -Depth 4
