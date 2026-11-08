# Read managed method bodies only. No save read/write, native call or game process access.
param([ValidatePattern('^[a-z0-9_]+\.json$')][string]$OutputName = 'quest_reader_il_01.json', [switch]$IncludeCompression)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$output = Join-Path $PSScriptRoot $OutputName
if (Test-Path -LiteralPath $output) { throw 'Fresh output required' }
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$opcodes = @{}
foreach ($field in [Reflection.Emit.OpCodes].GetFields([Reflection.BindingFlags]'Static,Public')) {
    $opcode = $field.GetValue($null)
    if ($opcode -is [Reflection.Emit.OpCode]) { $opcodes[([int]$opcode.Value -band 0xFFFF)] = $opcode }
}
function Read-MethodIL([Reflection.MethodBase]$Method) {
    $il = $Method.GetMethodBody().GetILAsByteArray()
    $position = 0
    $rows = [Collections.Generic.List[object]]::new()
    while ($position -lt $il.Length) {
        $offset = $position
        $code = [int]$il[$position++]
        if ($code -eq 0xFE) { $code = 0xFE00 + [int]$il[$position++] }
        if (-not $opcodes.ContainsKey($code)) { throw "Unknown opcode at $offset" }
        $op = $opcodes[$code]
        $kind = $op.OperandType.ToString()
        $size = switch ($kind) {
            'InlineNone' { 0 }; 'ShortInlineVar' { 1 }; 'ShortInlineI' { 1 }; 'ShortInlineBrTarget' { 1 }
            'InlineVar' { 2 }; 'InlineI8' { 8 }; 'InlineR' { 8 }
            'InlineSwitch' { 4 + 4 * [BitConverter]::ToInt32($il, $position) }
            default { 4 }
        }
        if ($size -lt 0 -or $position + $size -gt $il.Length) { throw 'Malformed managed method body' }
        $operand = if ($size) { [Convert]::ToHexString($il[$position..($position + $size - 1)]) } else { '' }
        if ($kind -in @('InlineField','InlineMethod','InlineTok','InlineType')) {
            $operand = $Method.Module.ResolveMember([BitConverter]::ToInt32($il, $position)).ToString()
        } elseif ($kind -eq 'InlineString') {
            $operand = $Method.Module.ResolveString([BitConverter]::ToInt32($il, $position))
        } elseif ($kind -eq 'InlineI') { $operand = [BitConverter]::ToInt32($il, $position) }
        elseif ($kind -eq 'ShortInlineI') { $operand = [int]$il[$position]; if ($operand -gt 127) { $operand -= 256 } }
        elseif ($kind -eq 'InlineBrTarget') { $operand = $position + $size + [BitConverter]::ToInt32($il, $position) }
        elseif ($kind -eq 'ShortInlineBrTarget') { $delta = [int]$il[$position]; if ($delta -gt 127) { $delta -= 256 }; $operand = $position + $size + $delta }
        $position += $size
        $rows.Add(@{ offset = $offset; opcode = $op.Name; operand = $operand })
    }
    @{ type = $Method.DeclaringType.FullName; method = $Method.ToString(); il_hex = [Convert]::ToHexString($il); instructions = $rows; decoded_bytes = $position }
}
$assembly = [WolvenKit.RED4.Save.IO.CyberpunkSaveReader].Assembly
$selection = @{
    'WolvenKit.RED4.Save.IO.CyberpunkSaveReader' = @('ReadFile','LoadFromStream','get_BaseStream')
    'WolvenKit.RED4.Save.ParserHelper' = @('ReadNode','ReadChildren')
    'WolvenKit.RED4.Save.QuestSystemParser' = @('Read')
}
if ($IncludeCompression) { $selection['WolvenKit.RED4.Save.Compression'] = @('Decompress') }
$methods = @()
foreach ($typeName in $selection.Keys | Sort-Object) {
    foreach ($method in $assembly.GetType($typeName).GetMethods([Reflection.BindingFlags]'Instance,Static,Public,NonPublic,DeclaredOnly')) {
        if ($method.Name -in $selection[$typeName]) { $methods += Read-MethodIL $method }
    }
}
@{ assembly = $assembly.Location; assembly_sha256 = (Get-FileHash -LiteralPath $assembly.Location).Hash; status = 'MANAGED_READER_IL_SOURCE_EVIDENCE'; game_calls = 0; save_reads = 0; methods = $methods } |
    ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $output -Encoding utf8NoBOM
@{ methods = $methods.Count; output = $output } | ConvertTo-Json
