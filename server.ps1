# Local helper for index.html.
# Serves this folder at http://localhost:8800/ and fetches pages/images from HomePro,
# Traphet and Eco door on the page's behalf (those sites block cross-site requests).
# Only this computer can reach it, and only the listed shop websites can be fetched.
param([int]$Port = 8800, [switch]$NoBrowser)

$root = (Split-Path -Parent $MyInvocation.MyCommand.Path).TrimEnd('\') + '\'
try { [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12 } catch { }
Add-Type -AssemblyName System.Net.Http

$handler = New-Object System.Net.Http.HttpClientHandler
$handler.AutomaticDecompression = [System.Net.DecompressionMethods]::GZip -bor [System.Net.DecompressionMethods]::Deflate
$client = New-Object System.Net.Http.HttpClient($handler)
$client.Timeout = [TimeSpan]::FromSeconds(25)
[void]$client.DefaultRequestHeaders.TryAddWithoutValidation('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36')
[void]$client.DefaultRequestHeaders.TryAddWithoutValidation('Accept-Language', 'th-TH,th;q=0.9,en;q=0.8')

$allowedHosts = @(
  'www.boonthavorn.com',
  'www.homepro.co.th', 'homepro.co.th', 'statice.homepro.co.th',
  'traphet.com', 'www.traphet.com',
  'www.eco-door.net', 'eco-door.net'
)
$types = @{
  '.html' = 'text/html; charset=utf-8'; '.js' = 'text/javascript; charset=utf-8'; '.css' = 'text/css; charset=utf-8'
  '.json' = 'application/json'; '.png' = 'image/png'; '.jpg' = 'image/jpeg'; '.jpeg' = 'image/jpeg'
  '.svg' = 'image/svg+xml'; '.ico' = 'image/x-icon'; '.md' = 'text/plain; charset=utf-8'
}

# Already running (start.bat opened twice)? Just show the page again.
try {
  $probe = New-Object System.Net.Http.HttpClient
  $probe.Timeout = [TimeSpan]::FromSeconds(2)
  if ($probe.GetStringAsync("http://localhost:$Port/proxy-status").Result -eq 'ok') {
    Write-Host "  The helper is already running. Opening http://localhost:$Port/ ..."
    if (-not $NoBrowser) { Start-Process "http://localhost:$Port/" }
    Start-Sleep -Seconds 2
    exit 2
  }
} catch { }

# Find a free port.
$listener = $null
for ($p = $Port; $p -lt $Port + 10; $p++) {
  try {
    $candidate = New-Object System.Net.HttpListener
    $candidate.Prefixes.Add("http://localhost:$p/")
    $candidate.Start()
    $listener = $candidate
    $Port = $p
    break
  } catch { }
}
if (-not $listener) {
  Write-Host "Could not open a local port ($Port-$($Port + 9)). Close other copies of this window and try again."
  exit 1
}

$url = "http://localhost:$Port/"
Write-Host ""
Write-Host "  Material Selection helper is running at $url"
Write-Host ""
Write-Host "  - The page opens in your browser by itself."
Write-Host "    If it does not, type $url into the browser's address bar."
Write-Host "  - Keep this window open while using the page (you can minimise it)."
Write-Host "  - Close this window when you are done."
Write-Host ""
if (-not $NoBrowser) { Start-Process $url }

$utf8 = New-Object System.Text.UTF8Encoding($false)
# Customer projects are saved here, one file per project (plus a small summary file).
$projectsDir = Join-Path $root 'projects'

# $shared = $false keeps a response private to this page (no cross-site access header).
function Send-Response($ctx, [int]$status, [byte[]]$body, [string]$type, [bool]$shared = $true) {
  $res = $ctx.Response
  $res.StatusCode = $status
  if ($type) { $res.ContentType = $type }
  if ($shared) { $res.Headers['Access-Control-Allow-Origin'] = '*' }
  $res.Headers['Cache-Control'] = 'no-store'
  if ($body) {
    $res.ContentLength64 = $body.Length
    if ($ctx.Request.HttpMethod -ne 'HEAD') { $res.OutputStream.Write($body, 0, $body.Length) }
  }
  $res.Close()
}

function Send-Text($ctx, [int]$status, [string]$text, [bool]$shared = $true) {
  Send-Response $ctx $status ([Text.Encoding]::UTF8.GetBytes($text)) 'text/plain; charset=utf-8' $shared
}

# Project data is only for this page: the request must come to localhost and carry the
# page's own header (other websites can't add it without the browser blocking them).
function Test-PageRequest($ctx) {
  $req = $ctx.Request
  return ($req.Headers['Host'] -in @("localhost:$Port", "127.0.0.1:$Port")) -and ($req.Headers['X-KS-App'] -eq '1')
}

function Handle-Projects($ctx, [string]$path) {
  if (-not (Test-PageRequest $ctx)) { Send-Text $ctx 403 'Forbidden' $false; return }
  $method = $ctx.Request.HttpMethod
  $parts = @($path.Substring('/api/projects'.Length).Split('/') | Where-Object { $_ })

  if ($parts.Count -eq 0) {
    # List: the summary files joined into one JSON array.
    $metas = @()
    if (Test-Path -LiteralPath $projectsDir) {
      $metas = @(Get-ChildItem -LiteralPath $projectsDir -Filter '*.meta.json' -File | ForEach-Object { [IO.File]::ReadAllText($_.FullName, $utf8) })
    }
    $list = $utf8.GetBytes('[' + ($metas -join ',') + ']')
    Send-Response $ctx 200 $list 'application/json; charset=utf-8' $false
    return
  }

  $id = $parts[0]
  if ($id -cnotmatch '^[a-z0-9-]{3,64}$') { Send-Text $ctx 400 'Bad project id' $false; return }
  $dataFile = Join-Path $projectsDir "$id.json"
  $metaFile = Join-Path $projectsDir "$id.meta.json"

  if ($method -eq 'GET' -and $parts.Count -eq 1) {
    if (Test-Path -LiteralPath $dataFile) { Send-Response $ctx 200 ([IO.File]::ReadAllBytes($dataFile)) 'application/json; charset=utf-8' $false }
    else { Send-Text $ctx 404 'Not found' $false }
    return
  }
  if ($method -eq 'PUT') {
    New-Item -ItemType Directory -Force $projectsDir | Out-Null
    $buffer = New-Object System.IO.MemoryStream
    $ctx.Request.InputStream.CopyTo($buffer)
    $target = if ($parts.Count -ge 2 -and $parts[1] -eq 'meta') { $metaFile } else { $dataFile }
    # Write to a temporary file first so a crash never leaves a half-written project.
    $tmp = "$target.tmp"
    [IO.File]::WriteAllBytes($tmp, $buffer.ToArray())
    [IO.File]::Copy($tmp, $target, $true)
    [IO.File]::Delete($tmp)
    # The page sends the project's summary in a header with each save.
    $metaHeader = $ctx.Request.Headers['X-KS-Meta']
    if ($metaHeader -and $target -eq $dataFile) { [IO.File]::WriteAllText($metaFile, [Uri]::UnescapeDataString($metaHeader), $utf8) }
    Send-Text $ctx 200 'saved' $false
    return
  }
  if ($method -eq 'DELETE' -and $parts.Count -eq 1) {
    # Deleted projects are kept in projects\deleted so they can be restored by hand.
    $trash = Join-Path $projectsDir 'deleted'
    New-Item -ItemType Directory -Force $trash | Out-Null
    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    foreach ($f in @($dataFile, $metaFile)) {
      if (Test-Path -LiteralPath $f) { [IO.File]::Move($f, (Join-Path $trash ("$stamp-" + [IO.Path]::GetFileName($f)))) }
    }
    Send-Text $ctx 200 'deleted' $false
    return
  }
  Send-Text $ctx 405 'Method not allowed' $false
}

while ($listener.IsListening) {
  try { $ctx = $listener.GetContext() } catch { break }
  try {
    $path = $ctx.Request.Url.AbsolutePath

    if ($path -eq '/proxy-status') { Send-Text $ctx 200 'ok'; continue }

    if ($path -eq '/api/projects' -or $path.StartsWith('/api/projects/')) { Handle-Projects $ctx $path; continue }

    if ($path -eq '/proxy') {
      # Read ?url= from the raw query so Thai characters decode as UTF-8.
      $raw = $ctx.Request.RawUrl
      $i = $raw.IndexOf('url=')
      $target = if ($i -ge 0) { [Uri]::UnescapeDataString($raw.Substring($i + 4).Split('&')[0]) } else { '' }
      $uri = $null
      if (-not $target -or -not [Uri]::TryCreate($target, [UriKind]::Absolute, [ref]$uri) -or $uri.Scheme -ne 'https' -or ($allowedHosts -notcontains $uri.Host)) {
        Send-Text $ctx 403 'This address is not allowed.'
        continue
      }
      $resp = $client.GetAsync($uri).Result
      $bytes = $resp.Content.ReadAsByteArrayAsync().Result
      $ctype = if ($resp.Content.Headers.ContentType) { $resp.Content.Headers.ContentType.ToString() } else { 'application/octet-stream' }
      Write-Host ("  {0}  {1}" -f [int]$resp.StatusCode, $uri.Host)
      Send-Response $ctx ([int]$resp.StatusCode) $bytes $ctype
      continue
    }

    # Static files from this folder.
    $rel = [Uri]::UnescapeDataString($path.TrimStart('/'))
    if (-not $rel) { $rel = 'index.html' }
    $file = [IO.Path]::GetFullPath((Join-Path $root $rel))
    $inProjects = $file.StartsWith($projectsDir + '\', [StringComparison]::OrdinalIgnoreCase)
    if (-not $inProjects -and $file.StartsWith($root, [StringComparison]::OrdinalIgnoreCase) -and (Test-Path -LiteralPath $file -PathType Leaf)) {
      $type = $types[[IO.Path]::GetExtension($file).ToLower()]
      if (-not $type) { $type = 'application/octet-stream' }
      Send-Response $ctx 200 ([IO.File]::ReadAllBytes($file)) $type
    } else {
      Send-Text $ctx 404 'Not found'
    }
  } catch {
    $msg = $_.Exception.Message
    if ($_.Exception.InnerException) { $msg = $_.Exception.InnerException.Message }
    Write-Host "  error: $msg (line $($_.InvocationInfo.ScriptLineNumber), $($ctx.Request.HttpMethod) $($ctx.Request.Url.AbsolutePath))"
    try { Send-Text $ctx 502 ('Fetch failed: ' + $msg) } catch { }
  }
}
