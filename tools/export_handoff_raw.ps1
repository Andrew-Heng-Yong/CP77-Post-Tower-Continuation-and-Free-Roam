param(
    [Parameter(Mandatory=$true)][string]$InputRaw,
    [Parameter(Mandatory=$true)][string]$JsonOutput
)
$ErrorActionPreference='Stop'
$wkHandoff='C:\Users\Ayong\Documents\WolvenKit-8.20.0'
foreach($assembly in @('WolvenKit.Core.dll','WolvenKit.Common.dll','WolvenKit.RED4.dll')) {
    [void][Reflection.Assembly]::LoadFrom((Join-Path $wkHandoff $assembly))
}
$hsHandoff=[WolvenKit.Common.Services.HashService]::new();$hsHandoff.Load()
$script:acceptedDefaultValues=0
$handler=[WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($errorArgs)
    # Only accept a value which decoded correctly but is redundantly serialized.
    # CR2WReader.ReadVariable preserves that decoded value after this callback.
    if($errorArgs -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs]) {
        $script:acceptedDefaultValues++
        return $true
    }
    return $false
}
$stream=[IO.File]::OpenRead((Resolve-Path -LiteralPath $InputRaw))
try {
    $reader=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($stream)
    $reader.add_ParsingError($handler)
    $file=$null
    $result=$reader.ReadFile([ref]$file,$true)
    if($result.ToString() -ne 'NoError'){throw "Read failure: $result"}
    $dto=[WolvenKit.Common.Conversion.RedFileDto]::new($file,$false)
    $options=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new()
    $json=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize($dto,$options)
    New-Item -ItemType Directory -Force -Path (Split-Path $JsonOutput) | Out-Null
    [IO.File]::WriteAllText($JsonOutput,$json,[Text.UTF8Encoding]::new($false))
    $metadata=[ordered]@{
        InputRaw=(Resolve-Path -LiteralPath $InputRaw).Path
        RawSha256=(Get-FileHash -LiteralPath $InputRaw -Algorithm SHA256).Hash
        JsonOutput=(Resolve-Path -LiteralPath $JsonOutput).Path
        RootType=$file.RootChunk.GetType().Name
        AcceptedRedundantDefaults=$script:acceptedDefaultValues
        Policy='Only InvalidDefaultValueEventArgs accepted; decoded field values retained. Other errors rejected.'
        Reference='https://github.com/WolvenKit/WolvenKit/blob/main/WolvenKit.RED4/Archive/IO/CR2WReader.cs'
    }
    $metadata | ConvertTo-Json | Set-Content -LiteralPath ($JsonOutput+'.provenance.json') -Encoding utf8NoBOM
    $metadata | ConvertTo-Json
} finally {$stream.Dispose()}
