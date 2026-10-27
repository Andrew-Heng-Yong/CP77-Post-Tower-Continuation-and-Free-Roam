Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$proofPath=Join-Path $PSScriptRoot 'candidate_01/package_proof_01.json'
$proof=Get-Content -LiteralPath $proofPath -Raw|ConvertFrom-Json -Depth 80
if($proof.status -cne 'FULL_51_PATH_W2_CANDIDATE_PACKED_NOT_INSTALLED' -or $proof.new_resources.Count -ne 10){throw 'Candidate proof changed'}
$out=Join-Path $PSScriptRoot 'candidate_02/collisions_01.json'
if(Test-Path -LiteralPath $out){throw 'Preserve collision evidence'}
$wanted=@{}
foreach($r in $proof.new_resources){$key=[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString([string]$r.resource).ToString();if($wanted.ContainsKey($key)){throw 'Hash collision among new resources'};$wanted[$key]=$r.resource}
$mod='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc\mod'
$archives=@(Get-ChildItem -LiteralPath $mod -Filter '*.archive' -File|Sort-Object Name)
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$hits=[Collections.Generic.List[object]]::new()
foreach($f in $archives){
 $arc=$null
 if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($f.FullName,$hs,[ref]$arc).ToString() -cne 'NoError'){throw "Unreadable installed archive $($f.FullName)"}
 foreach($e in $arc.Files.Values){$key=$e.Key.ToString();if($wanted.ContainsKey($key)){$hits.Add([ordered]@{archive=$f.Name;depot=$e.Name;expected=$wanted[$key]})}}
}
$expected=@($hits|Where-Object {$_.archive -ceq 'zzzz_PTFR_WW1_Prototype.archive' -and $_.depot -ceq 'towercontinued\world_workspots_ww1\ce_pac_cvi_116_owner.questphase'})
$unexpected=@($hits|Where-Object {$_.archive -cne 'zzzz_PTFR_WW1_Prototype.archive' -or $_.depot -cne 'towercontinued\world_workspots_ww1\ce_pac_cvi_116_owner.questphase'})
$result=[ordered]@{status=if($expected.Count -eq 1 -and !$unexpected.Count){'PASS_EXPECTED_PROBE_COLLISION_ONLY'}else{'REVIEW_REQUIRED'};archives=$archives.Count;new_resources=$wanted.Count;expected_probe_hits=$expected.Count;unexpected_hits=$unexpected.Count;hits=@($hits);game_writes=0}
[IO.File]::WriteAllText($out,($result|ConvertTo-Json -Depth 20)+"`n",[Text.UTF8Encoding]::new($false))
@{status=$result.status;archives=$result.archives;unexpected=$result.unexpected_hits}|ConvertTo-Json
if($result.status -cne 'PASS_EXPECTED_PROBE_COLLISION_ONLY'){throw 'New resource collisions require review'}
