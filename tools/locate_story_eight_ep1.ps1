param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$arc=$null
$archive='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc\ep1\ep1_1_nightcity.archive'
[void]([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$arc)
$handler=[WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($e)return ($e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs])}
$rows=[Collections.Generic.List[object]]::new();$count=0
foreach($entry in $arc.Files.Values){
 if($entry.Extension -ne '.streamingsector'){continue}
 $m=[IO.MemoryStream]::new()
 try{
  $entry.Extract($m);$bytes=$m.ToArray();$text=[Text.Encoding]::UTF8.GetString($bytes);$count++
  if(-not ($text.Contains('wst_ep1_11') -or $text.Contains('ronald_area_02'))){continue}
  $hash=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes));$m.Position=0
  $file=$null;$reader=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($m);$reader.add_ParsingError($handler)
  if($reader.ReadFile([ref]$file,$true).ToString() -ne 'NoError'){throw 'Decode failed'}
  foreach($d in $file.RootChunk.NodeData.Data){
   $ref=$d.QuestPrefabRefHash.ToString();$idx=[int]$d.NodeIndex.ToString();$n=$file.RootChunk.Nodes[$idx].Chunk
   $name=$n.DebugName.ToString()
   if(($ref+' '+$name) -notmatch 'wst_ep1_11|bill_default|ronald_area_02'){continue}
   $rows.Add([pscustomobject]@{sector=$entry.Name;sha256=$hash;reference=$ref;name=$name;node_type=$n.GetType().Name;x=[double]$d.Position.X.ToString();y=[double]$d.Position.Y.ToString();z=[double]$d.Position.Z.ToString()})
  }
 }finally{$m.Dispose()}
}
$path=Join-Path $WorkspaceRoot 'research\b0_story_eight\ep1_location_evidence.json'
[IO.File]::WriteAllText($path,(ConvertTo-Json -InputObject @($rows.ToArray()) -Depth 5))
"Scanned $count sectors; matched $($rows.Count) nodes"
$rows | Where-Object { $_.reference -match '#wst_ep1_11_bill_met$|#q302_tr_ronald_area_02$|#wst_ep1_11_bill_com$' } | Format-Table reference,x,y,z
