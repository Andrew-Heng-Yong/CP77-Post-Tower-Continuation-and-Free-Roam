param(
    [string]$WorkspaceRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$GameRoot = 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',
    [switch]$PreflightOnly
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = [IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd([IO.Path]::DirectorySeparatorChar)
$game = [IO.Path]::GetFullPath($GameRoot).TrimEnd([IO.Path]::DirectorySeparatorChar)
if (@(Get-Process -Name Cyberpunk2077 -ErrorAction SilentlyContinue).Count) {
    throw 'Cyberpunk 2077 is running. Exit before installing the shared vendor probe.'
}
if (-not (Test-Path -LiteralPath (Join-Path $game 'r6\cache\final.redscripts') -PathType Leaf) -or
    -not (Test-Path -LiteralPath (Join-Path $game 'bin\x64\plugins\cyber_engine_tweaks\mods') -PathType Container)) {
    throw "Unexpected game installation: $game"
}
function InGame([string]$relative) {
    $resolved = [IO.Path]::GetFullPath((Join-Path $game $relative))
    if (-not $resolved.StartsWith($game + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Target escaped game directory: $resolved"
    }
    return $resolved
}
$replace = @(
    [pscustomobject]@{Name='PTFR_B0_Northside_Gunsmith';Receipt='research\b0_northside_gunsmith\validation\install_receipt.json'},
    [pscustomobject]@{Name='PTFR_B0_Northside_Foodshop';Receipt='research\b0_northside_foodshop\validation\install_receipt.json'},
    [pscustomobject]@{Name='PTFR_B0_Northside_Medicstore';Receipt='research\b0_northside_medicstore\validation\install_receipt.json'},
    [pscustomobject]@{Name='PTFR_B0_LCH_Clothing_Vendor';Receipt='research\b0_lch_clothing_vendor\validation\install_receipt.json'}
)
$rollback = Join-Path $workspace 'build\B0_VendorShared\rollback_original_4'
if (Test-Path -LiteralPath $rollback) { throw "Rollback directory already exists: $rollback" }
$oldMarker = 'q:GetFactStr(PREFIX.."Enabled")==1 then'
$newMarker = 'q:GetFactStr(PREFIX.."Enabled")==1 and q:GetFactStr("PTFRB0VSH_SharedMode")~=1 then'
$oldLogBlock = @'
  if attached and elapsed-lastPoll>=2 then
    lastPoll=elapsed
    local state=snap()
    if state.markers.Near~=priorNear or state.markers.SpawnActionOut~=priorSpawn or
       state.markers.ActorDistanceGate~=priorGate then
      log("NATIVE_STAGE_CHANGE",state,{near_from=priorNear,spawn_from=priorSpawn,gate_from=priorGate})
      priorNear=state.markers.Near;priorSpawn=state.markers.SpawnActionOut
      priorGate=state.markers.ActorDistanceGate
    elseif state.markers.Enabled==1 then log("SAMPLE",state,{}) end
  end
'@
$newLogBlock = @'
  if attached and elapsed-lastPoll>=2 then
    lastPoll=elapsed
    if Game.GetQuestsSystem():GetFactStr("PTFRB0VSH_SharedMode")~=1 then
      local state=snap()
      if state.markers.Near~=priorNear or state.markers.SpawnActionOut~=priorSpawn or
         state.markers.ActorDistanceGate~=priorGate then
        log("NATIVE_STAGE_CHANGE",state,{near_from=priorNear,spawn_from=priorSpawn,gate_from=priorGate})
        priorNear=state.markers.Near;priorSpawn=state.markers.SpawnActionOut
        priorGate=state.markers.ActorDistanceGate
      elseif state.markers.Enabled==1 then log("SAMPLE",state,{}) end
    end
  end
'@
$changes = @()
foreach ($entry in $replace) {
    $receipt = Get-Content -LiteralPath (Join-Path $workspace $entry.Receipt) -Raw | ConvertFrom-Json
    $record = @($receipt.files | Where-Object { $_.path -like '*\init.lua' })
    if ($record.Count -ne 1) { throw "Expected one installed Lua receipt for $($entry.Name)" }
    $relative = "bin\x64\plugins\cyber_engine_tweaks\mods\$($entry.Name)\init.lua"
    $target = InGame $relative
    if ($record[0].path -ne $target -or -not (Test-Path -LiteralPath $target -PathType Leaf)) {
        throw "Installed Lua path mismatch: $target"
    }
    $currentHash = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash
    if ($currentHash -ne $record[0].sha256) { throw "Installed Lua changed since receipt: $target" }
    $source = Join-Path $workspace "diagnostics\$($entry.Name)\init.lua"
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw "Missing source: $source" }
    $before = [IO.File]::ReadAllText($target).Replace("`r`n","`n")
    $after = [IO.File]::ReadAllText($source).Replace("`r`n","`n")
    if (-not $before.Contains($oldMarker) -or -not $before.Contains($oldLogBlock) -or
        $before.Replace($oldMarker,$newMarker).Replace($oldLogBlock,$newLogBlock) -ne $after) {
        throw "Shared-mode change is not the only Lua edit: $($entry.Name)"
    }
    $changes += [pscustomobject]@{Name=$entry.Name;Source=$source;Target=$target;OldHash=$currentHash;NewHash=(Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash}
}
$newFiles = @(
    [pscustomobject]@{Source=(Join-Path $workspace 'redscript\PTFR_B0_VendorShared\VendorSharedFarDriver.reds');Target=(InGame 'r6\scripts\PTFR_B0_VendorShared\VendorSharedFarDriver.reds')},
    [pscustomobject]@{Source=(Join-Path $workspace 'diagnostics\PTFR_B0_VendorBatch\init.lua');Target=(InGame 'bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_B0_VendorBatch\init.lua')}
)
foreach ($item in $newFiles) {
    if (-not (Test-Path -LiteralPath $item.Source -PathType Leaf)) { throw "Missing source: $($item.Source)" }
    if (Test-Path -LiteralPath $item.Target) { throw "Refusing to overwrite: $($item.Target)" }
    $item | Add-Member -NotePropertyName Hash -NotePropertyValue ((Get-FileHash -LiteralPath $item.Source -Algorithm SHA256).Hash)
}
$cli = Join-Path $workspace 'research\finalboards_dismissal\tooling\redscript-cli.exe'
& $cli lint -s $newFiles[0].Source -b (Join-Path $game 'r6\cache\final.redscripts')
if ($LASTEXITCODE -ne 0) { throw 'Shared redscript failed offline lint' }
if (@(Get-Process -Name Cyberpunk2077 -ErrorAction SilentlyContinue).Count) { throw 'Game started during preflight' }
if ($PreflightOnly) {
    [pscustomobject]@{status='PREFLIGHT_OK';replacementLua=$changes.Count;addedFiles=$newFiles.Count;rollbackTarget=$rollback}
    return
}
New-Item -ItemType Directory -Force -Path $rollback | Out-Null
$installedNew = [System.Collections.Generic.List[string]]::new()
$replaced = [System.Collections.Generic.List[object]]::new()
try {
    foreach ($item in $changes) {
        $backup = Join-Path $rollback ($item.Name + '.init.lua')
        Copy-Item -LiteralPath $item.Target -Destination $backup
        if ((Get-FileHash -LiteralPath $backup -Algorithm SHA256).Hash -ne $item.OldHash) { throw "Backup hash mismatch: $backup" }
        $item | Add-Member -NotePropertyName Backup -NotePropertyValue $backup
    }
    foreach ($item in $changes) {
        Copy-Item -LiteralPath $item.Source -Destination $item.Target -Force
        $replaced.Add($item)
        if ((Get-FileHash -LiteralPath $item.Target -Algorithm SHA256).Hash -ne $item.NewHash) { throw "Installed Lua hash mismatch: $($item.Target)" }
    }
    foreach ($item in $newFiles) {
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $item.Target) | Out-Null
        Copy-Item -LiteralPath $item.Source -Destination $item.Target
        $installedNew.Add($item.Target)
        if ((Get-FileHash -LiteralPath $item.Target -Algorithm SHA256).Hash -ne $item.Hash) { throw "Installed hash mismatch: $($item.Target)" }
    }
} catch {
    foreach ($path in $installedNew) {
        if ($path.StartsWith($game + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase) -and (Test-Path -LiteralPath $path -PathType Leaf)) {
            Remove-Item -LiteralPath $path
        }
    }
    foreach ($item in $replaced) { Copy-Item -LiteralPath $item.Backup -Destination $item.Target -Force }
    throw
}
$receipt = [ordered]@{
    status='INSTALLED_OPT_IN_SHARED_VENDOR_TEST'
    installedAtUtc=(Get-Date).ToUniversalTime().ToString('o')
    replacementLua=@($changes | ForEach-Object {[ordered]@{name=$_.Name;path=$_.Target;oldSha256=$_.OldHash;newSha256=$_.NewHash;backup=$_.Backup}})
    addedFiles=@($newFiles | ForEach-Object {[ordered]@{path=$_.Target;sha256=$_.Hash}})
    vanillaReplacements=@();savesModified=$false;storyFactsModified=$false
    testResult='PENDING_COMBINED_DISPOSABLE_RUN'
}
$receiptPath = Join-Path $workspace 'research\b0_vendor_shared\install_receipt.json'
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $receiptPath) | Out-Null
[IO.File]::WriteAllText($receiptPath,($receipt | ConvertTo-Json -Depth 9),[Text.UTF8Encoding]::new($false))
$receipt | ConvertTo-Json -Depth 9
