param([Parameter(Mandatory=$true)][string]$OutputDirectory,[switch]$IncludeNativeHelper)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=(Resolve-Path (Join-Path $PSScriptRoot '../../../../..')).Path
$out=[IO.Path]::GetFullPath($OutputDirectory)
if(Test-Path -LiteralPath $out){throw 'Fresh output required'}
if(-not $out.StartsWith((Join-Path $ws 'prealpha/quest_restoration_qr4/groups/G10/reviews'),[StringComparison]::OrdinalIgnoreCase)){throw 'Review output containment'}
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$capture=Get-Content -Raw -LiteralPath (Join-Path $ws 'prealpha/quest_restoration_qr4/groups/G08/regina_world_01/capture.json')|ConvertFrom-Json -Depth 100
[IO.Directory]::CreateDirectory($out)|Out-Null
$rows=@()
foreach($block in $capture.blocks){
 if((Get-FileHash -LiteralPath $block.raw).Hash -ne $block.sha256){throw 'Pinned block changed'}
 if($block.matching_descriptors -eq 0){continue}
 $r=Read-Cr2wFile $block.raw;$matches=@()
 foreach($desc in $r.RootChunk.Descriptors){
  $text=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize($desc,[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new())
  if($text.Contains('mq007_pr_gun_return') -or ($IncludeNativeHelper -and $text.Contains('mq007_pr_gun_re_acquiring'))){$matches+=,($text|ConvertFrom-Json -Depth 100)}
 }
 if(-not $IncludeNativeHelper -and $matches.Count -ne 1){throw 'Expected exact one return descriptor per pinned native block'}
 foreach($definition in $matches){$rows+=,@{binary=$block.raw;sha256=(Get-FileHash -LiteralPath $block.raw).Hash;archive=$block.archive;definition=$definition}}
}
foreach($hit in $capture.hits){if((Get-FileHash -LiteralPath $hit.raw).Hash -ne $hit.sha256){throw 'Pinned sector payload changed'}}
@{status='INDEPENDENT_ACTUAL_BINARY_DESCRIPTOR_READBACK';sources=$rows;sector_pins=$capture.hits;runtime_changes=@()}|ConvertTo-Json -Depth 100|Set-Content -LiteralPath (Join-Path $out 'descriptors.json') -Encoding utf8NoBOM
@{descriptors=$rows.Count;output=$out}|ConvertTo-Json
