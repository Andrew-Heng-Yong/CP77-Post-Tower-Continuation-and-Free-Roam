param([string]$Revision='presentation_01')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$WorkspaceRoot=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
if($Revision -cnotmatch '^presentation_\d{2}$'){throw 'Bad revision'}
$out=Join-Path $PSScriptRoot ('build/'+$Revision)
$python='C:\Users\Ayong\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $python (Join-Path $PSScriptRoot 'prepare_01.py') $out
if($LASTEXITCODE -ne 0){throw 'Presentation preparation failed'}
. (Join-Path $WorkspaceRoot 'tools/build_phase2a.ps1') -HelpersOnly
$plan=Get-Content -LiteralPath (Join-Path $out 'prepared.json') -Raw|ConvertFrom-Json -Depth 100
$resources=[ordered]@{}
$options=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new()
foreach($input in $plan.inputs){
 $json=Get-Content -LiteralPath (Join-Path $WorkspaceRoot $input.expected) -Raw
 $dto=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Deserialize([WolvenKit.Common.Conversion.RedFileDto],$json,$options)
 $raw=Join-Path (Join-Path $out 'source') $input.depot
 Write-Cr2wFile $dto.Data $raw
 $readback=Join-Path (Join-Path $out 'readback') ($input.depot+'.json')
 New-Item -ItemType Directory -Force (Split-Path $readback -Parent)|Out-Null
 Export-Cr2wJson (Read-Cr2wFile $raw) $readback
 $resources[$input.depot]=(Get-FileHash -LiteralPath $raw).Hash
}
$component=[ordered]@{status='EXPORTED_U10_PRESENTATION_NOT_INSTALLED';resources=$resources;boots=@();source_pins=$plan.source_pins;inputs=$plan.inputs;reference_replacements=$plan.reference_replacements;main_replacement=$plan.main_replacement;native_overrides=@();prepared_sha256=(Get-FileHash -LiteralPath (Join-Path $out 'prepared.json')).Hash}
[IO.File]::WriteAllText((Join-Path $out 'component.json'),($component|ConvertTo-Json -Depth 100),[Text.UTF8Encoding]::new($false))
& $python (Join-Path $PSScriptRoot 'test_01.py') $out
if($LASTEXITCODE -ne 0){throw 'Presentation validation failed'}
@{status=$component.status;resources=$resources.Count;build=$out}|ConvertTo-Json
