Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$W=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$C=Join-Path $PSScriptRoot 'candidate_01';$b=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'baseline.json') -Raw|ConvertFrom-Json -Depth 100
. (Join-Path $W 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $W 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
function OpenArc($path){$r=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($path,$hs,[ref]$r).ToString() -ne 'NoError'){throw 'Unusable archive'};return $r}
function HashPayload($entry){$m=[IO.MemoryStream]::new();try{$entry.Extract($m);return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($m.ToArray()))}finally{$m.Dispose()}}
$p='archive/pc/mod/zzzz_PTFR_Combined.archive'
$old=OpenArc (Join-Path (Join-Path $b.candidate 'package') $p);$new=OpenArc (Join-Path (Join-Path $C 'package') $p)
if($old.Files.Count -ne $new.Files.Count){throw 'Member inventory changed'}
$rows=@()
foreach($key in $old.Files.Keys){
 if(-not $new.Files.ContainsKey($key)){throw 'Lost resource'}
 $a=HashPayload $old.Files[$key];$z=HashPayload $new.Files[$key]
 if($a -cne $z){throw 'Unexpected gameplay/resource delta'}
 $rows+=,@{key=$key.ToString();baseline_sha256=$a;candidate_sha256=$z}
}
$checked=0
foreach($r in $b.package_files){
 if($r.path -ceq $p){continue}
 if((Get-FileHash -LiteralPath (Join-Path (Join-Path $C 'package') $r.path)).Hash -cne $r.after){throw 'Changed stable payload outside archive'};$checked++
}
@{status='PASS_INDEPENDENT_BASELINE_EQUIVALENCE_REVIEW';method='Separate archive reader comparison against actual pinned PH3 archive; does not use rebuild expected-source hash table';resources=$rows;resource_count=$rows.Count;other_package_files_checked=$checked;vanilla_review='No quest implementation changed. Existing native corpus controls and native alias traces are retained; full vanilla lifecycle review remains incomplete.';reviewer_limit='Separate verification pass in the same Codex session, not an independent human/agent review';gameplay_repair_count=0;static_verified_quests=0;game_writes=0;save_writes=0}|ConvertTo-Json -Depth 30|Set-Content -LiteralPath (Join-Path $C 'adversarial_01.json') -Encoding utf8NoBOM
'PASS_INDEPENDENT_BASELINE_EQUIVALENCE_REVIEW'
