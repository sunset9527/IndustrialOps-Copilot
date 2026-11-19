$ErrorActionPreference = 'Continue'

$projectRoot = 'E:\python\LLM\IndustrialOps_Copilot'
$manifestPath = Join-Path $projectRoot 'data\source_manifests\download_manifest_2026-11-04.csv'
$outputManifest = Join-Path $projectRoot 'data\source_manifests\web_snapshot_validation_2026-11-04.csv'
$skipIds = @('HAAS-VF2-SCOPE-ZH','HAAS-ALARM-HELP-ZH','OSHA-1910-147','EDW-NXDS-DOCUMENTS')
$items = Import-Csv -LiteralPath $manifestPath | Where-Object {
    $_.kind -eq 'web_snapshot_pdf' -and $_.source_id -notin $skipIds
}
$validation = New-Object System.Collections.Generic.List[object]
$env:AGENT_BROWSER_DEFAULT_TIMEOUT = '10000'

foreach ($item in $items) {
    Write-Host "[CDP] $($item.source_id)"
    $status = 'failed'
    $message = ''
    $pages = 0
    $bytes = 0
    try {
        if (Test-Path -LiteralPath $item.local_path) {
            $existingFile = Get-Item -LiteralPath $item.local_path
            $existingInfo = & pdfinfo $item.local_path 2>$null
            $existingPagesLine = $existingInfo | Where-Object { $_ -match '^Pages:' }
            $existingPages = 0
            if ($existingPagesLine) { $existingPages = [int](($existingPagesLine -replace '^Pages:\s*','').Trim()) }
            if ($existingFile.Length -ge 100000 -and $existingPages -ge 2) {
                $bytes = $existingFile.Length
                $pages = $existingPages
                $status = 'validated'
                $validation.Add([PSCustomObject]@{
                    source_id = $item.source_id; url = $item.url; local_path = $item.local_path
                    status = $status; pages = $pages; bytes = $bytes; message = 'existing valid PDF'
                })
                Write-Host "[SKIP] existing valid PDF: pages=$pages bytes=$bytes"
                continue
            }
        }

        & agent-browser --cdp 9222 --max-output 300 open $item.url | Out-Host
        & agent-browser --cdp 9222 --max-output 100 wait 5000 | Out-Null
        $title = (& agent-browser --cdp 9222 --max-output 500 get title) -join ' '
        if ($title -match '请稍候|Just a moment') {
            & agent-browser --cdp 9222 --max-output 100 wait 10000 | Out-Null
            $title = (& agent-browser --cdp 9222 --max-output 500 get title) -join ' '
        }
        if ($title -match '404|请稍候|Just a moment') { throw "无效页面标题：$title" }

        & agent-browser --cdp 9222 --max-output 300 pdf $item.local_path | Out-Host
        if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $item.local_path)) {
            throw 'PDF 保存失败'
        }

        $file = Get-Item -LiteralPath $item.local_path
        $bytes = $file.Length
        $pdfInfo = & pdfinfo $item.local_path 2>$null
        $pagesLine = $pdfInfo | Where-Object { $_ -match '^Pages:' }
        if ($pagesLine) { $pages = [int](($pagesLine -replace '^Pages:\s*','').Trim()) }
        if ($bytes -lt 80000 -or $pages -lt 1) {
            throw "PDF 内容异常：bytes=$bytes pages=$pages"
        }
        $status = 'validated'
    }
    catch {
        $message = $_.Exception.Message
        Write-Warning "$($item.source_id)：$message"
    }

    $validation.Add([PSCustomObject]@{
        source_id = $item.source_id
        url = $item.url
        local_path = $item.local_path
        status = $status
        pages = $pages
        bytes = $bytes
        message = $message
    })
}

$validation | Export-Csv -LiteralPath $outputManifest -NoTypeInformation -Encoding UTF8
$ok = @($validation | Where-Object status -eq 'validated').Count
$failed = @($validation | Where-Object status -eq 'failed').Count
Write-Host "CDP 网页快照完成：成功 $ok，失败 $failed"
if ($failed -gt 0) {
    $validation | Where-Object status -eq 'failed' | Format-Table source_id, message -AutoSize
    exit 2
}

