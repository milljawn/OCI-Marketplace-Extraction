#!/bin/bash

# Oracle Cloud Marketplace Complete Extractor - All Regions
# Updated for OC2 (DoD) and OC3 (Gov) realms with customer-specific compartment IDs
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

# Prompt for customer-specific compartment IDs
echo ""
echo "🔐 Customer Compartment ID Configuration"
echo "========================================"
echo ""
echo "Please provide your compartment IDs for the restricted realms:"
echo ""

read -p "Enter your OC2 (DoD) tenancy compartment ID: " OC2_COMPARTMENT_ID
echo ""
read -p "Enter your OC3 (Government) tenancy compartment ID: " OC3_COMPARTMENT_ID
echo ""

# Validate inputs
if [ -z "$OC2_COMPARTMENT_ID" ] || [ -z "$OC3_COMPARTMENT_ID" ]; then
    echo "❌ Both compartment IDs are required. Exiting..."
    exit 1
fi

echo "✅ Using compartment IDs:"
echo "   OC2 (DoD): $OC2_COMPARTMENT_ID"
echo "   OC3 (Gov): $OC3_COMPARTMENT_ID"
echo ""

# Create output directory
mkdir -p marketplace_data
cd marketplace_data

echo ""
echo "Phase 1: Extracting commercial marketplace catalog..."
echo "================================================="

echo "📊 Extracting all commercial marketplace listings..."
if oci marketplace listing list --all --profile OC1 --output json > all_listings_commercial.json; then
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
if oci marketplace listing-summary search-listings-structured --search-query '{}' --all --profile OC1 --output json > listings_detailed_commercial.json; then
    echo "✅ Successfully extracted detailed commercial metadata"
else
    echo "⚠️  Warning: Could not extract detailed metadata (proceeding with main data)"
fi

echo ""
echo "Phase 2: OC3 Government region extraction..."
echo "============================================"

# Function to extract OC3 marketplace data with proper compartment ID
extract_oc3_data() {
    local region=$1
    local output_prefix=$2
    local description=$3
    
    echo "🏛️  Extracting $description..."
    
    # Main listings with compartment ID for OC3
    if oci marketplace listing list --compartment-id "$OC3_COMPARTMENT_ID" --all --region "$region" --profile OC3 --output json > "${output_prefix}_listings.json" 2>/dev/null; then
        GOV_COUNT=$(jq '.data | length' "${output_prefix}_listings.json" 2>/dev/null || echo "0")
        echo "   ✅ $description: $GOV_COUNT listings available"
        
        # Detailed metadata with compartment ID
        echo "   📋 Extracting detailed metadata for $description..."
        if oci marketplace listing-summary search-listings-structured --search-query '{}' --all --region "$region" --profile OC3 --output json > "${output_prefix}_detailed.json" 2>/dev/null; then
            echo "   ✅ Detailed metadata extracted for $description"
        else
            echo "   ⚠️  Could not extract detailed metadata for $description"
        fi
        
        # Publisher information with compartment ID
        echo "   🏢 Extracting publishers for $description..."
        if oci marketplace publisher list --compartment-id "$OC3_COMPARTMENT_ID" --all --region "$region" --profile OC3 --output json > "${output_prefix}_publishers.json" 2>/dev/null; then
            echo "   ✅ Publishers extracted for $description"
        else
            echo "   ⚠️  Could not extract publishers for $description"
        fi
        
    else
        echo "   ❌ $description: Region not accessible or authentication failed"
        echo '{"data": []}' > "${output_prefix}_listings.json"
    fi
}

# Extract OC3 US Government regions
extract_oc3_data "us-gov-ashburn-1" "oc3_us_gov_east" "OC3 US Government East (Ashburn)"
extract_oc3_data "us-gov-phoenix-1" "oc3_us_gov_west" "OC3 US Government West (Phoenix)"

echo ""
echo "Phase 3: OC2 DoD region extraction..."
echo "===================================="

# Function to extract OC2 marketplace data with proper compartment ID
extract_oc2_data() {
    local region=$1
    local output_prefix=$2
    local description=$3
    
    echo "🏛️  Extracting $description..."
    
    # Main listings with compartment ID for OC2
    if oci marketplace listing list --compartment-id "$OC2_COMPARTMENT_ID" --region "$region" --profile OC2 --output json > "${output_prefix}_listings.json" 2>/dev/null; then
        DOD_COUNT=$(jq '.data | length' "${output_prefix}_listings.json" 2>/dev/null || echo "0")
        echo "   ✅ $description: $DOD_COUNT listings available"
        
        # Detailed metadata with compartment ID
        echo "   📋 Extracting detailed metadata for $description..."
        if oci marketplace listing-summary search-listings-structured --search-query '{}' --region "$region" --profile OC2 --output json > "${output_prefix}_detailed.json" 2>/dev/null; then
            echo "   ✅ Detailed metadata extracted for $description"
        else
            echo "   ⚠️  Could not extract detailed metadata for $description"
        fi
        
        # Publisher information with compartment ID
        echo "   🏢 Extracting publishers for $description..."
        if oci marketplace publisher list --compartment-id "$OC2_COMPARTMENT_ID" --region "$region" --profile OC2 --output json > "${output_prefix}_publishers.json" 2>/dev/null; then
            echo "   ✅ Publishers extracted for $description"
        else
            echo "   ⚠️  Could not extract publishers for $description"
        fi
        
    else
        echo "   ❌ $description: Region not accessible or authentication failed"
        echo '{"data": []}' > "${output_prefix}_listings.json"
    fi
}

# Extract OC2 DoD regions
extract_oc2_data "us-langley-1" "oc2_us_dod_east" "OC2 US DoD East (Langley)"

# Additional DoD regions if they exist in OC2
echo "   🔍 Checking for additional OC2 DoD regions..."
extract_oc2_data "us-luke-1" "oc2_us_dod_west" "OC2 US DoD West (Luke)"

echo ""
echo "Phase 4: Legacy DoD region extraction (if accessible)..."
echo "====================================================="

# Function to extract legacy DoD data (fallback method)
extract_legacy_dod_data() {
    local region=$1
    local output_prefix=$2
    local description=$3
    
    echo "🏛️  Attempting legacy extraction for $description..."
    
    # Try without compartment ID first (legacy method)
    if oci marketplace listing list --all --region "$region" --output json > "${output_prefix}_listings.json" 2>/dev/null; then
        LEGACY_COUNT=$(jq '.data | length' "${output_prefix}_listings.json" 2>/dev/null || echo "0")
        echo "   ✅ $description (legacy): $LEGACY_COUNT listings available"
    else
        echo "   ❌ $description: Not accessible via legacy method"
        echo '{"data": []}' > "${output_prefix}_listings.json"
    fi
}

# Try legacy DoD regions
extract_legacy_dod_data "us-dod-east-1" "legacy_us_dod_east" "Legacy US DoD East"
extract_legacy_dod_data "us-dod-central-1" "legacy_us_dod_central" "Legacy US DoD Central"
extract_legacy_dod_data "us-dod-west-1" "legacy_us_dod_west" "Legacy US DoD West"



echo ""
echo "Phase 5: Extracting comprehensive commercial metadata..."
echo "====================================================="

# Get categories for commercial region
echo "📊 Extracting by categories for complete coverage..."
categories=("analytics" "compute" "databases" "developer-tools" "integration" "iot" "machine-learning" "monitoring" "networking" "security" "storage" "business-applications")

for category in "${categories[@]}"; do
    echo "   📁 Extracting $category category..."
    if oci marketplace listing list --all --category "$category" --profile OC1 --output json > "commercial_category_$category.json" 2>/dev/null; then
        CAT_COUNT=$(jq '.data | length' "commercial_category_$category.json" 2>/dev/null || echo "0")
        echo "      Found: $CAT_COUNT listings"
    else
        echo "      ⚠️  Category $category not found"
        echo '{"data": []}' > "commercial_category_$category.json"
    fi
done

# Get publisher information for commercial
echo "🏢 Extracting commercial publisher details..."
if oci marketplace publisher list --all --profile OC1 --output json > commercial_publishers.json; then
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
        oc3_us_gov_east: .[1].data,
        oc3_us_gov_west: .[2].data,
        oc2_us_dod_east: .[3].data,
        oc2_us_dod_west: .[4].data,
        legacy_us_dod_east: .[5].data,
        legacy_us_dod_central: .[6].data,
        legacy_us_dod_west: .[7].data
      }
    ' all_listings_commercial.json \
      oc3_us_gov_east_listings.json \
      oc3_us_gov_west_listings.json \
      oc2_us_dod_east_listings.json \
      oc2_us_dod_west_listings.json \
      legacy_us_dod_east_listings.json \
      legacy_us_dod_central_listings.json \
      legacy_us_dod_west_listings.json > all_regions_master.json
    
    echo "✅ Master file created: all_regions_master.json"
else
    echo "⚠️  jq not installed - skipping master file creation"
fi

# Create summary table
echo "📄 Creating summary tables..."
oci marketplace listing list --all --profile OC1 --output table > commercial_listings_summary.txt 2>/dev/null || echo "Summary table creation failed" > commercial_listings_summary.txt

echo ""
echo "Phase 7: Generating comprehensive extraction report..."
echo "==================================================="

# Count listings per region
COMMERCIAL_COUNT=$(jq '.data | length' all_listings_commercial.json 2>/dev/null || echo "0")
OC3_US_GOV_EAST_COUNT=$(jq '.data | length' oc3_us_gov_east_listings.json 2>/dev/null || echo "0")
OC3_US_GOV_WEST_COUNT=$(jq '.data | length' oc3_us_gov_west_listings.json 2>/dev/null || echo "0")
OC2_US_DOD_EAST_COUNT=$(jq '.data | length' oc2_us_dod_east_listings.json 2>/dev/null || echo "0")
OC2_US_DOD_WEST_COUNT=$(jq '.data | length' oc2_us_dod_west_listings.json 2>/dev/null || echo "0")
LEGACY_US_DOD_EAST_COUNT=$(jq '.data | length' legacy_us_dod_east_listings.json 2>/dev/null || echo "0")
LEGACY_US_DOD_CENTRAL_COUNT=$(jq '.data | length' legacy_us_dod_central_listings.json 2>/dev/null || echo "0")
LEGACY_US_DOD_WEST_COUNT=$(jq '.data | length' legacy_us_dod_west_listings.json 2>/dev/null || echo "0")

# Calculate totals
TOTAL_OC3_COUNT=$((OC3_US_GOV_EAST_COUNT + OC3_US_GOV_WEST_COUNT))
TOTAL_OC2_COUNT=$((OC2_US_DOD_EAST_COUNT + OC2_US_DOD_WEST_COUNT))
TOTAL_LEGACY_DOD_COUNT=$((LEGACY_US_DOD_EAST_COUNT + LEGACY_US_DOD_CENTRAL_COUNT + LEGACY_US_DOD_WEST_COUNT))
TOTAL_ALL_COUNT=$((COMMERCIAL_COUNT + TOTAL_OC3_COUNT + TOTAL_OC2_COUNT + TOTAL_LEGACY_DOD_COUNT))

cat > extraction_report.txt << EOF
Oracle Cloud Marketplace Extraction Report - All Regions
Generated: $(date)
Extracted by: $(whoami)
Machine: $(hostname)

Regional Breakdown:
==================
Commercial Region:           $COMMERCIAL_COUNT listings

OC3 Government Regions:      $TOTAL_OC3_COUNT listings total
- US Gov East (Ashburn):     $OC3_US_GOV_EAST_COUNT listings
- US Gov West (Phoenix):     $OC3_US_GOV_WEST_COUNT listings

OC2 DoD Regions:            $TOTAL_OC2_COUNT listings total
- US DoD East (Langley):    $OC2_US_DOD_EAST_COUNT listings
- US DoD West (Luke):       $OC2_US_DOD_WEST_COUNT listings

Legacy DoD Regions:         $TOTAL_LEGACY_DOD_COUNT listings total
- US DoD East:              $LEGACY_US_DOD_EAST_COUNT listings
- US DoD Central:           $LEGACY_US_DOD_CENTRAL_COUNT listings
- US DoD West:              $LEGACY_US_DOD_WEST_COUNT listings

TOTAL ACROSS ALL REGIONS:   $TOTAL_ALL_COUNT listings

Compartment IDs Used:
====================
OC2 (DoD): $OC2_COMPARTMENT_ID
OC3 (Gov): $OC3_COMPARTMENT_ID

Files Generated:
================
Commercial Data:
- all_listings_commercial.json
- listings_detailed_commercial.json
- commercial_category_*.json
- commercial_publishers.json

OC3 Government Data:
- oc3_us_gov_east_listings.json / oc3_us_gov_east_detailed.json
- oc3_us_gov_west_listings.json / oc3_us_gov_west_detailed.json

OC2 DoD Data:
- oc2_us_dod_east_listings.json / oc2_us_dod_east_detailed.json
- oc2_us_dod_west_listings.json / oc2_us_dod_west_detailed.json

Legacy DoD Data:
- legacy_us_dod_east_listings.json
- legacy_us_dod_central_listings.json
- legacy_us_dod_west_listings.json

Consolidated Data:
- all_regions_master.json (if jq installed)

Next Steps:
===========
1. Run the Python processor to create sales-focused analysis:
   python3 ../process_oci_customer.py

2. The processor will create:
   - oracle_marketplace_complete_catalog.xlsx (comprehensive Excel analysis)
   - oracle_marketplace_sales_summary.txt (executive summary)

OCI CLI Configuration Used:
==========================
Default Region: $(grep region ~/.oci/config | head -1 | cut -d= -f2 || echo "Default")
Config Profile: $(grep '\[' ~/.oci/config | head -1 | tr -d '[]' || echo "DEFAULT")

Authentication Method:
=====================
- OC2 DoD regions: Compartment ID authentication
- OC3 Gov regions: Compartment ID authentication  
- Commercial/UK: Standard regional authentication

Notes:
======
- OC2 and OC3 regions require specific compartment IDs for access
- 404 errors without compartment IDs are expected and handled
- Legacy DoD regions are attempted as fallback
- Empty files indicate region inaccessibility, not extraction failure
EOF

echo ""
echo "========================================="
echo "✅ Multi-Realm Extraction Complete!"
echo "========================================="
echo ""
echo "📊 Regional Summary:"
echo "   Commercial:          $COMMERCIAL_COUNT listings"
echo "   OC3 Gov East:        $OC3_US_GOV_EAST_COUNT listings"
echo "   OC3 Gov West:        $OC3_US_GOV_WEST_COUNT listings"
echo "   OC2 DoD East:        $OC2_US_DOD_EAST_COUNT listings"
echo "   OC2 DoD West:        $OC2_US_DOD_WEST_COUNT listings"
echo "   Legacy DoD East:     $LEGACY_US_DOD_EAST_COUNT listings"
echo "   Legacy DoD Central:  $LEGACY_US_DOD_CENTRAL_COUNT listings"
echo "   Legacy DoD West:     $LEGACY_US_DOD_WEST_COUNT listings"
echo "   ────────────────────────────────────"
echo "   TOTAL:              $TOTAL_ALL_COUNT listings"
echo ""
echo "🎯 Next step: Create comprehensive Excel analysis"
echo "   Command: python3 ../process_oci_customer.py"
echo ""
echo "📁 All files saved in: $(pwd)"
echo ""
echo "🔐 Realm Access Status:"
echo "   OC2 (DoD): $([ $TOTAL_OC2_COUNT -gt 0 ] && echo "✅ Accessible" || echo "❌ Not accessible")"
echo "   OC3 (Gov): $([ $TOTAL_OC3_COUNT -gt 0 ] && echo "✅ Accessible" || echo "❌ Not accessible")"
echo "   Commercial: $([ $COMMERCIAL_COUNT -gt 0 ] && echo "✅ Accessible" || echo "❌ Not accessible")"
echo ""

# Go back to parent directory
cd ..

echo "Ready to process comprehensive multi-realm data for sales analysis!"
echo "Run: python3 process_oci_customer.py"