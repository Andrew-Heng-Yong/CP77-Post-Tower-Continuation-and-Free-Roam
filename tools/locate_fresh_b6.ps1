param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -HelpersOnly
$out=Join-Path $WorkspaceRoot 'research\gig_restoration\fresh_b6\world_lookup.json'
if(Test-Path $out){throw 'Preserve existing lookup evidence'}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$rows=[Collections.Generic.List[object]]::new()
$arc=$null;$rel='content\basegame_3_nightcity.archive'
$path=Join-Path 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc' $rel
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($path,$hs,[ref]$arc).ToString() -ne 'NoError'){throw 'Official archive read failed'}
$scanned=0
foreach($entry in $arc.Files.Values){
 if($entry.Extension -ne '.streamingsector'){continue}
 $s=[IO.MemoryStream]::new()
 try{
  $entry.Extract($s);$scanned++;$bytes=$s.ToArray();$txt=[Text.Encoding]::UTF8.GetString($bytes)
  if(-not ($txt.Contains('hil_01',[StringComparison]::Ordinal) -or $txt.Contains('jpn_02',[StringComparison]::Ordinal))){continue}
  $s.Position=0;$file=$null;$reader=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($s)
  try{
   if($reader.ReadFile([ref]$file,$true).ToString() -ne 'NoError'){throw 'Strict sector decode failed'}
   foreach($d in $file.RootChunk.NodeData.Data){
    $reference=$d.QuestPrefabRefHash.ToString()
    if(-not ($reference.Contains('hil_01',[StringComparison]::Ordinal) -or $reference.Contains('jpn_02',[StringComparison]::Ordinal))){continue}
    $idx=[int]$d.NodeIndex.ToString();$n=$file.RootChunk.Nodes[$idx].Chunk
    $rows.Add([ordered]@{archive=$rel;sector=$entry.Name;index=$idx;type=$n.GetType().Name;reference=$reference;x=[double]$d.Position.X.ToString();y=[double]$d.Position.Y.ToString();z=[double]$d.Position.Z.ToString()})
   }
  }catch{$rows.Add([ordered]@{archive=$rel;sector=$entry.Name;decode_error=$_.Exception.Message})}
 }finally{$s.Dispose()}
}
[IO.File]::WriteAllText($out,(ConvertTo-Json -InputObject $rows.ToArray() -Depth 6),[Text.UTF8Encoding]::new($false))
[pscustomobject]@{scanned=$scanned;rows=$rows.Count;output=$out}|ConvertTo-Json
$rows|Where-Object {$_.Contains('reference') -and $_.reference -match 'tr_building$|tr_quest$|tr_start$|wp_start$'}|ConvertTo-Json -Depth 5
