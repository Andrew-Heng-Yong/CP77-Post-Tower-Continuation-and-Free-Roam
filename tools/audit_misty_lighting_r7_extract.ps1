$ErrorActionPreference='Stop'
. "$PSScriptRoot/build_phase2a.ps1" -HelpersOnly
$lightingOut=Join-Path (Split-Path -Parent $PSScriptRoot) 'research/misty_viktor_world/r7_lighting_sources'
$lightingDepots=@('-25_18_0_0','-25_17_0_0','-25_19_0_0','-26_18_0_0','-24_18_0_0','-27_20_0_0','-25_20_0_0','-19_8_0_1','-14_9_0_1','-13_9_0_1','-12_9_0_1','-13_10_0_1','-12_10_0_1','-7_4_0_2') | ForEach-Object {"base\worlds\03_night_city\_compiled\default\exterior_$_.streamingsector"}
$lightingHash=[WolvenKit.Common.Services.HashService]::new();$lightingHash.Load()
$lightingFiles=@{}
foreach($lightingArchive in @('C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc\content\basegame_3_nightcity.archive','C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc\ep1\ep1_1_nightcity.archive')){
  $lightingArc=$null;[void]([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($lightingArchive,$lightingHash,[ref]$lightingArc)
  foreach($lightingEntry in $lightingArc.Files.Values){if($lightingEntry.Name -in $lightingDepots){$lightingFiles[$lightingEntry.Name]=@($lightingEntry,$lightingArchive)}}
}
$lightingRows=foreach($lightingDepot in $lightingDepots){
  $lightingPair=$lightingFiles[$lightingDepot];$lightingMemory=[IO.MemoryStream]::new()
  try{
    $lightingPair[0].Extract($lightingMemory);$lightingBytes=$lightingMemory.ToArray();$lightingMemory.Position=0
    $lightingReader=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($lightingMemory)
    $lightingHandler=[WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($e) return ($e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs])}
    $lightingReader.add_ParsingError($lightingHandler);$lightingFile=$null
    if($lightingReader.ReadFile([ref]$lightingFile,$true).ToString() -ne 'NoError'){throw "Decode failed $lightingDepot"}
    $lightingJson=Join-Path $lightingOut ($lightingDepot+'.json');New-Item -ItemType Directory -Force -Path (Split-Path $lightingJson)|Out-Null
    $lightingDto=[WolvenKit.Common.Conversion.RedFileDto]::new($lightingFile,$false)
    [IO.File]::WriteAllText($lightingJson,[WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize($lightingDto,[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new()),[Text.UTF8Encoding]::new($false))
    [pscustomobject]@{Resource=$lightingDepot;Archive=$lightingPair[1];Sha256=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($lightingBytes));Json=$lightingJson}
  }finally{$lightingMemory.Dispose()}
}
$lightingRows|ConvertTo-Json -Depth 4|Set-Content -LiteralPath (Join-Path (Split-Path -Parent $lightingOut) 'r7_lighting_sources.json') -Encoding utf8NoBOM
$lightingRows|Select-Object Resource,Archive|Format-Table -AutoSize
