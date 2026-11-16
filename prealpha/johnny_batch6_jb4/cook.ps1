param([Parameter(Mandatory)][ValidateSet('batch5','batch6','batch6_02')][string]$Batch)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$planPath = Join-Path $PSScriptRoot "input_01/$Batch.json"
$plan = Get-Content -LiteralPath $planPath -Raw | ConvertFrom-Json -Depth 100
$out = Join-Path $PSScriptRoot "readback_$Batch"
if (Test-Path -LiteralPath $out) { throw 'Fresh readback directory required' }
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$candidate = if ($Batch -ceq 'batch6_02') { 'candidate_02' } else { 'candidate_01' }
$source = Join-Path $PSScriptRoot "$candidate/archive_source"
New-Item -ItemType Directory -Path $out | Out-Null
$rows = @(foreach ($edit in $plan.edits) {
    if ($edit.depot -notmatch '^towercontinued\\[a-z0-9_\\]+\.(scene|questphase)$') {
        throw "Unexpected private depot $($edit.depot)"
    }
    $target = Join-Path $source $edit.depot
    if ((Get-FileHash -LiteralPath $edit.edited_json).Hash -cne $edit.edited_json_sha256) {
        throw "Changed edited input $($edit.depot)"
    }
    if ($edit.is_new) {
        if (Test-Path -LiteralPath $target) { throw "Alias already exists $($edit.depot)" }
    } elseif ((Get-FileHash -LiteralPath $target).Hash -cne $edit.source_sha256) {
        throw "Wrong JB3 predecessor $($edit.depot)"
    }
    $dto = [WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Deserialize(
        [WolvenKit.Common.Conversion.RedFileDto], [IO.File]::ReadAllText($edit.edited_json),
        [WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new())
    Write-Cr2wFile $dto.Data $target
    $key = [WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($edit.depot).ToString()
    $json = Join-Path $out ($key + '.json')
    Export-Cr2wJson (Read-Cr2wFile $target) $json
    @{depot=$edit.depot; raw=$target; sha256=(Get-FileHash -LiteralPath $target).Hash;
      json=$json; json_sha256=(Get-FileHash -LiteralPath $json).Hash}
})
@{status='JB4_RESOURCES_COOKED_AND_READ_BACK'; batch=$Batch;
  plan_sha256=(Get-FileHash -LiteralPath $planPath).Hash; resources=$rows} |
    ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $out 'manifest.json') -Encoding utf8NoBOM
Write-Output "Cooked and read back $($rows.Count) $Batch resources."
