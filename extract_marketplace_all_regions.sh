@echo off
REM Oracle Cloud Marketplace Complete Extractor - All Regions (Windows Version)
REM Enhanced version with comprehensive government region extraction

echo ========================================
echo Oracle Cloud Marketplace Data Extractor
echo ALL REGIONS: Commercial + US Gov + DoD
echo ========================================

REM Check if OCI CLI is installed
where oci >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: OCI CLI not found. Please install it first:
    echo    https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/cliinstall.htm
    exit /b 1
)

REM Check if OCI is configured
if not exist "%USERPROFILE%\.oci\config" (
    echo ERROR: OCI CLI not configured. Please run:
    echo    oci setup config
    exit /b 1
)

REM Create output directory
if not exist marketplace_data mkdir marketplace_data
cd marketplace_data

echo.
echo Phase 1: Extracting commercial marketplace catalog...
echo =================================================

REM Get all commercial marketplace listings with full details
echo Extracting all commercial marketplace listings...
oci marketplace listing list --all --output json > all_listings_commercial.json
if %errorlevel% equ 0 (
    echo SUCCESS: Successfully extracted commercial listings
    for /f "tokens=*" %%a in ('powershell -Command "(Get-Content all_listings_commercial.json | ConvertFrom-Json).data.Count"') do set LISTING_COUNT=%%a
    echo    Found: %LISTING_COUNT% commercial listings
) else (
    echo ERROR: Failed to extract listings. Check OCI CLI configuration.
    echo    Try: oci iam user list
    exit /b 1
)

REM Get structured search results (additional metadata)
echo Extracting detailed commercial marketplace metadata...
oci marketplace listing-summary search-listings-structured --search-query "{}" --all --output json > listings_detailed_commercial.json
if %errorlevel% equ 0 (
    echo SUCCESS: Successfully extracted detailed commercial metadata
) else (
    echo WARNING: Could not extract detailed metadata (proceeding with main data)
)

echo.
echo Phase 2: US Government region extraction...
echo =========================================

REM Extract US Government East (Ashburn)
echo Extracting US Government East region...
oci marketplace listing list --all --region us-gov-ashburn-1 --output json > us_gov_east_listings.json 2>nul
if %errorlevel% equ 0 (
    for /f "tokens=*" %%a in ('powershell -Command "(Get-Content us_gov_east_listings.json | ConvertFrom-Json).data.Count"') do set GOV_COUNT=%%a
    echo    SUCCESS: US Government East: %GOV_COUNT% listings available
    
    echo    Extracting detailed metadata for US Gov East...
    oci marketplace listing-summary search-listings-structured --search-query "{}" --all --region us-gov-ashburn-1 --output json > us_gov_east_detailed.json 2>nul
) else (
    echo    WARNING: US Government East: Region not accessible
    echo {"data": []} > us_gov_east_listings.json
)

REM Extract US Government West (Phoenix)
echo Extracting US Government West region...
oci marketplace listing list --all --region us-gov-phoenix-1 --output json > us_gov_west_listings.json 2>nul
if %errorlevel% equ 0 (
    for /f "tokens=*" %%a in ('powershell -Command "(Get-Content us_gov_west_listings.json | ConvertFrom-Json).data.Count"') do set GOV_COUNT=%%a
    echo    SUCCESS: US Government West: %GOV_COUNT% listings available
    
    echo    Extracting detailed metadata for US Gov West...
    oci marketplace listing-summary search-listings-structured --search-query "{}" --all --region us-gov-phoenix-1 --output json > us_gov_west_detailed.json 2>nul
) else (
    echo    WARNING: US Government West: Region not accessible
    echo {"data": []} > us_gov_west_listings.json
)

echo.
echo Phase 3: DoD region extraction...
echo =================================

REM Extract DoD regions
echo Extracting US DoD East region...
oci marketplace listing list --all --region us-dod-east-1 --output json > us_dod_east_listings.json 2>nul
if %errorlevel% equ 0 (
    for /f "tokens=*" %%a in ('powershell -Command "(Get-Content us_dod_east_listings.json | ConvertFrom-Json).data.Count"') do set DOD_COUNT=%%a
    echo    SUCCESS: US DoD East: %DOD_COUNT% listings available
) else (
    echo    WARNING: US DoD East: Region not accessible
    echo {"data": []} > us_dod_east_listings.json
)

echo Extracting US DoD Central region...
oci marketplace listing list --all --region us-dod-central-1 --output json > us_dod_central_listings.json 2>nul
if %errorlevel% equ 0 (
    for /f "tokens=*" %%a in ('powershell -Command "(Get-Content us_dod_central_listings.json | ConvertFrom-Json).data.Count"') do set DOD_COUNT=%%a
    echo    SUCCESS: US DoD Central: %DOD_COUNT% listings available
) else (
    echo    WARNING: US DoD Central: Region not accessible
    echo {"data": []} > us_dod_central_listings.json
)

echo Extracting US DoD West region...
oci marketplace listing list --all --region us-dod-west-1 --output json > us_dod_west_listings.json 2>nul
if %errorlevel% equ 0 (
    for /f "tokens=*" %%a in ('powershell -Command "(Get-Content us_dod_west_listings.json | ConvertFrom-Json).data.Count"') do set DOD_COUNT=%%a
    echo    SUCCESS: US DoD West: %DOD_COUNT% listings available
) else (
    echo    WARNING: US DoD West: Region not accessible
    echo {"data": []} > us_dod_west_listings.json
)

echo.
echo Phase 4: UK Government region extraction...
echo ==========================================

REM Extract UK Government region
echo Extracting UK Government region...
oci marketplace listing list --all --region uk-gov-london-1 --output json > uk_gov_listings.json 2>nul
if %errorlevel% equ 0 (
    for /f "tokens=*" %%a in ('powershell -Command "(Get-Content uk_gov_listings.json | ConvertFrom-Json).data.Count"') do set UK_COUNT=%%a
    echo    SUCCESS: UK Government: %UK_COUNT% listings available
) else (
    echo    WARNING: UK Government: Region not accessible
    echo {"data": []} > uk_gov_listings.json
)

echo.
echo Phase 5: Extracting comprehensive metadata across all regions...
echo ==============================================================

REM Get categories for commercial region
echo Extracting by categories for complete coverage...
set categories=analytics compute databases developer-tools integration iot machine-learning monitoring networking security storage business-applications

for %%c in (%categories%) do (
    echo    Extracting %%c category...
    oci marketplace listing list --all --category %%c --output json > commercial_category_%%c.json 2>nul
)

REM Get publisher information for commercial
echo Extracting commercial publisher details...
oci marketplace publisher list --all --output json > commercial_publishers.json
if %errorlevel% equ 0 (
    echo    SUCCESS: Found publisher information
) else (
    echo    WARNING: Could not extract publisher data
)

echo.
echo Phase 6: Creating consolidated data files...
echo ===========================================

REM Create summary table
echo Creating summary tables...
oci marketplace listing list --all --output table > commercial_listings_summary.txt 2>nul

REM Generate extraction report
echo.
echo Generating extraction report...

REM Create timestamp
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "timestamp=%dt:~0,4%-%dt:~4,2%-%dt:~6,2% %dt:~8,2%:%dt:~10,2%:%dt:~12,2%"

(
echo Oracle Cloud Marketplace Extraction Report - All Regions
echo Generated: %timestamp%
echo Extracted by: %USERNAME%
echo Machine: %COMPUTERNAME%
echo.
echo Regional Breakdown:
echo ==================
echo See JSON files for exact counts
echo.
echo Files Generated:
echo ================
echo Commercial Data:
echo - all_listings_commercial.json
echo - listings_detailed_commercial.json
echo - commercial_category_*.json
echo - commercial_publishers.json
echo.
echo US Government Data:
echo - us_gov_east_listings.json / us_gov_east_detailed.json
echo - us_gov_west_listings.json / us_gov_west_detailed.json
echo.
echo US DoD Data:
echo - us_dod_east_listings.json
echo - us_dod_central_listings.json
echo - us_dod_west_listings.json
echo.
echo UK Government Data:
echo - uk_gov_listings.json
echo.
echo Next Steps:
echo ===========
echo 1. Run the Python processor to create sales-focused CSV:
echo    python process_oci_all_regions.py
echo.
echo 2. The processor will create:
echo    - oracle_marketplace_sales_catalog.csv
echo    - oracle_marketplace_sales_summary.txt
) > extraction_report.txt

echo.
echo =========================================
echo SUCCESS: Extraction Complete!
echo =========================================
echo.
echo Regional data extracted (check individual files for counts)
echo.
echo Next step: Create sales-focused CSV
echo    Command: python process_oci_all_regions.py
echo.
echo All files saved in: %cd%
echo.

REM Go back to parent directory
cd ..

echo Ready to process data for sales team! Run the Python processor next.
pause