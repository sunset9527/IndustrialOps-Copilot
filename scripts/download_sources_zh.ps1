$ErrorActionPreference = 'Stop'

$projectRoot = 'E:\python\LLM\IndustrialOps_Copilot'
$archiveRoot = Join-Path $projectRoot 'data\raw_archive'
$manifestRoot = Join-Path $projectRoot 'data\source_manifests'
$chrome = 'C:\Program Files\Google\Chrome\Application\chrome.exe'
$chromeProfile = Join-Path $projectRoot '.download_chrome_profile'
$accessDate = '2026-11-04'

$directories = @(
    'cnc_haas_vf2_ngc\00_scope_and_versions',
    'cnc_haas_vf2_ngc\01_operator',
    'cnc_haas_vf2_ngc\02_installation_and_safety',
    'cnc_haas_vf2_ngc\03_ngc_alarm_and_evidence',
    'cnc_haas_vf2_ngc\04_axis_and_servo',
    'cnc_haas_vf2_ngc\05_spindle_and_drive',
    'cnc_haas_vf2_ngc\06_umbrella_tool_changer',
    'cnc_haas_vf2_ngc\07_lubrication',
    'cnc_haas_vf2_ngc\08_coolant',
    'cnc_haas_vf2_ngc\09_maintenance_and_enclosure',
    'cnc_haas_vf2_ngc\90_reference_only',
    'dry_vacuum_edwards_nxds\00_scope_and_versions',
    'dry_vacuum_edwards_nxds\01_operation_and_faults',
    'dry_vacuum_edwards_nxds\02_maintenance',
    'dry_vacuum_edwards_nxds\03_safety_and_installation',
    'dry_vacuum_edwards_nxds\90_reference_only'
)

foreach ($relativeDir in $directories) {
    New-Item -ItemType Directory -Force -Path (Join-Path $archiveRoot $relativeDir) | Out-Null
}
New-Item -ItemType Directory -Force -Path $manifestRoot | Out-Null
New-Item -ItemType Directory -Force -Path $chromeProfile | Out-Null

$results = New-Object System.Collections.Generic.List[object]

function Add-Result {
    param(
        [string]$SourceId,
        [string]$Language,
        [string]$Kind,
        [string]$Url,
        [string]$Path,
        [string]$Status,
        [string]$Message
    )
    $item = [PSCustomObject]@{
        source_id = $SourceId
        language = $Language
        kind = $Kind
        url = $Url
        local_path = $Path
        status = $Status
        message = $Message
        accessed_at = $accessDate
    }
    $script:results.Add($item)
}

function Test-PdfSignature {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { return $false }
    if ((Get-Item -LiteralPath $Path).Length -lt 1024) { return $false }
    $bytes = Get-Content -LiteralPath $Path -Encoding Byte -TotalCount 4
    if ($bytes.Count -ne 4) { return $false }
    return ([System.Text.Encoding]::ASCII.GetString($bytes) -eq '%PDF')
}

function Download-Pdf {
    param(
        [string]$SourceId,
        [string]$Language,
        [string]$RelativeDir,
        [string]$FileName,
        [string]$Url
    )
    $destination = Join-Path (Join-Path $archiveRoot $RelativeDir) $FileName
    Write-Host "[PDF] $SourceId -> $FileName"
    try {
        if (-not (Test-PdfSignature -Path $destination)) {
            Invoke-WebRequest -UseBasicParsing -Uri $Url -OutFile $destination -Headers @{
                'User-Agent' = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140 Safari/537.36'
                'Accept' = 'application/pdf,*/*'
            }
        }
        if (-not (Test-PdfSignature -Path $destination)) {
            throw '下载结果不是有效 PDF'
        }
        Add-Result $SourceId $Language 'pdf' $Url $destination 'downloaded' ''
    }
    catch {
        Add-Result $SourceId $Language 'pdf' $Url $destination 'failed' $_.Exception.Message
        Write-Warning "$SourceId 下载失败：$($_.Exception.Message)"
    }
}

function Save-WebPagePdf {
    param(
        [string]$SourceId,
        [string]$Language,
        [string]$RelativeDir,
        [string]$FileName,
        [string]$Url
    )
    $destination = Join-Path (Join-Path $archiveRoot $RelativeDir) $FileName
    Write-Host "[WEB] $SourceId -> $FileName"
    try {
        if (-not (Test-PdfSignature -Path $destination)) {
            & $chrome `
                '--headless=new' `
                '--disable-gpu' `
                '--disable-extensions' `
                '--no-pdf-header-footer' `
                '--run-all-compositor-stages-before-draw' `
                '--virtual-time-budget=10000' `
                "--user-data-dir=$chromeProfile" `
                "--print-to-pdf=$destination" `
                $Url | Out-Host
        }
        if (-not (Test-PdfSignature -Path $destination)) {
            throw '网页快照不是有效 PDF'
        }
        Add-Result $SourceId $Language 'web_snapshot_pdf' $Url $destination 'downloaded' ''
    }
    catch {
        Add-Result $SourceId $Language 'web_snapshot_pdf' $Url $destination 'failed' $_.Exception.Message
        Write-Warning "$SourceId 保存失败：$($_.Exception.Message)"
    }
}

# Haas：中文阅读版 + 英文当前版本校验
Download-Pdf 'HAAS-OP-ZH-2023' 'zh-CN' 'cnc_haas_vf2_ngc\01_operator' 'haas_mill_operator_manual_2023_zh-CN.pdf' 'https://www.haascnc.com/content/dam/haascnc/additional-languages/zh/service/manual/supplement/Chinese---mill-operator%27s-manual---2023.pdf'
Download-Pdf 'HAAS-OP-EN-2025' 'en' 'cnc_haas_vf2_ngc\01_operator' 'haas_mill_ngc_operator_manual_2025_en.pdf' 'https://haascnc.com/content/dam/haascnc/en/service/manual/operator/english---mill-ngc---operator%27s-manual---2025.pdf'
Download-Pdf 'HAAS-VF-BROCHURE-2026' 'en' 'cnc_haas_vf2_ngc\00_scope_and_versions' 'haas_vf_series_brochure_2026-03_en.pdf' 'https://www.haascnc.com/content/dam/haascnc/assets/sales-and-marketing/public/machines/vertical-mills/vf/2026-03-VF-4Pager-39-4139.pdf'
Download-Pdf 'OSHA-LOTO-FACTSHEET' 'en' 'cnc_haas_vf2_ngc\02_installation_and_safety' 'osha_lockout_tagout_factsheet_oshafs3529_en.pdf' 'https://www.osha.gov/sites/default/files/publications/OSHAFS3529.pdf'
Download-Pdf 'HAAS-VFVM-LEGACY' 'en' 'cnc_haas_vf2_ngc\90_reference_only' 'haas_vf_vm_service_manual_legacy_en.pdf' 'https://www.haascnc.com/content/dam/haascnc/en/service/manual/service/vf_vm_series_interactive_service_manual.pdf'

$haasPages = @(
    @('HAAS-VF2-SCOPE-ZH','cnc_haas_vf2_ngc\00_scope_and_versions','haas_vf2_product_scope_zh-CN_snapshot_2026-11-04.pdf','https://www.haascnc.com/zh/machines/vertical-mills/vf-series/models/small/vf-2.html'),
    @('HAAS-VFVM-SPECS-ZH','cnc_haas_vf2_ngc\00_scope_and_versions','haas_vf_vm_specifications_zh-CN_snapshot_2026-11-04.pdf','https://www.haascnc.com/zh/service/online-manuals/vf-vm-series---service-manual/vf-vm---specifications.html'),
    @('HAAS-VMC-INSTALL-ZH','cnc_haas_vf2_ngc\02_installation_and_safety','haas_vmc_installation_zh-CN_snapshot_2026-11-04.pdf','https://www.haascnc.com/zh/service/troubleshooting-and-how-to/how-to/vmc-installation-guide.html'),
    @('OSHA-1910-147','cnc_haas_vf2_ngc\02_installation_and_safety','osha_1910_147_loto_en_snapshot_2026-11-04.pdf','https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.147'),
    @('OSHA-1910-212','cnc_haas_vf2_ngc\02_installation_and_safety','osha_1910_212_machine_guarding_en_snapshot_2026-11-04.pdf','https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.212'),
    @('HAAS-ALARM-HELP-ZH','cnc_haas_vf2_ngc\03_ngc_alarm_and_evidence','haas_alarm_search_help_zh-CN_snapshot_2026-11-04.pdf','https://www.haascnc.com/zh/service/troubleshooting-and-how-to/reference-documents/alarm-search-help.html'),
    @('HAAS-NGC-ERROR-ZH','cnc_haas_vf2_ngc\03_ngc_alarm_and_evidence','haas_ngc_error_report_zh-CN_snapshot_2026-11-04.pdf','https://www.haascnc.com/zh/service/online-manuals/next-gen-control-electrical---service-manual/ngc---error-report-and-backup.html'),
    @('HAAS-NGC-IO-ZH','cnc_haas_vf2_ngc\03_ngc_alarm_and_evidence','haas_ngc_io_tc_pcb_zh-CN_snapshot_2026-11-04.pdf','https://www.haascnc.com/zh/service/online-manuals/next-gen-control-electrical---service-manual/ngc---i-o.html'),
    @('HAAS-NGC-ICONS-ZH','cnc_haas_vf2_ngc\03_ngc_alarm_and_evidence','haas_ngc_control_icons_zh-CN_snapshot_2026-11-04.pdf','https://www.haascnc.com/zh/service/online-manuals/next-gen-control-electrical---service-manual/ngc---control-icons.html'),
    @('HAAS-NGC-BREAKER-ZH','cnc_haas_vf2_ngc\03_ngc_alarm_and_evidence','haas_ngc_circuit_breaker_transformer_zh-CN_snapshot_2026-11-04.pdf','https://www.haascnc.com/zh/service/online-manuals/next-gen-control-electrical---service-manual/ngc---circuit-breaker-and-transformer.html'),
    @('HAAS-NGC-PSUP-ZH','cnc_haas_vf2_ngc\03_ngc_alarm_and_evidence','haas_ngc_psup_zh-CN_snapshot_2026-11-04.pdf','https://www.haascnc.com/zh/service/online-manuals/next-gen-control-electrical---service-manual/ngc---power-distribuition.html'),
    @('HAAS-AXIS-MOTION-ZH','cnc_haas_vf2_ngc\04_axis_and_servo','haas_vf_vm_axis_motion_zh-CN_snapshot_2026-11-04.pdf','https://www.haascnc.com/zh/service/online-manuals/vf-vm-series---service-manual/vf-vm---axis-motion.html'),
    @('HAAS-SERVO-MOTOR-ZH','cnc_haas_vf2_ngc\04_axis_and_servo','haas_ngc_servo_motors_axis_cables_zh-CN_snapshot_2026-11-04.pdf','https://www.haascnc.com/zh/service/online-manuals/next-gen-control-electrical---service-manual/ngc---servo-motors-and-axis-cables.html'),
    @('HAAS-SERVO-AMP-ZH','cnc_haas_vf2_ngc\04_axis_and_servo','haas_ngc_servo_amplifiers_zh-CN_snapshot_2026-11-04.pdf','https://www.haascnc.com/zh/service/online-manuals/next-gen-control-electrical---service-manual/ngc---servo-amplifiers.html'),
    @('HAAS-40T-SPINDLE-ZH','cnc_haas_vf2_ngc\05_spindle_and_drive','haas_vf_vm_40t_spindle_zh-CN_snapshot_2026-11-04.pdf','https://www.haascnc.com/zh/service/online-manuals/vf-vm-series---service-manual/vf-vm---40t---spindle.html'),
    @('HAAS-40T-MOTOR-ZH','cnc_haas_vf2_ngc\05_spindle_and_drive','haas_vf_vm_40t_spindle_motor_zh-CN_snapshot_2026-11-04.pdf','https://www.haascnc.com/zh/service/online-manuals/vf-vm-series---service-manual/vf-vm---40t-spindle-motor.html'),
    @('HAAS-VECTOR-DRIVE-ZH','cnc_haas_vf2_ngc\05_spindle_and_drive','haas_ngc_vector_drive_zh-CN_snapshot_2026-11-04.pdf','https://www.haascnc.com/zh/service/online-manuals/next-gen-control-electrical---service-manual/ngc---vector-drive.html'),
    @('HAAS-WYE-DELTA-ZH','cnc_haas_vf2_ngc\05_spindle_and_drive','haas_ngc_wye_delta_zh-CN_snapshot_2026-11-04.pdf','https://www.haascnc.com/zh/service/online-manuals/next-gen-control-electrical---service-manual/ngc---wye---delta.html'),
    @('HAAS-UMBRELLA-VFVM-ZH','cnc_haas_vf2_ngc\06_umbrella_tool_changer','haas_vf_vm_umbrella_tool_changer_zh-CN_snapshot_2026-11-04.pdf','https://www.haascnc.com/zh/service/online-manuals/vf-vm-series---service-manual/vf-vm---umbrella-tool-changer.html'),
    @('HAAS-UMBRELLA-REPLACE-ZH','cnc_haas_vf2_ngc\06_umbrella_tool_changer','haas_umbrella_service_replacements_zh-CN_snapshot_2026-11-04.pdf','https://www.haascnc.com/zh/service/online-manuals/mill-tool-changer---service-manual/umbrella-tool-changer---service-replacements.html'),
    @('HAAS-UMBRELLA-ALIGN-ZH','cnc_haas_vf2_ngc\06_umbrella_tool_changer','haas_umbrella_alignment_zh-CN_snapshot_2026-11-04.pdf','https://www.haascnc.com/zh/service/online-manuals/mill-tool-changer---service-manual/umbrella-tool-changer---alignment-.html'),
    @('HAAS-UMBRELLA-TSG-ZH','cnc_haas_vf2_ngc\06_umbrella_tool_changer','haas_umbrella_tsg_zh-CN_snapshot_2026-11-04.pdf','https://www.haascnc.com/zh/service/online-manuals/mill-tool-changer---service-manual/tool-changer-troubleshooting-guides.html'),
    @('HAAS-TOOL-CHANGER-TOC-ZH','cnc_haas_vf2_ngc\06_umbrella_tool_changer','haas_mill_tool_changer_toc_zh-CN_snapshot_2026-11-04.pdf','https://www.haascnc.com/zh/service/online-manuals/mill-tool-changer---service-manual/mill-tool-changer---table-of-contents.html.html'),
    @('HAAS-LUBE-INTRO-ZH','cnc_haas_vf2_ngc\07_lubrication','haas_lube_systems_intro_zh-CN_snapshot_2026-11-04.pdf','https://www.haascnc.com/zh/service/online-manuals/lubrication-systems---service-manual/lube-systems---introduction.html'),
    @('HAAS-HALO-ZH','cnc_haas_vf2_ngc\07_lubrication','haas_axis_lubrication_halo_zh-CN_snapshot_2026-11-04.pdf','https://www.haascnc.com/zh/service/online-manuals/lubrication-systems---service-manual/haas-axis-lubrication-oil.html'),
    @('HAAS-SPINDLE-OIL-ZH','cnc_haas_vf2_ngc\07_lubrication','haas_spindle_oil_collection_test_zh-CN_snapshot_2026-11-04.pdf','https://www.haascnc.com/zh/service/troubleshooting-and-how-to/how-to/mill---spindle---lubrication-oil---collection-test.html'),
    @('HAAS-FLOOD-COOLANT-ZH','cnc_haas_vf2_ngc\08_coolant','haas_standard_flood_coolant_zh-CN_snapshot_2026-11-04.pdf','https://www.haascnc.com/zh/service/online-manuals/chip-and-coolant---service-manual/standard-flood-coolant.html'),
    @('HAAS-MAINTENANCE-ZH','cnc_haas_vf2_ngc\09_maintenance_and_enclosure','haas_vf_vm_maintenance_zh-CN_snapshot_2026-11-04.pdf','https://www.haascnc.com/zh/service/online-manuals/vf-vm-series---service-manual/vf-vm---maintenance.html'),
    @('HAAS-ENCLOSURE-ZH','cnc_haas_vf2_ngc\09_maintenance_and_enclosure','haas_vf_vm_enclosure_zh-CN_snapshot_2026-11-04.pdf','https://www.haascnc.com/zh/service/online-manuals/vf-vm-series---service-manual/vf-vm---enclosure.html')
)

foreach ($page in $haasPages) {
    Save-WebPagePdf $page[0] 'zh-CN' $page[1] $page[2] $page[3]
}

# Edwards：中文版优先，英文最新版与暂无中文的补充资料同时归档
Download-Pdf 'EDW-NXDS-MANUAL-ZH-K' 'zh-CN' 'dry_vacuum_edwards_nxds\01_operation_and_faults' 'edwards_nxds_instruction_manual_A73501846_K_zh-CN.pdf' 'https://global.my.edwardsvacuum.com/medias/A73501846-Instructions.pdf?attachment=true&context=bWFzdGVyfHJvb3R8MTUyMTQ3MXxhcHBsaWNhdGlvbi9wZGZ8YURabEwyZzVaUzh4TURNek56QTNNamszTlRBMU5UZ3ZRVGN6TlRBeE9EUTJJQzBnU1c1emRISjFZM1JwYjI1ekxuQmtaZ3xjMDUxMmQ1MDk1MTE4YmExOTg2MWJjODZmNjRkNWNkZmZhNjc1Yzk2NmJhNGFmYzBkYWM0MWJlNDY3N2Q1YzA4'
Download-Pdf 'EDW-NXDS-MANUAL-EN-L' 'en' 'dry_vacuum_edwards_nxds\01_operation_and_faults' 'edwards_nxds_instruction_manual_A73501880_L_en.pdf' 'https://global.my.edwardsvacuum.com/medias/A73501880-Instructions.pdf?attachment=true&context=bWFzdGVyfHJvb3R8MTU2NzYyM3xhcHBsaWNhdGlvbi9wZGZ8YUdGaUwyaGxaUzh4TVRnek5ETTJOVEkyTXpnM05UQXZRVGN6TlRBeE9EZ3dJQzBnU1c1emRISjFZM1JwYjI1ekxuQmtaZ3xiMTY1YjNlMGJhMDE4NWI5NjdiMmQ1YjA5ZDEyYzdjNDY0ODdhYTdmNTUxOWQyYWJmNjY1YjJlNTVhNmNmOTM5'
Download-Pdf 'EDW-NXDS-TIP-SEAL-EN' 'en' 'dry_vacuum_edwards_nxds\02_maintenance' 'edwards_nxds_tip_seal_kit_A73502840_F_en.pdf' 'https://global.my.edwardsvacuum.com/medias/A73502840-Instructions.pdf?attachment=true&context=bWFzdGVyfHJvb3R8NzgxMTYxfGFwcGxpY2F0aW9uL3BkZnxhREJpTDJnd05TOHhNVGd6TXpjME1EUTRPVFV5TmpJdlFUY3pOVEF5T0RRd0lDMGdTVzV6ZEhKMVkzUnBiMjV6TG5Ca1pnfGE2NzBmNmI3MGQ3NjZkNWFlYzk4MTA2ODYxODFkYWMzMzVlODFlOWVlMTI2NWQ0YjA3M2JhYjliZThjZmE2NzM'
Download-Pdf 'EDW-NXDS-ADDENDUM-EN' 'en' 'dry_vacuum_edwards_nxds\01_operation_and_faults' 'edwards_nxds_addendum_P60102856_A_en.pdf' 'https://global.my.edwardsvacuum.com/medias/P60102856-Instructions.pdf?attachment=true&context=bWFzdGVyfHJvb3R8MjczODExfGFwcGxpY2F0aW9uL3BkZnxhREJrTDJnNE5TOHhNVGs0TWpnMU5ESTVPREF4TWpZdlVEWXdNVEF5T0RVMkxTQkpibk4wY25WamRHbHZibk11Y0dSbXw5MWQ1N2Y4OTQxMjJkMzg1YWZkM2UzYmMxMTFjOTQwNTI2NzAzN2FiZjRhNjA2M2M4YWQ5ZWVlMWM4MzUyOGVm'
Download-Pdf 'EDW-NXDS-LIFT-MULTI' 'multi-zh-CN' 'dry_vacuum_edwards_nxds\03_safety_and_installation' 'edwards_nxds_lifting_guide_P41100260_multi.pdf' 'https://global.my.edwardsvacuum.com/medias/P41100260-Instructions.pdf?attachment=true&context=bWFzdGVyfHJvb3R8MTM4ODA4fGFwcGxpY2F0aW9uL3BkZnxhRFJsTDJnMlpTOHhNVGd5TnpnNE5UVTBNall3TnpndlVEUXhNVEF3TWpZd0lDMGdTVzV6ZEhKMVkzUnBiMjV6TG5Ca1pnfGFlMjc3ZjY0OTIwYzQ5N2Y0NTAzOGRjYjNhYmVhODA4MjZiODAzYzRkNWMzZjY2NDYxNDYzOGQ3NDg0M2Q3YzA'
Download-Pdf 'EDW-NXDS-BROCHURE-ZH' 'zh-CN' 'dry_vacuum_edwards_nxds\00_scope_and_versions' 'edwards_nxds_brochure_3601-0086-59_zh-CN.pdf' 'https://global.my.edwardsvacuum.com/medias/3601-0086-59-nXDS-brochure.pdf?attachment=true'
Download-Pdf 'EDW-SAFETY-EN' 'en' 'dry_vacuum_edwards_nxds\03_safety_and_installation' 'edwards_vacuum_system_safety_P40040100_E_en.pdf' 'https://www.edwardsvacuum.com/content/dam/brands/edwards-vacuum/edwards-website-assets/corporate/documents/edwards-vacuum-safety-booklet.pdf'
Save-WebPagePdf 'EDW-NXDS-DOCUMENTS' 'en' 'dry_vacuum_edwards_nxds\00_scope_and_versions' 'edwards_nxds6i_product_documents_snapshot_2026-11-04.pdf' 'https://global.my.edwardsvacuum.com/Catalog/Pumps/Dry-Scroll-Pumps/nXDSi-Scroll-Pumps/nXDS6i/p/b_nxds6i'

$manifestCsv = Join-Path $manifestRoot 'download_manifest_2026-11-04.csv'
$results | Export-Csv -LiteralPath $manifestCsv -NoTypeInformation -Encoding UTF8

$hashCsv = Join-Path $manifestRoot 'source_hashes_2026-11-04.csv'
Get-ChildItem -LiteralPath $archiveRoot -File -Recurse | ForEach-Object {
    $hash = Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256
    [PSCustomObject]@{
        path = $_.FullName
        bytes = $_.Length
        sha256 = $hash.Hash
    }
} | Export-Csv -LiteralPath $hashCsv -NoTypeInformation -Encoding UTF8

$downloaded = @($results | Where-Object status -eq 'downloaded').Count
$failed = @($results | Where-Object status -eq 'failed').Count
Write-Host "完成：成功 $downloaded，失败 $failed"
Write-Host "清单：$manifestCsv"
Write-Host "哈希：$hashCsv"
if ($failed -gt 0) {
    $results | Where-Object status -eq 'failed' | Format-Table source_id, message -AutoSize
    exit 2
}

