param(
  [Parameter(Mandatory)][string]$Game,
  [Parameter(Mandatory)][string]$WolvenKitRoot,
  [Parameter(Mandatory)][ValidatePattern('^scope_records_[0-9]+\.json$')][string]$EvidenceName
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$output = Join-Path $PSScriptRoot $EvidenceName
if (Test-Path -LiteralPath $output) { throw 'Record evidence already exists.' }
. (Join-Path $PSScriptRoot '../../tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot $WolvenKitRoot

$databases = foreach ($file in @('tweakdb_ep1.bin', 'tweakdb.bin')) {
  $path = Join-Path $Game ('r6/cache/' + $file)
  $digest = (Get-FileHash -LiteralPath $path).Hash
  $stream = [IO.File]::OpenRead($path)
  try {
    $db = $null
    $result = [WolvenKit.RED4.TweakDB.TweakDBReader]::new($stream).ReadFile([ref]$db)
    if ($result.ToString() -ne 'NoError') { throw "Could not read $path" }
    [pscustomobject]@{ Database = $db; Path = $path; Sha256 = $digest }
  } finally {
    $stream.Dispose()
  }
}

$hashMethod = [WolvenKit.RED4.Types.TweakDBID].GetMethods() | Where-Object {
  $_.Name -eq 'op_Implicit' -and $_.ReturnType -eq [uint64]
}
function Get-TweakHash([string]$Name) {
  [WolvenKit.RED4.Types.TweakDBID]::CalculateHash($Name)
}
function Get-Flat($Database, [string]$Name) {
  $hash = Get-TweakHash $Name
  if ($Database.Flats.Exists($hash)) { return ,$Database.Flats.GetValue($hash) }
  return $null
}
function Get-Id($Value) {
  $hashMethod.Invoke($null, [object[]]@($Value.PSObject.BaseObject))
}

Add-Type -TypeDefinition @'
public static class CyberwareTweakHash {
  public static ulong Append(ulong id, string suffix) {
    var bytes = System.Text.Encoding.UTF8.GetBytes(suffix);
    uint crc = (uint)id ^ 0xffffffffu;
    foreach (byte value in bytes) {
      crc ^= value;
      for (int bit = 0; bit < 8; bit++)
        crc = (crc >> 1) ^ ((crc & 1) != 0 ? 0xedb88320u : 0u);
    }
    return (((id >> 32) + (ulong)bytes.Length) << 32) | (crc ^ 0xffffffffu);
  }
}
'@

$models = [ordered]@{
  JohnnyTattoo = 'CasiusTattoo'
  TogetherForever = 'SilverhandTattoo'
  TygerClaws = 'YakuzaTattoo'
  TitaniumBones = 'TitaniumInfusedBones'
  Chitin = 'Chiton'
  SubdermalArmor = 'BoringPlating'
  Carapace = 'WeirdTankyPlating'
  BasicKiroshi = 'KiroshiOpticsBare'
}
$qualities = @('', 'Common', 'CommonPlus', 'Uncommon', 'UncommonPlus', 'Rare', 'RarePlus',
  'Epic', 'EpicPlus', 'Legendary', 'LegendaryPlus', 'LegendaryPlusPlus')
$modelsEvidence = [ordered]@{}
foreach ($model in $models.Keys) {
  $expectedArea = switch ($model) {
    { $_ -in @('JohnnyTattoo', 'TogetherForever', 'TygerClaws') } { 'EquipmentArea.HandsCW' }
    'TitaniumBones' { 'EquipmentArea.MusculoskeletalSystemCW' }
    'BasicKiroshi' { 'EquipmentArea.EyesCW' }
    default { 'EquipmentArea.IntegumentarySystemCW' }
  }
  $rows = foreach ($prefix in @('', 'Advanced', 'Iconic', 'IconicAdvanced')) {
    foreach ($quality in $qualities) {
      $name = 'Items.' + $prefix + $models[$model] + $quality
      foreach ($source in $databases) {
        $db = $source.Database
        $recordType = $db.Records.GetRecord((Get-TweakHash $name))
        if ($null -eq $recordType) { continue }
        $area = Get-Flat $db ($name + '.equipArea')
        if ($recordType.Name -ne 'gamedataItem_Record' -or $null -eq $area -or
            (Get-Id $area) -ne (Get-TweakHash $expectedArea)) {
          throw "Unexpected stock record or equipment area for $name ($area, expected $expectedArea)"
        }
        $side = Get-Flat $db ($name + '.sideUpgradeItem')
        $sideID = if ($null -ne $side) { Get-Id $side } else { 0 }
        if ($sideID -ne 0) {
          $sideArea = $db.Flats.GetValue([CyberwareTweakHash]::Append($sideID, '.equipArea'))
          if ($null -eq $db.Records.GetRecord($sideID) -or $null -eq $sideArea -or (Get-Id $sideArea) -ne (Get-TweakHash $expectedArea)) {
            throw "Invalid stock side upgrade for $name"
          }
        }
        [pscustomobject]@{ id = $name; area = $expectedArea; source = (Split-Path -Leaf $source.Path); sideUpgrade = $sideID }
        break
      }
    }
  }
  if (@($rows).Count -eq 0) { throw "No stock records found for $model" }
  $modelsEvidence[$model] = @($rows)
}

$db = $databases[0].Database
$slots = [ordered]@{}
foreach ($area in @('ArmsCW', 'ArmsCWStyle', 'HandsCW', 'EyesCW', 'MusculoskeletalSystemCW', 'IntegumentarySystemCW',
    'FrontalCortexCW', 'SystemReplacementCW', 'NervousSystemCW', 'CardiovascularSystemCW', 'LegsCW', 'PersonalLink')) {
  $equipSlots = Get-Flat $db ('EquipmentArea.' + $area + '.equipSlots')
  if ($null -eq $equipSlots) { throw "Missing native equipment slots for $area" }
  $slots[$area] = @(foreach ($slot in $equipSlots) {
    $slotID = Get-Id $slot
    $packages = $db.Flats.GetValue([CyberwareTweakHash]::Append($slotID, '.onInsertion'))
    [pscustomobject]@{ slot = $slotID; onInsertion = @($packages | Where-Object { $null -ne $_ } | ForEach-Object { Get-Id $_ }) }
  })
}

foreach ($source in $databases) {
  if ((Get-FileHash -LiteralPath $source.Path).Hash -ne $source.Sha256) { throw 'Native TweakDB changed during audit.' }
}
[ordered]@{
  inputs = @($databases | Select-Object Path, Sha256)
  models = $modelsEvidence
  slots = $slots
} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $output -Encoding utf8
