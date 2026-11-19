$ErrorActionPreference = 'Stop'

$projectRoot = 'E:\python\LLM\IndustrialOps_Copilot'
$archiveRoot = Join-Path $projectRoot 'data\raw_archive\dry_vacuum_edwards_nxds'
$chunkSize = 196608

function Invoke-AgentEvalJson {
    param([string]$JavaScript, [int]$MaxOutput = 400000)
    $raw = & agent-browser --cdp 9222 --max-output $MaxOutput eval $JavaScript
    if ($LASTEXITCODE -ne 0) { throw "Browser eval failed: $($raw -join ' ')" }
    return (($raw -join "`n") | ConvertFrom-Json)
}

function Download-FromBrowser {
    param(
        [string]$SourceId,
        [string]$Needle,
        [string]$RelativeDir,
        [string]$FileName
    )
    $destination = Join-Path (Join-Path $archiveRoot $RelativeDir) $FileName
    Write-Host "[BROWSER FETCH] $SourceId -> $FileName"

    $prepareJs = @"
(()=>{
  const link=[...document.querySelectorAll('a')].find(a=>a.href.includes('$Needle'));
  if(!link) throw new Error('document link not found: $Needle');
  return fetch(link.href,{credentials:'include'}).then(async r=>{
    const buffer=await r.arrayBuffer();
    if(!r.ok) throw new Error('HTTP '+r.status);
    window.__codexDownloadBytes=new Uint8Array(buffer);
    return {status:r.status,length:window.__codexDownloadBytes.length,url:link.href};
  });
})()
"@
    $meta = Invoke-AgentEvalJson -JavaScript $prepareJs -MaxOutput 4000
    if ([int]$meta.length -le 0) { throw "$SourceId returned an empty file" }

    $stream = [System.IO.File]::Open($destination, [System.IO.FileMode]::Create, [System.IO.FileAccess]::Write)
    try {
        for ($offset = 0; $offset -lt [int]$meta.length; $offset += $chunkSize) {
            $end = [Math]::Min($offset + $chunkSize, [int]$meta.length)
            $chunkJs = @"
(()=>{
  const s=window.__codexDownloadBytes.slice($offset,$end);
  let binary='';
  for(let i=0;i<s.length;i+=32768){
    binary+=String.fromCharCode.apply(null,s.subarray(i,Math.min(i+32768,s.length)));
  }
  return btoa(binary);
})()
"@
            $base64 = Invoke-AgentEvalJson -JavaScript $chunkJs -MaxOutput 400000
            $bytes = [Convert]::FromBase64String([string]$base64)
            $stream.Write($bytes, 0, $bytes.Length)
            Write-Host "  $end / $($meta.length) bytes"
        }
    }
    finally {
        $stream.Dispose()
    }

    $signature = [System.Text.Encoding]::ASCII.GetString((Get-Content -LiteralPath $destination -Encoding Byte -TotalCount 4))
    if ($signature -ne '%PDF') { throw "$SourceId result is not a PDF" }
    $info = & pdfinfo $destination 2>$null
    $pages = (($info | Where-Object { $_ -match '^Pages:' }) -replace '^Pages:\s*','').Trim()
    $length = (Get-Item -LiteralPath $destination).Length
    Write-Host "  OK: bytes=$length pages=$pages"
}

Download-FromBrowser 'EDW-NXDS-MANUAL-EN-L' 'A73501880-Instructions.pdf' '01_operation_and_faults' 'edwards_nxds_instruction_manual_A73501880_L_en.pdf'
Download-FromBrowser 'EDW-NXDS-TIP-SEAL-EN' 'A73502840-Instructions.pdf' '02_maintenance' 'edwards_nxds_tip_seal_kit_A73502840_F_en.pdf'
Download-FromBrowser 'EDW-NXDS-ADDENDUM-EN' 'P60102856-Instructions.pdf' '01_operation_and_faults' 'edwards_nxds_addendum_P60102856_A_en.pdf'
Download-FromBrowser 'EDW-NXDS-LIFT-MULTI' 'P41100260-Instructions.pdf' '03_safety_and_installation' 'edwards_nxds_lifting_guide_P41100260_multi.pdf'

