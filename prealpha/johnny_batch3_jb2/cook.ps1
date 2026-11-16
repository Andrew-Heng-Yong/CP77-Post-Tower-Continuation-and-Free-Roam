Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$planPath = Join-Path $PSScriptRoot 'input_02/plan.json'
$plan = Get-Content -LiteralPath $planPath -Raw | ConvertFrom-Json -Depth 100
$out = Join-Path $PSScriptRoot 'readback_02'
if ($plan.epoch -cne 'JB2' -or $plan.predecessor -cne 'JB1' -or (Test-Path -LiteralPath $out)) {
    throw 'Fresh JB2 readback required'
}
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
New-Item -ItemType Directory -Path $out | Out-Null
$source = Join-Path $plan.candidate 'archive_source'
$rows = @(foreach ($edit in $plan.edits) {
    if ((Get-FileHash -LiteralPath $edit.edited_json).Hash -cne $edit.edited_json_sha256) {
        throw "Changed edited input $($edit.depot)"
    }
    $target = Join-Path $source $edit.depot
    if ($edit.is_new) {
        if (Test-Path -LiteralPath $target) { throw "Alias already present $($edit.depot)" }
    } elseif ((Get-FileHash -LiteralPath $target).Hash -cne $edit.source.sha256) {
        throw "Wrong JB1 predecessor payload $($edit.depot)"
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
@{status='JB2_RESOURCES_COOKED_AND_READ_BACK'; plan_sha256=(Get-FileHash -LiteralPath $planPath).Hash;
  resources=$rows; game_writes=0; save_writes=0} | ConvertTo-Json -Depth 10 |
    Set-Content -LiteralPath (Join-Path $out 'manifest.json') -Encoding utf8NoBOM
Write-Output "Cooked and read back $($rows.Count) private resources."
