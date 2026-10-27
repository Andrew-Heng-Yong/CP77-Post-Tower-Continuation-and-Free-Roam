Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$manifest=Get-Content (Join-Path $PSScriptRoot 'prepared_02/manifest.json') -Raw|ConvertFrom-Json -Depth 100
$out=Join-Path $PSScriptRoot 'serialized_02';if(Test-Path $out){throw 'Successor required'}
New-Item -ItemType Directory $out|Out-Null
$opt=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new();$items=@()
foreach($v in $manifest.resources){
 $path=Join-Path $ws $v.prepared
 $dto=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Deserialize([WolvenKit.Common.Conversion.RedFileDto],(Get-Content -LiteralPath $path -Raw),$opt)
 $raw=Join-Path $out ('source/'+$v.private);New-Item -ItemType Directory (Split-Path $raw -Parent) -Force|Out-Null
 $file=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$file.RootChunk=$dto.Data.RootChunk
 Write-Cr2wFile $file $raw
 $readback=Join-Path $out ('readback/'+$v.private+'.json');New-Item -ItemType Directory (Split-Path $readback -Parent) -Force|Out-Null
 Export-Cr2wJson (Read-Cr2wFile $raw) $readback
 $items+=,@{native=$v.native;private=$v.private;sha256=(Get-FileHash $raw).Hash;readback_sha256=(Get-FileHash $readback).Hash}
}
$m=@{status='SERIALIZED_NOT_INSTALLED';resources=$items;prepared_manifest_sha256=(Get-FileHash (Join-Path $PSScriptRoot 'prepared_02/manifest.json')).Hash}
[IO.File]::WriteAllText((Join-Path $out 'manifest.json'),($m|ConvertTo-Json -Depth 50),[Text.UTF8Encoding]::new($false))
@{resources=$items.Count;output=$out}|ConvertTo-Json
