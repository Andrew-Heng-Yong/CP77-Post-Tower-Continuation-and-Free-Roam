param(
    [string]$WorkspaceRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$GameRoot = 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = [IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd([IO.Path]::DirectorySeparatorChar)
$game = [IO.Path]::GetFullPath($GameRoot).TrimEnd([IO.Path]::DirectorySeparatorChar)
if (@(Get-Process -Name Cyberpunk2077 -ErrorAction SilentlyContinue).Count) {
    throw 'Cyberpunk 2077 is running. Exit before restoring the prior vendor modules.'
}
$receiptPath = Join-Path $workspace 'research\b0_vendor_shared\install_receipt.json'
$receipt = Get-Content -LiteralPath $receiptPath -Raw | ConvertFrom-Json
if ($receipt.status -ne 'INSTALLED_OPT_IN_SHARED_VENDOR_TEST' -or
    @($receipt.replacementLua).Count -ne 4 -or @($receipt.addedFiles).Count -ne 2) {
    throw 'Shared vendor receipt is not the expected six-file test package'
}
function CheckGamePath([string]$path) {
    $resolved = [IO.Path]::GetFullPath($path)
    if (-not $resolved.StartsWith($game + [IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) {
        throw "Path escaped the game directory: $resolved"
    }
    return $resolved
}
foreach ($item in $receipt.replacementLua) {
    $target = CheckGamePath $item.path
    if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash -ne $item.newSha256) { throw "Installed Lua changed: $target" }
    if ((Get-FileHash -LiteralPath $item.backup -Algorithm SHA256).Hash -ne $item.oldSha256) { throw "Rollback copy changed: $($item.backup)" }
}
foreach ($item in $receipt.addedFiles) {
    $target = CheckGamePath $item.path
    if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash -ne $item.sha256) { throw "Added test file changed: $target" }
}
foreach ($item in $receipt.replacementLua) {
    Copy-Item -LiteralPath $item.backup -Destination $item.path -Force
    if ((Get-FileHash -LiteralPath $item.path -Algorithm SHA256).Hash -ne $item.oldSha256) { throw "Rollback hash mismatch: $($item.path)" }
}
foreach ($item in $receipt.addedFiles) {
    $target = CheckGamePath $item.path
    Remove-Item -LiteralPath $target
}
$record = [ordered]@{status='RESTORED_PRIOR_VENDOR_LUA';atUtc=(Get-Date).ToUniversalTime().ToString('o');sourceReceipt=$receiptPath;removedNewFiles=@($receipt.addedFiles|ForEach-Object {$_.path})}
$out = Join-Path $workspace 'research\b0_vendor_shared\rollback_receipt.json'
[IO.File]::WriteAllText($out,($record|ConvertTo-Json -Depth 5),[Text.UTF8Encoding]::new($false))
$record | ConvertTo-Json -Depth 5
