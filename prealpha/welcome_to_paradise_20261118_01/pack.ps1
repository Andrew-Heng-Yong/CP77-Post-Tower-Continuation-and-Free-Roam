# Rebuild from individually verified installed members. Replace the private lipmap and append the tour.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$work=Join-Path $PSScriptRoot 'work'
$out=Join-Path $work 'pack_01'
if (Test-Path $out) {throw 'Fresh archive output required'}
function Json($path) {Get-Content -LiteralPath $path -Raw | ConvertFrom-Json -AsHashtable -Depth 100 -DateKind String}
function Hash($path) {(Get-FileHash -LiteralPath $path).Hash}
$template=Get-Content -LiteralPath (Join-Path $ws 'prealpha/misty_rooftop_seat_20261117_01/pack.ps1') -Raw
$start=$template.IndexOf('function Plain(')
. ([scriptblock]::Create($template.Substring($start,$template.IndexOf('$manifestPath =')-$start)))
$start=$template.IndexOf('$hashService =')
. ([scriptblock]::Create($template.Substring($start,$template.IndexOf('$old = OpenArchive')-$start)))
$baseline=Join-Path $ws 'prealpha/misty_roof_pickup_release_20261118_01/installed_manifest.json'
$manifest=Json $baseline
$providers=Json (Join-Path $work 'private_01/providers.json')
$cook=Json (Join-Path $work 'cook_02/manifest.json')
if ((Hash $baseline) -cne $providers.manifest_sha256 -or $providers.hits.Count -ne 0 -or $providers.queries.Count -ne 13 -or $cook.resources.Count -ne 14) {throw 'Input inventory mismatch'}
$ar='archive/pc/mod/zzzz_PTFR_Combined.archive'
$xl=$ar+'.xl';$lip='towercontinued\sidejob_repair_sr1\en-us.lipmap'
$oldPath=Join-Path $manifest.game_root $ar
Plain $oldPath
if ((Hash $oldPath) -cne $manifest.archive_sha256) {throw 'Installed archive changed'}
$old=OpenArchive $oldPath
$donor=Join-Path $ws 'prealpha/misty_roof_chair_prompt_20261118_01/work/pack_01/source'
$stage=Join-Path $out 'source';$members=@{}
Plain $donor
if (@(Get-ChildItem $donor -Recurse -Force -Attributes ReparsePoint).Count) {throw 'Linked donor'}
$files=@(Get-ChildItem $donor -File -Recurse)
if ($files.Count -ne $old.Files.Count -or $files.Count -ne 1751) {throw 'Donor count mismatch'}
$replacement=@{};foreach ($row in $cook.resources) {
    if ((Hash $row.raw) -cne $row.sha256 -or ($row.depot -cne $lip -and $row.depot -cnotin $providers.queries)) {throw "Unqualified input $($row.depot)"}
    $replacement[$row.depot]=$row
}
function Stage($depot,$src,$hash) {
    $key=DepotKey $depot
    if ($members.ContainsKey($key)) {throw "Duplicate $depot"}
    $dest=Join-Path $stage $depot
    [void][IO.Directory]::CreateDirectory((Split-Path $dest -Parent))
    [IO.File]::Copy($src,$dest,$false);$members[$key]=$hash
}
foreach ($f in $files) {
    $depot=[IO.Path]::GetRelativePath($donor,$f.FullName);$key=DepotKey $depot
    $hash=Hash $f.FullName
    if (!$old.Files.ContainsKey($key) -or $hash -cne (MemberHash $old.Files[$key])) {throw "Donor mismatch $depot"}
    if ($depot -cne $lip) {Stage $depot $f.FullName $hash}
}
foreach ($row in $cook.resources) {Stage $row.depot $row.raw $row.sha256}
$pkg=Join-Path $out 'package'
$archive=Join-Path $pkg $ar
[void][IO.Directory]::CreateDirectory((Split-Path $archive -Parent))
$stream=[IO.File]::Open($archive,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write)
try {
    $writer=[WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hashService,[WolvenKit.SerilogWrapper]::new())
    if (!$writer.WriteArchive([IO.DirectoryInfo]::new($stage),$stream)) {throw 'Packing failed'}
} finally {$stream.Dispose()}
$new=OpenArchive $archive
if ($new.Files.Count -ne 1764 -or $members.Count -ne $new.Files.Count) {throw 'Archive member mismatch'}
foreach ($k in $members.Keys) {
    if (!$new.Files.ContainsKey($k) -or (MemberHash $new.Files[$k]) -cne $members[$k]) {throw "Archive readback differs $k"}
}
$oldXL=Join-Path $manifest.game_root $xl
if ((Hash $oldXL) -cne @($manifest.core_files|Where-Object path -ceq $xl)[0].sha256) {throw 'Registration drift'}
$oldText=[IO.File]::ReadAllText($oldXL)
if ([regex]::Matches($oldText,'(?m)^streaming:').Count -ne 1) {throw 'Invalid insertion point'}
$newline=if ($oldText.Contains([char]13)) {[Environment]::NewLine} else {[string][char]10}
$addition=@('    - path: towercontinued\paradise\entry.questphase','      parent: ep1\quest\ep1.quest','      input:','        node: [1]','        socket: Out','') -join $newline
[IO.File]::WriteAllText((Join-Path $pkg $xl),$oldText.Replace('streaming:',($addition+'streaming:')),[Text.UTF8Encoding]::new($false))
@{status='MEMBERS_VERIFIED';baseline_sha256=(Hash $baseline);xl_addition=$addition;unchanged_members=1750;packed_members=$new.Files.Count;private_additions=13;archive_sha256=(Hash $archive);provider_count=$providers.archives.Count} | ConvertTo-Json | Set-Content (Join-Path $out 'readback.json') -Encoding utf8NoBOM
Write-Output "Read back all $($new.Files.Count) archive members."
