Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ws = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$sourcePath = Join-Path $PSScriptRoot 'native_validation_01.json'
$outPath = Join-Path $PSScriptRoot 'mismatch_resolution_01.json'
if (Test-Path -LiteralPath $outPath) { throw 'Preserve evidence; use successor' }
$validation = Get-Content -LiteralPath $sourcePath -Raw | ConvertFrom-Json -Depth 80
if ($validation.failed_count -ne 31) { throw 'Native mismatch count changed' }
$wanted = @{}
$rows = [Collections.Generic.List[object]]::new()
foreach ($f in $validation.failures) {
  $ref = $f.stored_refs[0]
  $hash = [WolvenKit.RED4.Types.NodeRef]::CalculateHash($ref)
  $key = 'quest_' + $hash.ToString('x16')
  $resource = 'base\worlds\03_night_city\_compiled\default\' + $key + '.streamingsector'
  $row = [ordered]@{id=$f.id; native_ref=$ref; hash=$hash.ToString();
    native_resource=$resource; matches=[Collections.Generic.List[object]]::new()}
  $rows.Add($row); $wanted[$resource] = $row
}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$archives=@((Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc/content') -Filter 'basegame_*.archive' -File|Sort-Object Name);(Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc/ep1') -Filter 'ep1_*.archive' -File|Sort-Object Name))
foreach($af in $archives){
  $a=$null
  if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($af.FullName,$hs,[ref]$a).ToString() -ne 'NoError'){throw "Archive read failed $($af.Name)"}
  foreach($e in $a.Files.Values){
    if($wanted.ContainsKey($e.Name)){
      $wanted[$e.Name].matches.Add([ordered]@{archive=$af.Name; domain=if($af.Name.StartsWith('ep1_')){'ep1'}else{'base'}; name=$e.Name})
    }
  }
}
$result=[ordered]@{status='READ_ONLY_EXACT_NATIVE_REF_LOOKUP';
  validation_sha256=(Get-FileHash -LiteralPath $sourcePath -Algorithm SHA256).Hash;
  count=$rows.Count; found=@($rows|Where-Object {$_.matches.Count -gt 0}).Count;
  rows=@($rows); game_writes=0; save_writes=0 }
[IO.File]::WriteAllText($outPath,($result|ConvertTo-Json -Depth 60)+"`n",[Text.UTF8Encoding]::new($false))
@{status=$result.status;count=$result.count;found=$result.found}|ConvertTo-Json
