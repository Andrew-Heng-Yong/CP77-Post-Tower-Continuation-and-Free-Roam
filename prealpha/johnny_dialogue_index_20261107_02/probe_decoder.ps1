Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$output=Join-Path $PSScriptRoot 'evidence_02'
if(Test-Path -LiteralPath $output){throw 'Use fresh decoder probe evidence'}
$capture=Get-Content -LiteralPath (Join-Path $workspace 'prealpha/johnny_dialogue_removal_20261107_01/step1_01/capture.json') -Raw | ConvertFrom-Json -Depth 100
$source=@($capture.resources | Where-Object {$_.depot -ceq 'ep1\quest\main_quests\q303\scenes\q303_10_concert_braindance.scene'})
if($source.Count -ne 1){throw 'Expected one exact opaque scene provider'}
if((Get-FileHash -LiteralPath $source[0].raw).Hash -cne $source[0].sha256){throw 'Opaque raw source changed'}
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$attempts=@(foreach($parseBuffers in @($true,$false)){
    $stream=[IO.File]::OpenRead($source[0].raw)
    try{
        $reader=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($stream)
        $resource=$null
        $code=$reader.ReadFile([ref]$resource,$parseBuffers)
        @{parse_buffers=$parseBuffers;code=$code.ToString();error=$null;root_type=if($resource){$resource.RootChunk.GetType().Name}else{$null}}
    }catch{
        @{parse_buffers=$parseBuffers;code='EXCEPTION';error=$_.Exception.Message;root_type=$null}
    }finally{$stream.Dispose()}
})
New-Item -ItemType Directory -Path $output | Out-Null
@{depot=$source[0].depot;archive=$source[0].archive;raw=$source[0].raw;sha256=$source[0].sha256;
reader_assembly=[WolvenKit.RED4.Archive.IO.CR2WReader].Assembly.FullName;
attempts=$attempts;status='DECODE_HOLD_UNLESS_SUPPORTED_FULL_DECODE_SUCCEEDS';
next_action='Keep exact raw bytes and recovered import tables. No lossy decoder workaround or synthesized dialogue is approved.';
game_writes=0;save_writes=0} | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $output 'decoder_probe.json') -Encoding utf8NoBOM
$attempts | ConvertTo-Json -Depth 8
