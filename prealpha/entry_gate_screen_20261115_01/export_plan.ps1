param([Parameter(Mandatory=$true)][string]$Plan)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
if ((Get-FileHash -LiteralPath ([WolvenKit.RED4.Save.IO.CyberpunkSaveReader].Assembly.Location)).Hash -cne 'EF17F40D73F207F0F71F1F41A70A4549A19792D438F680A9BFBB4800D2EE2987') { throw 'Parser drift' }
$rows=@(Get-Content -LiteralPath $Plan -Raw | ConvertFrom-Json)
foreach ($row in $rows) {
    $dest=[IO.Path]::GetFullPath([string]$row.output)
    if (-not $dest.StartsWith(([IO.Path]::GetFullPath($PSScriptRoot)+'\'),[StringComparison]::OrdinalIgnoreCase)) { throw 'Output outside investigation' }
    if (Test-Path -LiteralPath $dest) { throw 'Fresh output required' }
    foreach ($path in @([string]$row.raw_path,(Split-Path $dest -Parent))) {
        for ($item=Get-Item -LiteralPath $path -Force; $null -ne $item;) {
            if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Reparse input/output refused' }
            $item=if ($item -is [IO.FileInfo]) { $item.Directory } else { $item.Parent }
        }
    }
    if ((Get-FileHash -LiteralPath $row.raw_path).Hash -cne $row.sha256) { throw 'Resource drift' }
    Export-Cr2wJson (Read-Cr2wFile $row.raw_path) $dest
}
Write-Output ("Exported {0} pinned resources" -f $rows.Count)
