$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
function ReadWorld([string]$path){
 $stream=[IO.File]::OpenRead($path)
 try{$reader=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($stream);$reader.add_ParsingError([WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($e)return ($e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs])});$file=$null;if($reader.ReadFile([ref]$file,$true).ToString() -cne 'NoError'){throw 'Read failed'};return $file}finally{$stream.Dispose()}
}
foreach($stem in @('quest_da3955dd67711180','quest_0b5baaafb70a2a64')){
 $raw=Join-Path $PSScriptRoot ('../extracted_01/basegame_3_nightcity.archive/'+$stem+'.streamingsector')
 $out=Join-Path $PSScriptRoot ($stem+'_native_01.json');if(Test-Path -LiteralPath $out){throw 'Preserve output'}
 $file=ReadWorld $raw;Export-Cr2wJson $file $out
}
