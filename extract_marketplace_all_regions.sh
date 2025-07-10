#!/bin/bash

# Oracle Cloud Marketplace Complete Extractor - All Regions
# For macOS/Linux - Bash version

echo "========================================"
echo "Oracle Cloud Marketplace Data Extractor"
echo "ALL REGIONS: Commercial + US Gov + DoD"
echo "========================================"

# Check if OCI CLI is installed
if ! command -v oci &> /dev/null; then
    echo "❌ OCI CLI not found. Please install it first:"
    echo "   brew install oci-cli (macOS)"
    echo "   OR"
    echo "   bash -c \"\$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)\""
    exit 1
fi

# Check if OCI is configured
if [ ! -f ~/.oci/config ]; then
    echo "❌ OCI CLI not configured. Please run:"
    echo "   oci setup config"
    exit 1
fi

# Create output directory
mkdir -p marketplace_data
cd marketplace_data

echo ""
echo "Phase 1: Extracting commercial marketplace catalog..."
echo "================================================="

# Get all commercial marketplace listings with full details
echo "📊 Extracting all commercial marketplace listings..."
if oci marketplace listing list --all --output json > all_listings_commercial.json; then
    echo "✅ Successfully extracted commercial listings"
    LISTING_COUNT=$(jq '.data | length' all_listings_commercial.json 2>/dev/null || echo "unknown")
    echo "   Found: $LISTING_COUNT commercial listings"
else
    echo "❌ Failed to extract listings. Check OCI CLI configuration."
    echo "   Try: oci iam user list"
    exit 1
fi

# Get structured search results (additional metadata)
echo "📋 Extracting detailed commercial marketplace metadata..."
if oci marketplace listing-summary search-listings-structured --search-query '{}' --all --output json > listings_detailed_commercial.json; then
    echo "✅ Successfully extracted detailed commercial metadata"
else
    echo "⚠️  Warning: Could not extract detailed metadata (proceeding with main data)"
fi

echo ""
echo "Phase 2: US Government region extraction..."
echo "========================================="

# Function to extract marketplace data from a specific region
extract_region_data() {
    local region=$1
    local output_prefix=$2
    local description=$3
    
    echo "🏛️  Extracting $description..."
    
    # Main listings
    if oci marketplace listing list --all --region "$region" --output json > "${output_prefix}_listings.json" 2>/dev/null; then
        GOV_COUNT=$(jq '.data | length' "${output_prefix}_listings.json" 2>/dev/null || echo "0")
        echo "   ✅ $description: $GOV_COUNT listings available"
        
        # Detailed metadata
        echo "   📋 Extracting detailed metadata for $description..."
        oci marketplace listing-summary search-listings-structured --search-query '{}' --all --region "$region" --output json > "${output_prefix}_detailed.json" 2>/dev/null
        
        # Publisher information
        echo "   🏢 Extracting publishers for $description..."
        oci marketplace publisher list --all --region "$region" --output json > "${output_prefix}_publishers.json" 2>/dev/null
        
    else
        echo "   ❌ $description: Region not accessible"
        echo '{"data": []}' > "${output_prefix}_listings.json"
    fi
}

# Extract US Government East (Ashburn)
extract_region_data "us-gov-ashburn-1" "us_gov_east" "US Government East (Ashburn)"

# Extract US Government West (Phoenix)
extract_region_data "us-gov-phoenix-1" "us_gov_west" "US Government West (Phoenix)"

echo ""
echo "Phase 3: DoD region extraction..."
echo "================================="

# Extract DoD regions (if accessible)
extract_region_data "us-dod-east-1" "us_dod_east" "US DoD East"
extract_region_data "us-dod-central-1" "us_dod_central" "US DoD Central"
extract_region_data "us-dod-west-1" "us_dod_west" "US DoD West"

echo ""
echo "Phase 4: UK Government region extraction..."
echo "=========================================="

# Extract UK Government region
extract_region_data "uk-gov-london-1" "uk_gov" "UK Government (London)"

echo ""
echo "Phase 5: Extracting comprehensive metadata..."
echo "==========================================="

# Get categories for commercial region
echo "📊 Extracting by categories for complete coverage..."
categories=("analytics" "compute" "databases" "developer-tools" "integration" "iot" "machine-learning" "monitoring" "networking" "security" "storage" "business-applications")

for category in "${categories[@]}"; do
    echo "   📁 Extracting $category category..."
    if oci marketplace listing list --all --category "$category" --output json > "commercial_category_$category.json" 2>/dev/null; then
        CAT_COUNT=$(jq '.data | length' "commercial_category_$category.json" 2>/dev/null || echo "0")
        echo "      Found: $CAT_COUNT listings"
    else
        echo "      ⚠️  Category $category not found"
        echo '{"data": []}' > "commercial_category_$category.json"
    fi
done

# Get publisher information for commercial
echo "🏢 Extracting commercial publisher details..."
if oci marketplace publisher list --all --output json > commercial_publishers.json; then
    PUB_COUNT=$(jq '.data | length' commercial_publishers.json 2>/dev/null || echo "unknown")
    echo "   ✅ Found: $PUB_COUNT commercial publishers"
else
    echo "   ⚠️  Could not extract publisher data"
fi

echo ""
echo "Phase 6: Creating consolidated data files..."
echo "==========================================="

# Create consolidated master file if jq is available
if command -v jq &> /dev/null; then
    echo "🔄 Merging all regional data..."
    jq -s '
      {
        commercial: .[0].data,
        us_gov_east: .[1].data,
        us_gov_west: .[2].data,
        us_dod_east: .[3].data,
        us_dod_central: .[4].data,
        us_dod_west: .[5].data,
        uk_gov: .[6].data
      }
    ' all_listings_commercial.json \
      us_gov_east_listings.json \
      us_gov_west_listings.json \
      us_dod_east_listings.json \
      us_dod_central_listings.json \
      us_dod_west_listings.json \
      uk_gov_listings.json > all_regions_master.json
else
    echo "⚠️  jq not installed - skipping master file creation"
fi

# Create summary table
echo "📄 Creating summary tables..."
oci marketplace listing list --all --output table > commercial_listings_summary.txt 2>/dev/null || echo "Summary table creation failed" > commercial_listings_summary.txt

# Generate extraction report
echo ""
echo "📊 Generating extraction report..."

# Count listings per region
COMMERCIAL_COUNT=$(jq '.data | length' all_listings_commercial.json 2>/dev/null || echo "0")
US_GOV_EAST_COUNT=$(jq '.data | length' us_gov_east_listings.json 2>/dev/null || echo "0")
US_GOV_WEST_COUNT=$(jq '.data | length' us_gov_west_listings.json 2>/dev/null || echo "0")
US_DOD_EAST_COUNT=$(jq '.data | length' us_dod_east_listings.json 2>/dev/null || echo "0")
US_DOD_CENTRAL_COUNT=$(jq '.data | length' us_dod_central_listings.json 2>/dev/null || echo "0")
US_DOD_WEST_COUNT=$(jq '.data | length' us_dod_west_listings.json 2>/dev/null || echo "0")
UK_GOV_COUNT=$(jq '.data | length' uk_gov_listings.json 2>/dev/null || echo "0")

cat > extraction_report.txt << EOF
Oracle Cloud Marketplace Extraction Report - All Regions
Generated: $(date)
Extracted by: $(whoami)
Machine: $(hostname)

Regional Breakdown:
==================
Commercial Region:        $COMMERCIAL_COUNT listings
US Government East:       $US_GOV_EAST_COUNT listings
US Government West:       $US_GOV_WEST_COUNT listings
US DoD East:             $US_DOD_EAST_COUNT listings
US DoD Central:          $US_DOD_CENTRAL_COUNT listings
US DoD West:             $US_DOD_WEST_COUNT listings
UK Government:           $UK_GOV_COUNT listings

Files Generated:
================
Commercial Data:
- all_listings_commercial.json
- listings_detailed_commercial.json
- commercial_category_*.json
- commercial_publishers.json

US Government Data:
- us_gov_east_listings.json / us_gov_east_detailed.json
- us_gov_west_listings.json / us_gov_west_detailed.json

US DoD Data:
- us_dod_east_listings.json
- us_dod_central_listings.json
- us_dod_west_listings.json

UK Government Data:
- uk_gov_listings.json

Consolidated Data:
- all_regions_master.json (if jq installed)

Next Steps:
===========
1. Run the Python processor to create sales-focused CSV:
   python3 ../process_oci_all_regions.py

2. The processor will create:
   - oracle_marketplace_sales_catalog.csv (sales-focused format)
   - oracle_marketplace_sales_summary.txt (executive summary)

OCI CLI Configuration Used:
==========================
Default Region: $(grep region ~/.oci/config | head -1 | cut -d= -f2 || echo "Default")
EOF

echo ""
echo "========================================="
echo "✅ Extraction Complete!"
echo "========================================="
echo ""
echo "📊 Regional Summary:"
echo "   Commercial:      $COMMERCIAL_COUNT listings"
echo "   US Gov East:     $US_GOV_EAST_COUNT listings"
echo "   US Gov West:     $US_GOV_WEST_COUNT listings"
echo "   US DoD East:     $US_DOD_EAST_COUNT listings"
echo "   US DoD Central:  $US_DOD_CENTRAL_COUNT listings"
echo "   US DoD West:     $US_DOD_WEST_COUNT listings"
echo "   UK Government:   $UK_GOV_COUNT listings"
echo ""
echo "🎯 Next step: Create sales-focused CSV"
echo "   Command: python3 ../process_oci_all_regions.py"
echo ""
echo "📁 All files saved in: $(pwd)"
echo ""

# Go back to parent directory
cd ..

echo "Ready to process data for sales team! Run the Python processor next."
