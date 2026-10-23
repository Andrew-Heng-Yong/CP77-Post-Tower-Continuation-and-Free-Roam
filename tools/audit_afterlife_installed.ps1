param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),[string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$out=Join-Path $WorkspaceRoot 'research\afterlife_world';New-Item -ItemType Directory -Force $out|Out-Null
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$resources=[Collections.Generic.List[object]]::new();$matches=[Collections.Generic.List[object]]::new();$archives=[Collections.Generic.List[object]]::new()
$needles=@('afterlife','rogue','emmerick','emrick','holo_danc','hologram','dancing_holo')
foreach($file in Get-ChildItem -LiteralPath (Join-Path $GameRoot 'archive\pc\mod') -File -Filter '*.archive'){
 $arc=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($file.FullName,$hs,[ref]$arc).ToString() -ne 'NoError'){throw ('Cannot read '+$file.Name)}
 $project=$file.Name.StartsWith('TowerContinued')
 $archives.Add([ordered]@{name=$file.Name;project=$project;sha256=(Get-FileHash -LiteralPath $file.FullName).Hash;resources=$arc.Files.Count})
 foreach($entry in $arc.Files.Values){
  $resources.Add([ordered]@{archive=$file.Name;depot=$entry.Name;project=$project})
  if(-not $project){continue}
  $ms=[IO.MemoryStream]::new()
  try{
   $entry.Extract($ms);$bytes=$ms.ToArray();$content=[Text.Encoding]::UTF8.GetString($bytes)
   $hits=@($needles|Where-Object {$content.Contains($_,[StringComparison]::OrdinalIgnoreCase) -or $entry.Name.Contains($_,[StringComparison]::OrdinalIgnoreCase)})
   if($hits.Count){$matches.Add([ordered]@{archive=$file.Name;depot=$entry.Name;matched_strings=$hits;sha256=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))})}
  }finally{$ms.Dispose()}
 }
}
$report=[ordered]@{status='READ_ONLY_INSTALLED_ARCHIVE_INVENTORY';utc=[DateTime]::UtcNow.ToString('o');archives=@($archives);resources=@($resources);afterlife_string_matches=@($matches);limitations=@('String matches identify candidate resources, not reachable native behavior.','Game files do not encode one particular save runtime; original owners and recorded save facts must be interpreted separately.')}
[IO.File]::WriteAllText((Join-Path $out 'installed_archive_inventory.json'),($report|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
[pscustomobject]@{archives=$archives.Count;project_archives=@($archives|Where-Object project).Count;resources=$resources.Count;project_matching_payloads=$matches.Count;matches=@($matches)}|ConvertTo-Json -Depth 6
