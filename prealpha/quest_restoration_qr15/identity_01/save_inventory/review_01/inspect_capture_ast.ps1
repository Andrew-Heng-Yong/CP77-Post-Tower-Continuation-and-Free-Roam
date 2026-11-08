# Parse capture03 as source code only; never invoke it or open the save it names.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$captureScript = Join-Path (Split-Path -Parent $PSScriptRoot) 'capture_03.ps1'
$output = Join-Path $PSScriptRoot 'capture_ast_01.json'
if (Test-Path -LiteralPath $output) { throw 'Fresh output required' }
$tokens = $null; $parseErrors = $null
$ast = [Management.Automation.Language.Parser]::ParseFile($captureScript,[ref]$tokens,[ref]$parseErrors)
if ($parseErrors.Count) { throw 'Capture script parse failed' }
$entryLoops = @($ast.FindAll({param($node) $node -is [Management.Automation.Language.ForEachStatementAst] -and $node.Variable.VariablePath.UserPath -eq 'entry' -and $node.Condition.Extent.Text -ceq '$ps.Entries'},$true))
if ($entryLoops.Count -ne 1) { throw 'Exact entry scan not found' }
$entryLoop = $entryLoops[0]
$candidateIfs = @($entryLoop.Body.FindAll({param($node) $node -is [Management.Automation.Language.IfStatementAst] -and $node.Clauses[0].Item1.Extent.Text -ceq '$row.id_u64 -in $candidateKeys'},$true))
if ($candidateIfs.Count -ne 1) { throw 'Exact candidate condition not found' }
$candidateIf = $candidateIfs[0]
$candidateAssignments = @($ast.FindAll({param($node) $node -is [Management.Automation.Language.AssignmentStatementAst] -and $node.Left.Extent.Text -ieq '$candidateKeys'},$true))
$listAssignments = @($ast.FindAll({param($node) $node -is [Management.Automation.Language.AssignmentStatementAst] -and $node.Left.Extent.Text -ieq '$candidateMatches'},$true))
if ($candidateAssignments.Count -ne 1 -or $listAssignments.Count -ne 1) { throw 'Candidate definitions changed' }
$keys = @($candidateAssignments[0].Right.FindAll({param($node) $node -is [Management.Automation.Language.StringConstantExpressionAst]},$true) | ForEach-Object {$_.Value})
$matchVariables = @($ast.FindAll({param($node) $node -is [Management.Automation.Language.VariableExpressionAst] -and $node.VariablePath.UserPath -ieq 'Matches'},$true))
$guardTexts = @($ast.FindAll({param($node) $node -is [Management.Automation.Language.IfStatementAst] -and $node.Extent.Text -match "throw '(Historical body changed|Unstable source|Input changed during capture)'"},$true) | ForEach-Object {$_.Extent.Text})
$result = @{
 status='STATIC_POWERSHELL_AST_REVIEW';source=$captureScript;source_sha256=(Get-FileHash -LiteralPath $captureScript).Hash
 parse_errors=$parseErrors.Count;entry_loop=$entryLoop.Condition.Extent.Text
 candidate_keys=$keys;candidate_condition=$candidateIf.Clauses[0].Item1.Extent.Text
 candidate_if_direct_child_of_full_entry_loop=[object]::ReferenceEquals($candidateIf.Parent,$entryLoop.Body)
 candidate_body=$candidateIf.Clauses[0].Item2.Extent.Text
 candidate_list_constructor=$listAssignments[0].Right.Extent.Text
 automatic_matches_variable_references=$matchVariables.Count
 recorded_source_hash_guards=$guardTexts
 save_reads=0;capture_invocations=0;game_calls=0;runtime_changes=0
}
$result | ConvertTo-Json -Depth 7 | Set-Content -LiteralPath $output -Encoding utf8NoBOM
$result | Select-Object status,parse_errors,candidate_keys,candidate_if_direct_child_of_full_entry_loop,automatic_matches_variable_references,save_reads,capture_invocations | ConvertTo-Json -Depth 5
