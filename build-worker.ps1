# Builds worker.js (ONE file, ready to paste into Cloudflare)
# by embedding index.html and the user guide page into worker.src.js.
# Keep index.html, the guide .html, worker.src.js and this script in the same folder.
# (The guide is the one other .html file in the folder. If there is none, it is left out.)
$ErrorActionPreference = 'Stop'

$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
$utf8 = New-Object System.Text.UTF8Encoding($false)
$srcPath = Join-Path $dir 'worker.src.js'
$htmlPath = Join-Path $dir 'index.html'
$outPath = Join-Path $dir 'worker.js'

foreach ($p in @($srcPath, $htmlPath)) {
  if (-not (Test-Path -LiteralPath $p)) { throw "File not found: $p" }
}

# A page becomes a JavaScript string, written as a list of short pieces.
function ConvertTo-JsArray([string]$text) {
  $sb = New-Object System.Text.StringBuilder
  $size = 1000
  $i = 0
  while ($i -lt $text.Length) {
    $n = [Math]::Min($size, $text.Length - $i)
    # never cut between the two halves of a surrogate pair (emoji)
    if ($n -gt 1 -and [char]::IsHighSurrogate($text[$i + $n - 1])) { $n = $n - 1 }
    $chunk = $text.Substring($i, $n)
    $i = $i + $n
    $chunk = $chunk.Replace('\', '\\').Replace('"', '\"')
    $chunk = $chunk.Replace("`r", '\r').Replace("`n", '\n')
    $chunk = $chunk.Replace([string][char]0x2028, ' ').Replace([string][char]0x2029, ' ')
    $null = $sb.Append('  "')
    $null = $sb.Append($chunk)
    $null = $sb.AppendLine('",')
  }
  return '[' + "`n" + $sb.ToString() + "].join('')"
}

$src = [IO.File]::ReadAllText($srcPath, $utf8)
$markIndex = 'const PAGE_HTML = __INDEX_HTML__;'
$markGuide = 'const GUIDE_HTML = __GUIDE_HTML__;'
foreach ($m in @($markIndex, $markGuide)) {
  if (-not $src.Contains($m)) { throw "worker.src.js does not contain: $m (use the newest worker.src.js)" }
}

$indexJs = ConvertTo-JsArray ([IO.File]::ReadAllText($htmlPath, $utf8))

$guideJs = "''"
$guideName = '(none)'
$others = @(Get-ChildItem -LiteralPath $dir -Filter '*.html' -File | Where-Object { $_.Name -ne 'index.html' })
if ($others.Count -eq 1) {
  $guideJs = ConvertTo-JsArray ([IO.File]::ReadAllText($others[0].FullName, $utf8))
  $guideName = $others[0].Name
} elseif ($others.Count -gt 1) {
  Write-Host 'WARNING: more than one other .html file found, the guide was NOT embedded.'
  Write-Host '         Keep only index.html and the guide .html in this folder, then run again.'
}

$out = $src.Replace($markIndex, 'const PAGE_HTML = ' + $indexJs + ';')
$out = $out.Replace($markGuide, 'const GUIDE_HTML = ' + $guideJs + ';')
[IO.File]::WriteAllText($outPath, $out, $utf8)

$kb = [Math]::Round((Get-Item -LiteralPath $outPath).Length / 1024)
Write-Host ''
Write-Host "OK: worker.js created ($kb KB)"
Write-Host "  page : index.html"
Write-Host "  guide: $guideName"
Write-Host "Location: $outPath"
Write-Host 'Next: open worker.js, copy everything, paste it into the Cloudflare Worker editor, then Deploy.'
