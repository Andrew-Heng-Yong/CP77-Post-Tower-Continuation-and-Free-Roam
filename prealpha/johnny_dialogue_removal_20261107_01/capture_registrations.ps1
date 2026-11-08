Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$output = Join-Path $PSScriptRoot 'step1_01/registrations_structured.json'
if (Test-Path -LiteralPath $output) { throw 'Use a fresh registration output' }
[void][Reflection.Assembly]::LoadFrom((Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package/YamlDotNet.dll'))
$entries = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'step1_01/entry_sources.json') -Raw | ConvertFrom-Json -Depth 100
$rows = [Collections.Generic.List[object]]::new()
$errors = [Collections.Generic.List[object]]::new()
$files = [Collections.Generic.List[object]]::new()

function Convert-YamlNode($node) {
    if ($node -is [YamlDotNet.RepresentationModel.YamlScalarNode]) { return $node.Value }
    if ($node -is [YamlDotNet.RepresentationModel.YamlSequenceNode]) {
        $values = @($node.Children | ForEach-Object { Convert-YamlNode $_ })
        return ,$values
    }
    if ($node -is [YamlDotNet.RepresentationModel.YamlMappingNode]) {
        $mapping = [ordered]@{}
        foreach ($item in $node.Children.GetEnumerator()) {
            $mapping[$item.Key.Value] = Convert-YamlNode $item.Value
        }
        return $mapping
    }
    throw "Unsupported YAML node $($node.GetType().FullName)"
}

foreach ($file in $entries.source_files | Where-Object { $_.path.EndsWith('.xl') }) {
    $actualHash = (Get-FileHash -LiteralPath $file.path).Hash
    if ($actualHash -cne $file.sha256) { throw "XL input changed $($file.path)" }
    $files.Add(@{ path=$file.path; sha256=$actualHash })
    try {
        $yaml = [YamlDotNet.RepresentationModel.YamlStream]::new()
        $reader = [IO.StringReader]::new([IO.File]::ReadAllText($file.path))
        try { $yaml.Load($reader) } finally { $reader.Dispose() }
        $documentIndex = 0
        foreach ($document in $yaml.Documents) {
            $data = Convert-YamlNode $document.RootNode
            if ($data.Contains('quest')) {
                $quest = $data['quest']
                if ($quest.Contains('phases')) {
                    $ordinal = 0
                    foreach ($phase in $quest['phases']) {
                        if (!$phase.Contains('path') -or !$phase.Contains('parent')) {
                            $errors.Add(@{ file=$file.path; document=$documentIndex; ordinal=$ordinal; error='PHASE_PATH_OR_PARENT_MISSING'; value=$phase })
                        } else {
                            $rows.Add(@{ file=$file.path; sha256=$actualHash; document=$documentIndex; ordinal=$ordinal; binding=$phase })
                        }
                        $ordinal++
                    }
                } else {
                    $errors.Add(@{ file=$file.path; document=$documentIndex; error='QUEST_PHASES_MISSING'; value=$quest })
                }
            }
            $documentIndex++
        }
    } catch {
        $errors.Add(@{ file=$file.path; error=$_.Exception.Message })
    }
}
@{
    schema=1; parser='YamlDotNet representation model'; files=$files.ToArray();
    phase_bindings=$rows.ToArray(); errors=$errors.ToArray();
    scope='Preserves each registration mapping and ordered connection/input/output values without inferring runtime attachment.';
    parser_assembly_sha256=(Get-FileHash -LiteralPath (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package/YamlDotNet.dll')).Hash
} | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $output -Encoding utf8NoBOM
@{ files=$files.Count; bindings=$rows.Count; errors=$errors.Count } | ConvertTo-Json -Compress
