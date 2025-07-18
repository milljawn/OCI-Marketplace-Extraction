# Oracle Cloud Marketplace Data Extractor

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-lightgrey)](https://github.com)

> **Comprehensive Oracle Cloud Marketplace catalog extraction and government compliance analysis for global sales organizations**

Extract, analyze, and export all Oracle Cloud Marketplace offerings (562+ listings) with detailed government compliance assessment, sales prioritization, and comprehensive metadata analysis across Commercial (OC1), Government (OC3), and DoD (OC2) realms.

## 🎯 Features

- **Complete Multi-Realm Extraction**: All Oracle Cloud Marketplace listings across OC1, OC2, OC3
- **Government Compliance Analysis**: FedRAMP, CMMC, DoD Impact Levels assessment
- **Sales Intelligence**: Priority scoring, market categorization, enterprise readiness assessment
- **Professional Excel Output**: 4-sheet comprehensive analysis for global sales teams
- **Publisher Analysis**: Complete partner ecosystem insights
- **Interactive Configuration**: Prompts for customer-specific compartment IDs
- **Error Recovery**: Robust handling of network issues and partial data

## 📊 Output

### Excel Spreadsheet with 4 Professional Sheets:
- **Complete Catalog**: Full product database with 40+ data points per listing
- **Government Opportunities**: Specialized government sales analysis and compliance scoring
- **Publisher Analysis**: Partner ecosystem breakdown and strategic recommendations
- **Executive Summary**: Leadership dashboard with key metrics and insights

### Key Data Points:
- Product details, pricing models, technical requirements
- Government region availability (Commercial, US Gov, DoD)
- Compliance certifications (FedRAMP, CMMC, Impact Levels)
- Sales prioritization (1-10 scoring) and market categorization
- Publisher information and strategic partnership recommendations

## 🚀 Quick Start

### Prerequisites
- Oracle Cloud Infrastructure (OCI) account with marketplace access
- Multi-realm access: OC1 (Commercial), OC2 (DoD), and/or OC3 (Government)
- Python 3.8+ installed
- OCI CLI configured with valid profiles for each realm

### Installation

#### macOS
```bash
# Install dependencies
brew install python oci-cli jq
pip3 install pandas openpyxl requests beautifulsoup4 lxml

# Clone repository
git clone https://github.com/your-org/oracle-marketplace-extractor.git
cd oracle-marketplace-extractor

# Configure OCI CLI profiles for each realm
oci setup config  # Follow prompts for OC1, OC2, OC3 profiles

# Run extraction (will prompt for compartment IDs)
./extract_marketplace_customer.sh
python3 process_oci_customer.py
```

#### Windows
```cmd
# Install Python from python.org (ensure "Add to PATH" is checked)
# Install OCI CLI: https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/cliinstall.htm

# Install Python packages
pip install pandas openpyxl requests beautifulsoup4 lxml

# Clone repository and navigate to directory
git clone https://github.com/your-org/oracle-marketplace-extractor.git
cd oracle-marketplace-extractor

# Configure OCI CLI profiles
oci setup config

# Run extraction
extract_marketplace_customer.bat
python process_oci_customer.py
```

#### Linux
```bash
# Install dependencies (Ubuntu/Debian)
sudo apt update
sudo apt install python3 python3-pip jq curl
pip3 install pandas openpyxl requests beautifulsoup4 lxml

# Install OCI CLI
bash -c "$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)"

# Clone and setup
git clone https://github.com/your-org/oracle-marketplace-extractor.git
cd oracle-marketplace-extractor
oci setup config

# Run extraction
chmod +x extract_marketplace_customer.sh
./extract_marketplace_customer.sh
python3 process_oci_customer.py
```

## 📁 Project Structure

```
oracle-marketplace-extractor/
├── README.md                           # This file
├── LICENSE                            # MIT License
├── requirements.txt                   # Python dependencies
├── extract_marketplace_customer.sh    # macOS/Linux extraction script
├── extract_marketplace_customer.bat   # Windows extraction script (TBD)
├── process_oci_customer.py            # Data processor and Excel generator
├── marketplace_data/                  # Raw JSON data (generated)
│   ├── all_listings_commercial.json  # Commercial (OC1) data
│   ├── oc3_us_gov_east_listings.json # US Government East data
│   ├── oc3_us_gov_west_listings.json # US Government West data
│   ├── oc2_us_dod_east_listings.json # DoD East (Langley) data
│   ├── oc2_us_dod_west_listings.json # DoD West (Luke) data
│   └── legacy_us_dod_*.json          # Legacy DoD region data
├── oracle_marketplace_global_sales_catalog.xlsx  # Final output (generated)
└── docs/                             # Additional documentation
    ├── TROUBLESHOOTING.md
    ├── GOVERNMENT_COMPLIANCE.md
    └── SALES_GUIDE.md
```

## 🔧 Prerequisites

### Oracle Cloud Access Requirements

#### Minimum Requirements:
- **OC1 (Commercial)**: Active Oracle Cloud Infrastructure account with marketplace access
- **API Access**: OCI CLI authentication configured with profile [OC1]

#### Government/DoD Access (Optional but Recommended):
- **OC2 (DoD)**: Access to Oracle Defense Cloud with compartment ID
- **OC3 (Government)**: Access to Oracle Government Cloud with compartment ID
- **Multi-Realm Profiles**: Separate OCI CLI profiles for each realm

> **Note**: The tool works with any combination of realms. Government/DoD access enhances compliance analysis capabilities.

### OCI CLI Configuration

The tool requires valid OCI CLI profiles for each realm you have access to:

#### Example ~/.oci/config:
```ini
[OC1]
user=ocid1.user.oc1..aaaaaaaa...
fingerprint=xx:xx:xx:xx...
tenancy=ocid1.tenancy.oc1..aaaaaaaa...
region=us-ashburn-1
key_file=/path/to/oc1_key.pem

[OC2]
user=ocid1.user.oc2..aaaaaaaa...
fingerprint=xx:xx:xx:xx...
tenancy=ocid1.tenancy.oc2..aaaaaaaa...
region=us-langley-1
key_file=/path/to/oc2_key.pem

[OC3]
user=ocid1.user.oc3..aaaaaaaa...
fingerprint=xx:xx:xx:xx...
tenancy=ocid1.tenancy.oc3..aaaaaaaa...
region=us-gov-ashburn-1
key_file=/path/to/oc3_key.pem
```

Test your configuration:
```bash
oci iam user list --profile OC1
oci iam user list --profile OC2  # If you have DoD access
oci iam user list --profile OC3  # If you have Gov access
```

## 🖥️ Usage

### Interactive Extraction
```bash
# Run the extraction script
./extract_marketplace_customer.sh

# When prompted, enter your compartment IDs:
# Enter your OC2 (DoD) tenancy compartment ID: ocid1.tenancy.oc2..aaaaaaaa...
# Enter your OC3 (Government) tenancy compartment ID: ocid1.tenancy.oc3..aaaaaaaa...

# Process to professional Excel format
python3 process_oci_customer.py
```

### Finding Your Compartment IDs

#### For OC2 (DoD) and OC3 (Government):
1. Log into the respective Oracle Cloud console
2. Navigate to Identity & Security > Compartments
3. Copy the OCID of your tenancy compartment
4. Use these values when prompted by the extraction script

### Advanced Options

#### Single Realm Extraction
If you only have access to commercial (OC1):
```bash
# The script will gracefully handle missing realms
# Commercial data will still be extracted and processed
```

#### Custom Output Location
```bash
# Modify the data directory in the Python script
processor = OCIMarketplaceSalesProcessor(data_dir="custom_data_path")
```

## 📊 Output Analysis

### Excel Sheet Breakdown

#### Sheet 1: Complete Catalog
- **40+ columns** with comprehensive product information
- Regional availability matrix (OC1/OC2/OC3)
- Government compliance scoring
- Sales priority rankings
- Technical deployment details

#### Sheet 2: Government Opportunities
- **Filtered view** of government-authorized products only
- Compliance scoring (FedRAMP, CMMC, Impact Levels)
- Government sales priorities (CRITICAL/HIGH/MEDIUM/LOW)
- Multi-realm availability analysis

#### Sheet 3: Publisher Analysis
- **Publisher ecosystem** overview and statistics
- Government vs commercial product ratios
- Strategic value assessment
- Partnership recommendations

#### Sheet 4: Executive Summary
- **Key metrics dashboard** for leadership
- Regional breakdown statistics
- Government sales opportunity counts
- Top categories and publishers

### Government Compliance Columns

| Column | Description | Values |
|--------|-------------|--------|
| `Commercial_OC1` | Available in Commercial Cloud | Yes/No |
| `US_Gov_OC3` | Available in Government Cloud | Yes/No |
| `DoD_OC2` | Available in Defense Cloud | Yes/No |
| `Gov_Authorization_Level` | Government clearance level | DoD/FedRAMP/Commercial Only |
| `FedRAMP_Status` | FedRAMP compliance level | High/Moderate/Low/Ready |
| `DoD_Impact_Level` | DoD Impact Level support | IL2/IL4/IL5/IL6 |
| `CMMC_Level` | CMMC compliance level | Level 1+/2/3 |
| `Gov_Sales_Priority` | Government opportunity priority | CRITICAL/HIGH/MEDIUM/LOW |

## 🏛️ Government Compliance Guide

### Understanding Oracle Cloud Realms

#### OC1 (Commercial Cloud)
- **Purpose**: Standard commercial workloads
- **Compliance**: Basic cloud security standards
- **Availability**: Global, no restrictions

#### OC2 (Defense Cloud)
- **Purpose**: DoD classified workloads up to IL6
- **Compliance**: CMMC, DoD Impact Levels, FedRAMP High
- **Availability**: US-based, requires DoD authorization

#### OC3 (Government Cloud)
- **Purpose**: US Government civilian agencies
- **Compliance**: FedRAMP Moderate/High
- **Availability**: US Government entities only

### Compliance Frameworks

#### FedRAMP (Federal Risk and Authorization Management Program)
- **Low**: Basic government workloads
- **Moderate**: Standard government data
- **High**: High impact government systems

#### CMMC (Cybersecurity Maturity Model Certification)
- **Level 1**: Basic cyber hygiene
- **Level 2**: Intermediate cybersecurity practices
- **Level 3**: Advanced/expert cybersecurity practices

#### DoD Impact Levels
- **IL2**: Controlled Unclassified Information (CUI)
- **IL4**: CUI requiring additional protections
- **IL5**: CUI requiring highest protection
- **IL6**: Classified National Security Systems

## 🔍 Troubleshooting

### Common Issues

#### Missing Compartment IDs
```bash
Error: Both compartment IDs are required
Solution: Contact your Oracle Cloud administrator for compartment OCIDs
```

#### Profile Not Found
```bash
Error: Profile 'OC2' not found
Solution: Run 'oci setup config' to create missing profiles
```

#### Empty Government Data
```bash
Warning: OC2/OC3 regions not accessible
Solution: Normal if you don't have government cloud access
```

#### Permission Denied
```bash
Error: Insufficient permissions
Solution: Verify your user has marketplace read permissions
```

### Debugging Commands

```bash
# Test realm connectivity
oci iam user list --profile OC1
oci iam user list --profile OC2
oci iam user list --profile OC3

# Check data extraction
ls -la marketplace_data/
head marketplace_data/all_listings_commercial.json

# Validate JSON integrity
python3 -c "import json; print('Valid JSON')" < marketplace_data/all_listings_commercial.json

# Test Python dependencies
python3 -c "import pandas, openpyxl; print('Dependencies OK')"
```

## 📈 Performance

### Extraction Times
- **Commercial extraction**: 3-5 minutes
- **Government regions**: 2-4 minutes each
- **Data processing**: 2-5 minutes
- **Total runtime**: 10-20 minutes

### Data Volume
- **Total listings**: 562+ across all realms
- **Data points**: 40+ per listing
- **JSON files**: 50-150MB total
- **Excel output**: 5-20MB

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone and setup development environment
git clone https://github.com/your-org/oracle-marketplace-extractor.git
cd oracle-marketplace-extractor

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🚀 Enterprise Usage

This tool is designed for global sales organizations requiring comprehensive Oracle Cloud Marketplace intelligence across multiple realms. The Excel output format enables immediate integration with existing sales processes, CRM systems, and executive reporting.

### Recommended Workflow:
1. **Extract**: Run monthly to capture new marketplace additions
2. **Analyze**: Use Government Opportunities sheet for federal sales targeting
3. **Report**: Share Executive Summary with leadership
4. **Partner**: Leverage Publisher Analysis for strategic partnerships
