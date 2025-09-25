#!/bin/bash

# Oracle Cloud Marketplace Complete Extractor - All Regions
# Simplified for OC1, OC2, OC3 classification extraction
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
echo "🔍 Customer Compartment ID Configuration"
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
echo "Phase 1: Extracting OC1 Commercial marketplace catalog..."
echo "========================================================="

echo "📊 Extracting all commercial marketplace listings..."
if oci marketplace listing list --all --profile OC1 --output json > oc1_commercial_listings.json; then
    echo "✅ Successfully extracted commercial listings"
    LISTING_COUNT=$(jq '.data | length' oc1_commercial_listings.json 2>/dev/null || echo "unknown")
    echo "   Found: $LISTING_COUNT commercial listings"
else
    echo "❌ Failed to extract listings. Check OCI CLI configuration."
    echo "   Try: oci iam user list"
    exit 1
fi

# Get structured search results for OC1
echo "📋 Extracting detailed commercial marketplace metadata..."
if oci marketplace listing-summary search-listings-structured --search-query '{}' --all --profile OC1 --output json > oc1_commercial_detailed.json; then
    echo "✅ Successfully extracted detailed commercial metadata"
else
    echo "⚠️  Warning: Could not extract detailed metadata (proceeding with main data)"
fi

# Get publisher information for OC1
echo "🏢 Extracting commercial publisher details..."
if oci marketplace publisher list --all --profile OC1 --output json > oc1_commercial_publishers.json; then
    PUB_COUNT=$(jq '.data | length' oc1_commercial_publishers.json 2>/dev/null || echo "unknown")
    echo "   ✅ Found: $PUB_COUNT commercial publishers"
else
    echo "   ⚠️  Could not extract publisher data"
fi

echo ""
echo "Phase 2: OC3 Government region extraction..."
echo "============================================"

# Extract OC3 marketplace data 
echo "🏛️  Extracting OC3 US Government marketplace data..."

# Try both OC3 regions and combine
echo "   Attempting US Gov East (Ashburn)..."
if oci marketplace listing list --compartment-id "$OC3_COMPARTMENT_ID" --all --region us-gov-ashburn-1 --profile OC3 --output json > oc3_us_gov_east_listings.json 2>/dev/null; then
    GOV_EAST_COUNT=$(jq '.data | length' oc3_us_gov_east_listings.json 2>/dev/null || echo "0")
    echo "   ✅ US Gov East: $GOV_EAST_COUNT listings"
else
    echo "   ❌ US Gov East: Region not accessible"
    echo '{"data": []}' > oc3_us_gov_east_listings.json
fi

echo "   Attempting US Gov West (Phoenix)..."
if oci marketplace listing list --compartment-id "$OC3_COMPARTMENT_ID" --all --region us-gov-phoenix-1 --profile OC3 --output json > oc3_us_gov_west_listings.json 2>/dev/null; then
    GOV_WEST_COUNT=$(jq '.data | length' oc3_us_gov_west_listings.json 2>/dev/null || echo "0")
    echo "   ✅ US Gov West: $GOV_WEST_COUNT listings"
else
    echo "   ❌ US Gov West: Region not accessible"
    echo '{"data": []}' > oc3_us_gov_west_listings.json
fi

# Combine OC3 regions into single file
echo "   Merging OC3 regional data..."
if command -v jq &> /dev/null; then
    jq -s '{"data": (.[0].data + .[1].data) | unique_by(.id)}' \
        oc3_us_gov_east_listings.json \
        oc3_us_gov_west_listings.json > oc3_government_listings.json
    OC3_TOTAL=$(jq '.data | length' oc3_government_listings.json 2>/dev/null || echo "0")
    echo "✅ OC3 Total Government listings: $OC3_TOTAL"
else
    cp oc3_us_gov_east_listings.json oc3_government_listings.json
fi

# Get OC3 detailed data
echo "📋 Extracting detailed OC3 metadata..."
if oci marketplace listing-summary search-listings-structured --search-query '{}' --all --region us-gov-ashburn-1 --profile OC3 --output json > oc3_government_detailed.json 2>/dev/null; then
    echo "   ✅ Detailed OC3 metadata extracted"
else
    echo "   ⚠️  Could not extract detailed OC3 metadata"
fi

echo ""
echo "Phase 3: OC2 DoD region extraction..."
echo "===================================="

# Extract OC2 DoD data
echo "🏛️  Extracting OC2 DoD marketplace data..."

# Try Langley region
echo "   Attempting US DoD East (Langley)..."
if oci marketplace listing list --compartment-id "$OC2_COMPARTMENT_ID" --region us-langley-1 --profile OC2 --output json > oc2_us_dod_east_listings.json 2>/dev/null; then
    DOD_EAST_COUNT=$(jq '.data | length' oc2_us_dod_east_listings.json 2>/dev/null || echo "0")
    echo "   ✅ US DoD East: $DOD_EAST_COUNT listings"
else
    echo "   ❌ US DoD East: Region not accessible"
    echo '{"data": []}' > oc2_us_dod_east_listings.json
fi

# Try Luke region
echo "   Attempting US DoD West (Luke)..."
if oci marketplace listing list --compartment-id "$OC2_COMPARTMENT_ID" --region us-luke-1 --profile OC2 --output json > oc2_us_dod_west_listings.json 2>/dev/null; then
    DOD_WEST_COUNT=$(jq '.data | length' oc2_us_dod_west_listings.json 2>/dev/null || echo "0")
    echo "   ✅ US DoD West: $DOD_WEST_COUNT listings"
else
    echo "   ❌ US DoD West: Region not accessible"
    echo '{"data": []}' > oc2_us_dod_west_listings.json
fi

# Combine OC2 DoD regions into single file
echo "   Merging OC2 DoD regional data..."
if command -v jq &> /dev/null; then
    jq -s '{"data": (.[0].data + .[1].data) | unique_by(.id)}' \
        oc2_us_dod_east_listings.json \
        oc2_us_dod_west_listings.json > oc2_dod_listings.json
    OC2_TOTAL=$(jq '.data | length' oc2_dod_listings.json 2>/dev/null || echo "0")
    echo "✅ OC2 Total DoD listings: $OC2_TOTAL"
else
    cp oc2_us_dod_east_listings.json oc2_dod_listings.json
fi

# Get OC2 detailed data
echo "📋 Extracting detailed OC2 metadata..."
if oci marketplace listing-summary search-listings-structured --search-query '{}' --region us-langley-1 --profile OC2 --output json > oc2_dod_detailed.json 2>/dev/null; then
    echo "   ✅ Detailed OC2 metadata extracted"
else
    echo "   ⚠️  Could not extract detailed OC2 metadata"
fi

echo ""
echo "Phase 4: Creating consolidated summary..."
echo "========================================"

# Count listings per classification
OC1_COUNT=$(jq '.data | length' oc1_commercial_listings.json 2>/dev/null || echo "0")
OC3_COUNT=$(jq '.data | length' oc3_government_listings.json 2>/dev/null || echo "0")
OC2_COUNT=$(jq '.data | length' oc2_dod_listings.json 2>/dev/null || echo "0")

TOTAL_COUNT=$((OC1_COUNT + OC3_COUNT + OC2_COUNT))

cat > extraction_report.txt << EOF
Oracle Cloud Marketplace Extraction Report
Generated: $(date)
Extracted by: $(whoami)
Machine: $(hostname)

Classification Breakdown:
========================
OC1 Commercial:      $OC1_COUNT listings
OC3 US Government:   $OC3_COUNT listings
OC2 DoD:            $OC2_COUNT listings
------------------------
TOTAL:              $TOTAL_COUNT listings

Compartment IDs Used:
====================
OC2 (DoD): $OC2_COMPARTMENT_ID
OC3 (Gov): $OC3_COMPARTMENT_ID

Files Generated:
================
OC1 Commercial:
- oc1_commercial_listings.json
- oc1_commercial_detailed.json
- oc1_commercial_publishers.json

OC3 Government:
- oc3_government_listings.json
- oc3_government_detailed.json

OC2 DoD:
- oc2_dod_listings.json
- oc2_dod_detailed.json

Next Steps:
===========
Run the Python processor to create sales Excel:
   python3 ../process_oci_customer.py

The processor will create:
   - oracle_marketplace_catalog.xlsx with 3 sheets (OC1, OC2, OC3)
EOF

echo ""
echo "========================================="
echo "✅ Extraction Complete!"
echo "========================================="
echo ""
echo "📊 Summary:"
echo "   OC1 Commercial:    $OC1_COUNT listings"
echo "   OC3 Government:    $OC3_COUNT listings"
echo "   OC2 DoD:          $OC2_COUNT listings"
echo "   ────────────────────────────────────"
echo "   TOTAL:            $TOTAL_COUNT listings"
echo ""
echo "📁 All files saved in: $(pwd)"
echo ""
echo "🎯 Next step: Create Excel catalog"
echo "   Command: python3 ../process_oci_customer.py"
echo ""

cd ..

echo "Ready to process data for Excel export!"