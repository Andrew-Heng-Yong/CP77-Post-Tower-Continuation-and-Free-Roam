param([string]$Candidate='candidate_01')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$W=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$C=Join-Path $PSScriptRoot $Candidate
if([IO.Path]::GetFullPath($C) -ne (Join-Path $PSScriptRoot 'candidate_01')){throw 'Unexpected output root'}
if(Test-Path -LiteralPath (Join-Path $C 'rebuild_01.json')){throw 'Preserve completed build'}
$b=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'baseline.json') -Raw|ConvertFrom-Json -Depth 100
$plan=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'approved_changes_02.json') -Raw|ConvertFrom-Json -Depth 100
. (Join-Path $W 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $W 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$expected=@{};foreach($p in $b.private_resources.PSObject.Properties){$expected[$p.Name]=$p.Value}
foreach($r in $plan.resources){
 if(-not $expected.ContainsKey($r.depot) -or $expected[$r.depot] -cne $r.before){throw 'Unpinned repair predecessor'}
 if(-not $r.evidence -or -not $r.tests){throw 'Repair requires evidence and tests'}
 $expected[$r.depot]=$r.after
}
$source=Join-Path $C 'archive_source';$found=@{};$changed=@()
foreach($f in Get-ChildItem -LiteralPath $source -File -Recurse){
 $rel=[IO.Path]::GetRelativePath($source,$f.FullName);$h=(Get-FileHash -LiteralPath $f.FullName).Hash
 if(-not $expected.ContainsKey($rel) -or $expected[$rel] -cne $h){throw "Unapproved source delta: $rel"}
 $found[$rel]=$h;if($b.private_resources.$rel -cne $h){$changed+=,$rel}
}
if($found.Count -ne $expected.Count){throw 'Source resources missing'}
foreach($r in $b.package_files){
 $p=Join-Path (Join-Path $C 'package') $r.path
 if((Get-FileHash -LiteralPath $p).Hash -cne $r.after){throw 'Package changed before approved rebuild'}
}
$archive=Join-Path $C 'package/archive/pc/mod/zzzz_PTFR_Combined.archive'
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Packing failed'}}finally{$stream.Dispose()}
$packed=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -ne 'NoError'){throw 'Archive unreadable'}
if($packed.Files.Count -ne $expected.Count){throw 'Archive member count differs'}
$rows=@();$keys=@{}
foreach($dep in $expected.Keys){
 $key=[uint64][WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($dep)
 if($keys.ContainsKey($key.ToString())){throw 'Source depot hash collision'};$keys[$key.ToString()]=$dep
 if(-not $packed.Files.ContainsKey($key)){throw "Missing member: $dep"}
 $mem=[IO.MemoryStream]::new();try{$packed.Files[$key].Extract($mem);$actual=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($mem.ToArray()))}finally{$mem.Dispose()}
 if($actual -cne $expected[$dep]){throw "Packed payload mismatch: $dep"}
 $rows+=,@{depot=$dep;key=$key.ToString();sha256=$actual;changed=($dep -in $changed)}
}
@{status='PASS_FULL_CONSOLIDATED_REBUILD_NOT_INSTALLED';gameplay_delta=($changed.Count -gt 0);source_count=$expected.Count;readback_count=$rows.Count;changed_resources=$changed;resources=$rows;archive_sha256=(Get-FileHash -LiteralPath $archive).Hash;xl_sha256=(Get-FileHash -LiteralPath (Join-Path $C 'package/archive/pc/mod/zzzz_PTFR_Combined.archive.xl')).Hash;game_writes=0;save_writes=0;installed=$false}|ConvertTo-Json -Depth 40|Set-Content -LiteralPath (Join-Path $C 'rebuild_01.json') -Encoding utf8NoBOM
'PASS_FULL_CONSOLIDATED_REBUILD_NOT_INSTALLED'
