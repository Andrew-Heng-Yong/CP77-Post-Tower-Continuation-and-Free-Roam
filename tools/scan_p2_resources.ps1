param([string]$OutputPath='research/phase2b_p2/resource_hits.json')
$ErrorActionPreference='Stop'
$wkP2='C:\Users\Ayong\Documents\WolvenKit-8.20.0'
foreach($a in @('WolvenKit.Core.dll','WolvenKit.Common.dll','WolvenKit.RED4.dll')){[void][Reflection.Assembly]::LoadFrom((Join-Path $wkP2 $a))}
Add-Type -TypeDefinition 'using System; public static class P2Bytes { public static bool Has(byte[] a, byte[] b) { return System.MemoryExtensions.IndexOf<byte>(a.AsSpan(), b.AsSpan()) >= 0; } }' -ErrorAction Stop
$hsP2=[WolvenKit.Common.Services.HashService]::new(); $hsP2.Load()
$needles=[ordered]@{}
foreach($s in @('05_take_walk','q307_tomorrow','q115_dvc_ripperdoc_room_door')){$needles[$s]=[Text.Encoding]::UTF8.GetBytes($s)}
$needles['door_entity_id']=[BitConverter]::GetBytes([uint64]13806931541592989805)
$needles['gate_entity_id']=[BitConverter]::GetBytes([uint64]6805700156449448318)
$hits=[Collections.Generic.List[object]]::new(); $counts=@{}; $failures=[Collections.Generic.List[object]]::new()
$root='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc'
foreach($folder in @('content','ep1')){foreach($f in Get-ChildItem (Join-Path $root $folder) -Filter '*.archive'){
    $arc=$null; [void]([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($f.FullName,$hsP2,[ref]$arc)
    $entries=@($arc.Files.Values | Where-Object { $_.Name -match '\.(scene|quest|questphase|streamingsector|streamingsector_inplace)$' })
    $counts[$f.Name]=$entries.Count
    Write-Output "Scanning $($f.Name): $($entries.Count) resources"
    foreach($e in $entries){$m=[IO.MemoryStream]::new();try{
        $e.Extract($m); $bytes=$m.ToArray()
        foreach($k in $needles.Keys){if([P2Bytes]::Has($bytes,$needles[$k])){$hits.Add([pscustomobject]@{Match=$k;Resource=$e.Name;Archive=$f.FullName;Bytes=$bytes.Length})}}
    }catch{$failures.Add([pscustomobject]@{Resource=$e.Name;Error=$_.Exception.Message})}finally{$m.Dispose()}}
}}
New-Item -ItemType Directory -Force -Path (Split-Path $OutputPath) | Out-Null
@{Counts=$counts;Hits=$hits;Failures=$failures} | ConvertTo-Json -Depth 6 | Set-Content $OutputPath -Encoding utf8NoBOM
$hits | Format-Table Match,Resource -AutoSize
