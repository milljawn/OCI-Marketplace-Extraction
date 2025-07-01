#!/bin/bash

# Oracle Cloud Marketplace Complete Extractor for macOS
# Uses OCI CLI for fast, accurate data extraction

echo "========================================"
echo "Oracle Cloud Marketplace Data Extractor"
echo "Using OCI CLI (Official Method) - macOS"
echo "========================================"

# Check if OCI CLI is installed
if ! command -v oci &> /dev/null; then
    echo "❌ OCI CLI not found. Please install it first:"
    echo "   brew install oci-cli"
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
echo "Phase 1: Extracting complete marketplace catalog..."
echo "================================================="

# Get all marketplace listings with full details
echo "📊 Extracting all marketplace listings..."
if oci marketplace listing list --all --output json > all_listings.json; then
    echo "✅ Successfully extracted main listings"
    LISTING_COUNT=$(jq '.data | length' all_listings.json 2>/dev/null || echo "unknown")
    echo "   Found: $LISTING_COUNT listings"
else
    echo "❌ Failed to extract listings. Check OCI CLI configuration."
    echo "   Try: oci iam user list"
    exit 1
fi

# Get structured search results (additional metadata)
echo "📋 Extracting detailed marketplace metadata..."
if oci marketplace listing-summary search-listings-structured --search-query '{}' --all --output json > listings_detailed.json; then
    echo "✅ Successfully extracted detailed metadata"
else
    echo "⚠️  Warning: Could not extract detailed metadata (proceeding with main data)"
fi

echo ""
echo "Phase 2: Government compliance analysis..."
echo "========================================="

# Function to safely run OCI commands for government regions
safe_oci_gov() {
    local region=$1
    local output_file=$2
    local description=$3
    
    echo "🏛️  Checking $description..."
    if oci marketplace listing list --all --region "$region" --output json > "$output_file" 2>/dev/null; then
        GOV_COUNT=$(jq '.data | length' "$output_file" 2>/dev/null || echo "0")
        echo "   ✅ $description: $GOV_COUNT listings available"
    else
        echo "   ⚠️  $description: Region not accessible (normal if no gov access)"
        echo '{"data": []}' > "$output_file"
    fi
}

# Check different government regions (if accessible)
safe_oci_gov "us-gov-ashburn-1" "us_gov_listings.json" "US Government East region"
safe_oci_gov "us-gov-phoenix-1" "us_gov_west_listings.json" "US Government West region"
safe_oci_gov "uk-gov-london-1" "uk_gov_listings.json" "UK Government region"

echo ""
echo "Phase 3: Extracting comprehensive metadata..."
echo "============================================="

# Get pricing information for each category
echo "📊 Extracting by categories for complete coverage..."
categories=("analytics" "compute" "databases" "developer-tools" "integration" "iot" "machine-learning" "monitoring" "networking" "security" "storage" "business-applications")

for category in "${categories[@]}"; do
    echo "   📁 Extracting $category category..."
    if oci marketplace listing list --all --category "$category" --output json > "category_$category.json" 2>/dev/null; then
        CAT_COUNT=$(jq '.data | length' "category_$category.json" 2>/dev/null || echo "0")
        echo "      Found: $CAT_COUNT listings"
    else
        echo "      ⚠️  Category $category not found"
        echo '{"data": []}' > "category_$category.json"
    fi
done

echo ""
echo "Phase 4: Additional metadata extraction..."
echo "========================================"

# Get publisher information
echo "🏢 Extracting publisher details..."
if oci marketplace publisher list --all --output json > publishers.json; then
    PUB_COUNT=$(jq '.data | length' publishers.json 2>/dev/null || echo "unknown")
    echo "   ✅ Found: $PUB_COUNT publishers"
else
    echo "   ⚠️  Could not extract publisher data"
fi

# Get human-readable summary
echo "📄 Creating summary table..."
oci marketplace listing list --all --output table > listings_summary.txt 2>/dev/null || echo "Summary table creation failed" > listings_summary.txt

# Generate extraction report
echo ""
echo "📊 Generating extraction report..."
cat > extraction_report.txt << EOF
Oracle Cloud Marketplace Extraction Report
Generated: $(date)
Extracted by: $(whoami)
Machine: $(hostname)

Files Generated:
================
- all_listings.json          : Complete marketplace catalog ($LISTING_COUNT listings)
- listings_detailed.json     : Detailed search results
- us_gov_listings.json       : US Government region availability
- us_gov_west_listings.json  : US Government West region availability  
- uk_gov_listings.json       : UK Government region availability
- category_*.json            : Category-specific listings
- publishers.json            : Publisher information ($PUB_COUNT publishers)
- listings_summary.txt       : Human-readable summary
- extraction_report.txt      : This report

Next Steps:
===========
1. Run the Python processor to create Excel spreadsheet:
   python3 ../process_oci_data.py

2. The processor will create:
   - oracle_marketplace_complete_catalog.xlsx (comprehensive spreadsheet)
   - Government compliance analysis
   - Sales prioritization
   - Publisher and category breakdowns

OCI CLI Configuration Used:
==========================
Region: $(oci setup config get 2>/dev/null | grep region || echo "Default")
User: $(oci setup config get 2>/dev/null | grep user || echo "Current user")
EOF

echo ""
echo "========================================="
echo "✅ Extraction Complete!"
echo "========================================="
echo ""
echo "📊 Generated files:"
echo "   - all_listings.json          (Complete marketplace catalog)"
echo "   - listings_detailed.json     (Detailed search results)"
echo "   - us_gov_listings.json       (US Government region listings)"  
echo "   - us_gov_west_listings.json  (US Government West region)"
echo "   - uk_gov_listings.json       (UK Government region listings)"
echo "   - category_*.json            (Category-specific listings)"
echo "   - publishers.json            (Publisher information)"
echo "   - listings_summary.txt       (Human-readable summary)"
echo "   - extraction_report.txt      (Detailed report)"
echo ""
echo "🎯 Next step: Create comprehensive Excel spreadsheet"
echo "   Command: python3 ../process_oci_data.py"
echo ""
echo "📁 All files saved in: $(pwd)"
echo ""

# Go back to parent directory
cd ..

echo "Ready to process data! Run the Python processor next."