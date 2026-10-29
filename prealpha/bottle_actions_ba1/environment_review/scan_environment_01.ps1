$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
$out=Join-Path $PSScriptRoot 'scan_02'
if(Test-Path -LiteralPath $out){throw 'Preserve existing evidence'}
[void][IO.Directory]::CreateDirectory($out)
$wk=Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package'
foreach($n in @('WolvenKit.Core.dll','WolvenKit.Common.dll','WolvenKit.RED4.dll')){[void][Reflection.Assembly]::LoadFrom((Join-Path $wk $n))}
Add-Type -TypeDefinition @'
public static class BAEnvMatch01 {
 public static bool Contains(byte[] data, byte[] find) {
  for(int i=0;i<=data.Length-find.Length;i++) {
   if(data[i]!=find[0]) continue;
   int k=1;while(k<find.Length && data[i+k]==find[k]) k++;
   if(k==find.Length)return true;
  }
  return false;
 }
}
'@
$prefix='$/03_night_city/c_pacifica/coastview/cvi_ce_prefabMZQN2IY/cs_goons_shooting_env_002_prefabBCFE3FQ/'
$refs=@('target_object_prefabG6AJLQI','target_object_001_prefabG6AJLQI','cs_goons_shooting_sec_area' | ForEach-Object {$prefix+$_})
$refs|ForEach-Object {Write-Output $_}
$needles=@();foreach($ref in $refs){$hash=[WolvenKit.RED4.Types.NodeRef]::CalculateHash($ref);$needles+=@{ref=$ref;hash=$hash.ToString();bytes=[BitConverter]::GetBytes([uint64]$hash)}}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$game='C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077'
$archives=@('archive/pc/content/basegame_3_nightcity.archive','archive/pc/ep1/ep1_1_nightcity.archive')
$matches=[Collections.Generic.List[object]]::new();$count=0
foreach($rel in $archives){
 $ap=Join-Path $game $rel;$a=$null
 if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($ap,$hs,[ref]$a).ToString() -ne 'NoError'){throw "Archive failed $rel"}
 foreach($e in $a.Files.Values){
  if($e.Extension -ne '.streamingsector'){continue}
  $ms=[IO.MemoryStream]::new()
  try{
   $e.Extract($ms);$bytes=$ms.ToArray();$count++
   $found=@($needles|Where-Object {[BAEnvMatch01]::Contains($bytes,$_.bytes)})
   if($found.Count){
    $raw=Join-Path $out (([IO.Path]::GetFileNameWithoutExtension($ap))+'_'+$e.Key+'.streamingsector')
    [IO.File]::WriteAllBytes($raw,$bytes)
    $matches.Add([pscustomobject]@{archive=$rel;resource=$e.Name;raw=$raw;sha256=(Get-FileHash -LiteralPath $raw).Hash;refs=@($found|ForEach-Object {$_.ref})})
    Write-Output "MATCH $rel $($e.Name) refs=$($found.Count)"
   }
   if(($count % 10000) -eq 0){Write-Output "Scanned $count"}
  }finally{$ms.Dispose()}
 }
}
$report=@{status='READ_ONLY_REFERENCE_HASH_SCAN_NOT_YET_OWNERSHIP_PROOF';count=$count;needles=@($needles|ForEach-Object {@{ref=$_.ref;hash=$_.hash}});matches=@($matches.ToArray());game_writes=0;save_writes=0}
[IO.File]::WriteAllText((Join-Path $out 'report_01.json'),($report|ConvertTo-Json -Depth 9)+"`n",[Text.UTF8Encoding]::new($false))
Write-Output "Done $count sectors, $($matches.Count) matches"
