param([string]$OutputRoot='research/phase2b_p4/variant_sectors')
$ErrorActionPreference='Stop'
$wkStaging='C:\Users\Ayong\Documents\WolvenKit-8.20.0'
foreach($a in @('WolvenKit.Core.dll','WolvenKit.Common.dll','WolvenKit.RED4.dll')){[void][Reflection.Assembly]::LoadFrom((Join-Path $wkStaging $a))}
$hsStaging=[WolvenKit.Common.Services.HashService]::new();$hsStaging.Load()
$wantedStaging=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
foreach($row in (Get-Content research/phase2b_p4/staging_variant_sectors.json -Raw | ConvertFrom-Json)){[void]$wantedStaging.Add($row.sector)}
$rootStaging='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc'
$rows=[Collections.Generic.List[object]]::new()
foreach($rel in @('content/basegame_3_nightcity.archive','ep1/ep1_1_nightcity.archive')){
  $archivePath=Join-Path $rootStaging $rel; $archiveKey=[IO.Path]::GetFileNameWithoutExtension($archivePath)
  $arc=$null; [void]([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archivePath,$hsStaging,[ref]$arc)
  foreach($e in $arc.Files.Values){if(-not $wantedStaging.Contains($e.Name)){continue}
    $m=[IO.MemoryStream]::new();$errorText=$null;$decode=$null
    $rawPath=Join-Path $OutputRoot (Join-Path $archiveKey (Join-Path 'raw' $e.Name));$jsonPath=Join-Path $OutputRoot (Join-Path $archiveKey (Join-Path 'json' ($e.Name+'.json')))
    try{
      $e.Extract($m);$bytes=$m.ToArray();New-Item -ItemType Directory -Force -Path (Split-Path $rawPath),(Split-Path $jsonPath)|Out-Null
      [IO.File]::WriteAllBytes($rawPath,$bytes)
      foreach($parseBuffers in @($true,$false)){
        try{
          $m.Position=0;$resource=$null
          $res=([WolvenKit.RED4.Archive.IO.CR2WReader]::new($m)).ReadFile([ref]$resource,$parseBuffers)
          if($res.ToString() -ne 'NoError'){throw "CR2W $res"}
          $dto=[WolvenKit.Common.Conversion.RedFileDto]::new($resource,$false)
          $options=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new()
          [IO.File]::WriteAllText($jsonPath,[WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize($dto,$options),[Text.UTF8Encoding]::new($false))
          $decode=if($parseBuffers){'full'}else{'buffers_unparsed'};break
        }catch{$errorText=$_.Exception.Message}
      }
      $rows.Add([pscustomobject]@{Resource=$e.Name;Archive=$archivePath;Bytes=$bytes.Length;RawSha256=(Get-FileHash -LiteralPath $rawPath).Hash;Decode=$decode;FullDecodeError=$errorText;RawOutput=$rawPath;JsonOutput=if($decode){$jsonPath}else{$null}})
    }finally{$m.Dispose()}
  }
}
$rows | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $OutputRoot 'inventory.json') -Encoding utf8NoBOM
$rows | Select-Object Resource,Decode,Bytes | Format-Table -AutoSize
