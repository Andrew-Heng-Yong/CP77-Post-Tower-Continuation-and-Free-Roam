param([string]$OutputRoot='research/phase2b_p4/staging_scan')
$ErrorActionPreference='Stop'
$wkStaging='C:\Users\Ayong\Documents\WolvenKit-8.20.0'
foreach($a in @('WolvenKit.Core.dll','WolvenKit.Common.dll','WolvenKit.RED4.dll')){[void][Reflection.Assembly]::LoadFrom((Join-Path $wkStaging $a))}
Add-Type -TypeDefinition 'using System; public static class P4StagingBytes { public static bool Has(byte[] a, byte[] b) { return System.MemoryExtensions.IndexOf<byte>(a.AsSpan(), b.AsSpan()) >= 0; } }'
$hsStaging=[WolvenKit.Common.Services.HashService]::new(); $hsStaging.Load()
$needles=[ordered]@{}
foreach($s in @('q307_zetatech','q307_entities','fb_sm_victor','wat_lch_dataterm_05')){$needles[$s]=[Text.Encoding]::UTF8.GetBytes($s)}
$hits=[Collections.Generic.List[object]]::new(); $counts=@{}; $failures=[Collections.Generic.List[object]]::new()
$rootStaging='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc'
New-Item -ItemType Directory -Force -Path $OutputRoot | Out-Null
foreach($folder in @('content','ep1')){foreach($f in Get-ChildItem (Join-Path $rootStaging $folder) -Filter '*.archive'){
    $arc=$null; $readArchive=([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($f.FullName,$hsStaging,[ref]$arc)
    if($readArchive.ToString() -ne 'NoError'){throw "Archive read failed: $($f.Name) $readArchive"}
    $entries=@($arc.Files.Values | Where-Object { $_.Name -match '\.(prefab|world|streamingblock|streamingsector|streamingsector_inplace)$' })
    $counts[$f.Name]=$entries.Count
    Write-Output "Scanning $($f.Name): $($entries.Count) resources"
    foreach($e in $entries){$m=[IO.MemoryStream]::new();try{
        $e.Extract($m); $bytes=$m.ToArray(); $matched=[Collections.Generic.List[string]]::new()
        foreach($k in $needles.Keys){if([P4StagingBytes]::Has($bytes,$needles[$k])){$matched.Add($k)}}
        if($matched.Count -gt 0){
            $archiveKey=[IO.Path]::GetFileNameWithoutExtension($f.Name)
            $rawPath=Join-Path $OutputRoot (Join-Path $archiveKey (Join-Path 'raw' $e.Name))
            $jsonPath=Join-Path $OutputRoot (Join-Path $archiveKey (Join-Path 'json' ($e.Name+'.json')))
            New-Item -ItemType Directory -Force -Path (Split-Path $rawPath),(Split-Path $jsonPath) | Out-Null
            [IO.File]::WriteAllBytes($rawPath,$bytes)
            $m.Position=0; $resource=$null
            $readResult=([WolvenKit.RED4.Archive.IO.CR2WReader]::new($m)).ReadFile([ref]$resource,$true)
            if($readResult.ToString() -ne 'NoError'){throw "CR2W read failed $readResult"}
            $dto=[WolvenKit.Common.Conversion.RedFileDto]::new($resource,$false)
            $options=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new()
            [IO.File]::WriteAllText($jsonPath,[WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize($dto,$options),[Text.UTF8Encoding]::new($false))
            $hits.Add([pscustomobject]@{Match=@($matched);Resource=$e.Name;Archive=$f.FullName;Bytes=$bytes.Length;RawSha256=(Get-FileHash -LiteralPath $rawPath).Hash;RawOutput=$rawPath;JsonOutput=$jsonPath})
        }
    }catch{$failures.Add([pscustomobject]@{Resource=$e.Name;Archive=$f.FullName;Error=$_.Exception.Message})}finally{$m.Dispose()}}
}}
@{Counts=$counts;Hits=$hits;Failures=$failures} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $OutputRoot 'inventory.json') -Encoding utf8NoBOM
$hits | Select-Object Match,Resource,Archive,Bytes | Format-Table -AutoSize
Write-Output "Matches $($hits.Count), failures $($failures.Count)"
