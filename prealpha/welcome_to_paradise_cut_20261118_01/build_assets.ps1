param([string]$Output='assets_02')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$parent=Join-Path $ws 'prealpha/welcome_to_paradise_20261118_01'
$work=Join-Path $PSScriptRoot 'work'
$out=Join-Path $work $Output
if ($Output -cnotmatch '^assets_\d+$' -or (Test-Path $out)) {throw 'Fresh asset output required'}
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
function Json($p) {Get-Content -LiteralPath $p -Raw | ConvertFrom-Json -AsHashtable -Depth 100}
function Hash($p) {(Get-FileHash -LiteralPath $p).Hash}
$plan=Json (Join-Path $work 'edit_02/plan.json')
$core=Join-Path $parent 'candidate_01/core_manifest.json'
if ((Hash $core) -cne $plan.parent_sha256) {throw 'Staged Core changed'}
$baseline=Json (Join-Path $ws 'prealpha/misty_roof_pickup_release_20261118_01/installed_manifest.json')
$template=Get-Content -LiteralPath (Join-Path $ws 'prealpha/misty_rooftop_seat_20261117_01/pack.ps1') -Raw
$i=$template.IndexOf('function Plain(')
. ([scriptblock]::Create($template.Substring($i,$template.IndexOf('$manifestPath =')-$i)))
$i=$template.IndexOf('$hashService =')
. ([scriptblock]::Create($template.Substring($i,$template.IndexOf('$old = OpenArchive')-$i)))
$prefix='towercontinued\paradise\'
$checked=@{}
foreach ($d in @((Get-Content (Join-Path $parent 'private_queries.json') -Raw | ConvertFrom-Json)) + @($plan.added|ForEach-Object {$prefix+$_})) {
    $key=DepotKey $d
    if ($checked.ContainsKey($key)) {throw "Private depot key collision $d"}
    $checked[$key]=$d
}
$roots=@('archive/pc','mods'|ForEach-Object {Join-Path $baseline.game_root $_}|Where-Object {Test-Path -LiteralPath $_})
$live=@(Get-ChildItem -LiteralPath $roots -Filter '*.archive' -File -Recurse)
foreach ($f in $live) {
    Plain $f.FullName
    $a=OpenArchive $f.FullName
    foreach ($k in $checked.Keys) {if ($a.Files.ContainsKey([uint64]$k)) {throw "Private depot already provided: $($checked[$k]) in $f"}}
}
$null=New-Item -ItemType Directory -Path $out
$records=[Collections.Generic.List[object]]::new()
function Save($file,$depot) {
    $raw=Join-Path $out ('changed/'+$depot)
    $back=Join-Path $out ('readback/'+$depot+'.json')
    foreach ($p in @($raw,$back)) {$null=New-Item -ItemType Directory -Force (Split-Path $p -Parent)}
    Write-Cr2wFile $file $raw
    Export-Cr2wJson (Read-Cr2wFile $raw) $back
    $records.Add(@{depot=$depot;raw=$raw;sha256=(Hash $raw);json=$back;json_sha256=(Hash $back)})
}
foreach ($d in $plan.changed) {
    $depot=$prefix+$d
    $path=Join-Path $work ('edit_02/'+$depot+'.json')
    $data=Json $path
    if (@($data.Data.EmbeddedFiles).Count -ne 0) {throw "Embedded data requires transfer $d"}
    $options=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new()
    $dto=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Deserialize([WolvenKit.Common.Conversion.RedFileDto],[IO.File]::ReadAllText($path),$options)
    $file=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$file.RootChunk=$dto.Data.RootChunk
    Save $file $depot
}
$lip='towercontinued\sidejob_repair_sr1\en-us.lipmap'
$donor=Join-Path $parent 'work/pack_01/source'
$extra=Json (Join-Path $parent 'work/extra_01/providers.json')
$native=@($extra.hits|Where-Object depot -ceq 'base\localization\en-us.lipmap')
if ($native.Count -ne 1 -or (Hash $native[0].raw) -cne $native[0].sha256) {throw 'English lipmap donor changed'}
$official=(Read-Cr2wFile $native[0].raw).RootChunk
$combined=Read-Cr2wFile (Join-Path $donor $lip)
foreach ($scene in @($plan.added|Where-Object {$_.EndsWith('.scene')})) {
    $key=DepotKey $scene;$dest=DepotKey ($prefix+$scene)
    $index=@(for ($i=0;$i -lt $official.ScenePaths.Count;$i++) {if ($official.ScenePaths[$i].ToString() -ceq $key.ToString()) {$i}})
    if ($index.Count -ne 1 -or @($combined.RootChunk.ScenePaths|Where-Object {$_.ToString() -ceq $dest.ToString()}).Count) {throw "Lipmap mapping $scene"}
    $combined.RootChunk.ScenePaths.Add([WolvenKit.RED4.Types.CUInt64]::op_Implicit([uint64]$dest))
    $combined.RootChunk.SceneEntries.Add($official.SceneEntries[$index[0]].DeepCopy())
}
Save $combined $lip
$ar='archive/pc/mod/zzzz_PTFR_Combined.archive'
$oldPath=Join-Path $parent ('candidate_01/package/'+$ar)
if ((Hash $oldPath) -cne @((Json $core).core_files|Where-Object path -ceq $ar)[0].sha256) {throw 'Staged archive changed'}
$old=OpenArchive $oldPath
$overrides=@{};foreach ($row in $records) {$overrides[$row.depot]=$row}
$stage=Join-Path $out 'source'
$members=@{}
function Stage($d,$p,$digest) {
    $k=DepotKey $d
    if ($members.ContainsKey($k)) {throw "Duplicate staged key $d"}
    $target=Join-Path $stage $d
    [void][IO.Directory]::CreateDirectory((Split-Path $target -Parent))
    [IO.File]::Copy($p,$target,$false)
    $members[$k]=$digest
}
Plain $donor
if (@(Get-ChildItem $donor -Recurse -Force -Attributes ReparsePoint).Count) {throw 'Linked donor'}
$prior=@(Get-ChildItem $donor -File -Recurse)
if ($prior.Count -ne 1764 -or $old.Files.Count -ne $prior.Count) {throw 'Unexpected staged member inventory'}
$preserved=0
foreach ($f in $prior) {
    $d=[IO.Path]::GetRelativePath($donor,$f.FullName);$k=DepotKey $d;$digest=Hash $f.FullName
    if (!$old.Files.ContainsKey($k) -or (MemberHash $old.Files[$k]) -cne $digest) {throw "Staged donor mismatch $d"}
    if (!$overrides.ContainsKey($d)) {Stage $d $f.FullName $digest;$preserved++}
}
foreach ($r in $records) {Stage $r.depot $r.raw $r.sha256}
$archive=Join-Path $out ('package/'+$ar)
[void][IO.Directory]::CreateDirectory((Split-Path $archive -Parent))
$stream=[IO.File]::Open($archive,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write)
try {
    $writer=[WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hashService,[WolvenKit.SerilogWrapper]::new())
    if (!$writer.WriteArchive([IO.DirectoryInfo]::new($stage),$stream)) {throw 'Archive pack failed'}
} finally {$stream.Dispose()}
$packed=OpenArchive $archive
if ($packed.Files.Count -ne $members.Count -or $packed.Files.Count -ne ($prior.Count+$plan.added.Count)) {throw 'Packed count mismatch'}
foreach ($k in $members.Keys) {
    if (!$packed.Files.ContainsKey($k) -or (MemberHash $packed.Files[$k]) -cne $members[$k]) {throw "Packed member drift $k"}
}
@{resources=$records.ToArray();preserved=$preserved;packed_members=$packed.Files.Count;archives_checked=$live.Count;private_keys_checked=$checked.Count;archive_sha256=(Hash $archive);parent_sha256=$plan.parent_sha256} | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $out 'readback.json') -Encoding utf8NoBOM
Write-Output "Read back all $($packed.Files.Count) members; $preserved matched the previous staged build."
