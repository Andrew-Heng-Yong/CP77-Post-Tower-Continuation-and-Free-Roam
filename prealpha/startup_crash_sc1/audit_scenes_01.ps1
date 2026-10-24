$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$W=Split-Path -Parent (Split-Path -Parent $PSScriptRoot);$out=Join-Path $PSScriptRoot 'candidate_01/scene_audit_01'
if(Test-Path $out){throw 'Use successor output'}
New-Item -ItemType Directory -Path $out|Out-Null
. (Join-Path $W 'tools/build_phase2a.ps1') -WorkspaceRoot $W -HelpersOnly -WolvenKitRoot (Join-Path $W 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$rows=@();$archives=@()
foreach($f in Get-ChildItem -LiteralPath 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc\mod' -File -Filter '*TowerContinued*.archive') {
 $arc=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($f.FullName,$hs,[ref]$arc).ToString() -ne 'NoError'){throw 'Archive read failed'}
 $archives+=@{path=$f.FullName;sha256=(Get-FileHash -LiteralPath $f.FullName).Hash;resources=$arc.Files.Count}
 foreach($e in $arc.Files.Values){
  if(!$e.Name.EndsWith('.scene')){continue}
  $ms=[IO.MemoryStream]::new();try{$e.Extract($ms);$bytes=$ms.ToArray()}finally{$ms.Dispose()}
  $temp=Join-Path $out 'current.scene';[IO.File]::WriteAllBytes($temp,$bytes);$res=Read-Cr2wFile $temp;$r=$res.RootChunk
  $ai=@($r.Actors|ForEach-Object {[uint32]$_.ActorId.Id});$pi=@($r.PlayerActors|ForEach-Object {[uint32]$_.ActorId.Id});$ids=@($ai)+@($pi);$dense=$true
  for($i=0;$i -lt $ids.Count;$i++){if($ids[$i] -ne $i){$dense=$false}}
  $row=@{archive=$f.Name;depot=$e.Name;sha256=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes));actors=$ai;players=$pi;dense=$dense}
  if(!$dense){$dest=Join-Path $out ('bad/'+$e.Name);New-Item -ItemType Directory -Force -Path (Split-Path $dest -Parent)|Out-Null;[IO.File]::WriteAllBytes($dest,$bytes);Export-Cr2wJson $res ($dest+'.json');$row.raw=$dest}
  $rows+=$row
 }
}
$result=@{status='READ_ONLY_ACTOR_INDEX_AUDIT';archives=$archives;scenes=$rows;count=$rows.Count;non_dense=@($rows|Where-Object {!$_.dense})}
$result|ConvertTo-Json -Depth 10|Set-Content -LiteralPath (Join-Path $out 'audit.json') -Encoding utf8
@{count=$rows.Count;bad=$result.non_dense}|ConvertTo-Json -Depth 8
