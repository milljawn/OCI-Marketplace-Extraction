# Oracle Cloud Marketplace Data Extractor

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-lightgrey)](https://github.com)

> **Comprehensive Oracle Cloud Marketplace catalog extraction and government compliance analysis for sales teams**

Extract, analyze, and export all Oracle Cloud Marketplace offerings (562+ listings) with detailed government compliance assessment, sales prioritization, and comprehensive metadata analysis.

## 🎯 Features

- **Complete Marketplace Extraction**: All 562+ Oracle Cloud Marketplace listings
- **Government Compliance Analysis**: FedRAMP, CMMC, DoD Impact Levels, UK Government readiness
- **Sales Intelligence**: Priority scoring, market categorization, enterprise readiness assessment
- **Multi-Format Export**: Excel spreadsheets with multiple analysis sheets
- **Publisher Analysis**: Comprehensive partner ecosystem insights
- **Automated Processing**: One-click extraction and analysis
- **Error Recovery**: Robust handling of network issues and partial data

## 📊 Output

### Excel Spreadsheet with Multiple Sheets:
- **Marketplace Catalog**: Complete listing details (70+ columns)
- **Government Analysis**: Compliance readiness assessment
- **Sales Priorities**: High/Medium/Low opportunity ranking
- **Publisher Breakdown**: Partner ecosystem analysis
- **Summary Statistics**: Executive dashboard metrics

### Key Data Points:
- Product details, pricing, technical requirements
- Government region availability (US Gov, UK Gov, DoD)
- Compliance certifications (FedRAMP, CMMC, Impact Levels)
- Sales prioritization and market categorization
- Publisher information and contact details

## 🚀 Quick Start

### Prerequisites
- Oracle Cloud Infrastructure (OCI) account with marketplace access
- Python 3.8+ installed
- OCI CLI configured with valid credentials

### Installation

#### macOS
```bash
# Install dependencies
brew install python oci-cli jq
pip3 install pandas openpyxl requests beautifulsoup4 lxml

# Clone repository
git clone https://github.com/your-org/oracle-marketplace-extractor.git
cd oracle-marketplace-extractor

# Configure OCI CLI
oci setup config

# Run extraction
./extract_marketplace_data.sh
python3 process_oci_data.py
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

# Configure OCI CLI
oci setup config

# Run extraction
extract_marketplace_data.bat
python process_oci_data.py
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
chmod +x extract_marketplace_data.sh
./extract_marketplace_data.sh
python3 process_oci_data.py
```

## 📁 Project Structure

```
oracle-marketplace-extractor/
├── README.md                           # This file
├── LICENSE                            # MIT License
├── requirements.txt                   # Python dependencies
├── extract_marketplace_data.sh        # macOS/Linux extraction script
├── extract_marketplace_data.bat       # Windows extraction script
├── process_oci_data.py               # Data processor and Excel generator
├── marketplace_data/                  # Raw JSON data (generated)
│   ├── all_listings.json            # Complete marketplace catalog
│   ├── us_gov_listings.json         # US Government region data
│   ├── uk_gov_listings.json         # UK Government region data
│   ├── category_*.json              # Category-specific listings
│   └── publishers.json              # Publisher information
├── oracle_marketplace_complete_catalog.xlsx  # Final output (generated)
└── docs/                             # Additional documentation
    ├── TROUBLESHOOTING.md
    ├── GOVERNMENT_COMPLIANCE.md
    └── SALES_GUIDE.md
```

## 🔧 Prerequisites

### Oracle Cloud Access Requirements

#### Minimum Requirements (All Users):
- **OCI Account**: Active Oracle Cloud Infrastructure account
- **Marketplace Access**: Permission to view Oracle Cloud Marketplace
- **API Access**: OCI CLI authentication configured

#### Government Compliance Analysis (Optional):
- **US Government Regions**: Access to `us-gov-ashburn-1`, `us-gov-phoenix-1`
- **UK Government Regions**: Access to `uk-gov-london-1`
- **DoD Regions**: Access to Oracle Defense Cloud regions

> **Note**: Government region access is not required. The tool provides content-based compliance analysis for all users.

### OCI CLI Configuration

The tool requires valid OCI CLI configuration. Run `oci setup config` and provide:

```
User OCID: ocid1.user.oc1..aaaaaaaa...
Tenancy OCID: ocid1.tenancy.oc1..aaaaaaaa...
Region: us-ashburn-1 (or your preferred region)
API Key: /path/to/your/api/key.pem
```

Test your configuration:
```bash
oci iam user list
```

## 🖥️ Usage

### Basic Extraction
```bash
# Extract all marketplace data
./extract_marketplace_data.sh

# Process to Excel format
python3 process_oci_data.py
```

### Advanced Options

#### Extract Specific Categories Only
```bash
# Modify categories in extract_marketplace_data.sh
categories=("security" "networking" "databases")
```

#### Government Bypass Mode
If you don't have government region access:
```bash
# Use the government bypass processor
python3 process_oci_data_bypass.py
```

#### Custom Output Filename
```python
# Modify in process_oci_data.py
processor.export_to_excel('custom_marketplace_catalog.xlsx')
```

## 📊 Output Analysis

### Government Compliance Columns

| Column | Description | Values |
|--------|-------------|--------|
| `us_government_ready` | US Government compatibility | READY, POTENTIAL, UNKNOWN |
| `us_government_available` | Available in FedRAMP regions | True/False |
| `us_dod_ready` | Department of Defense compatibility | READY, POTENTIAL, UNKNOWN |
| `dod_impact_level` | Supported Impact Levels | IL2, IL4, IL5, IL6 |
| `uk_government_ready` | UK Government compatibility | READY, POTENTIAL, UNKNOWN |
| `fedramp_indicators` | FedRAMP compliance mentioned | True/False |
| `cmmc_indicators` | CMMC compliance mentioned | True/False |
| `export_control_status` | ITAR/EAR restrictions | RESTRICTED, UNRESTRICTED |

### Sales Intelligence Columns

| Column | Description | Values |
|--------|-------------|--------|
| `sales_priority` | Opportunity priority | HIGH, MEDIUM, LOW |
| `market_category` | Market segment | Security, Database, Analytics, etc. |
| `enterprise_readiness` | Enterprise suitability | HIGH, MEDIUM, LOW |
| `deployment_complexity` | Implementation difficulty | LOW, MEDIUM, HIGH |

## 🏛️ Government Compliance Guide

### US Government Requirements

#### FedRAMP (Federal Risk and Authorization Management Program)
- **Purpose**: Standardized security assessment for cloud services
- **Levels**: Low, Moderate, High
- **Detection**: Automatic keyword analysis in product descriptions

#### CMMC (Cybersecurity Maturity Model Certification)
- **Purpose**: DoD cybersecurity framework
- **Levels**: 1, 2, 3
- **Detection**: Content analysis for CMMC mentions

#### DoD Impact Levels
- **IL2**: Controlled Unclassified Information (CUI)
- **IL4**: CUI with additional protections
- **IL5**: CUI requiring highest protection
- **IL6**: Classified information (Secret/Top Secret)

### UK Government Requirements

#### NCSC (National Cyber Security Centre)
- **Purpose**: UK cybersecurity standards
- **Classification**: OFFICIAL, OFFICIAL-SENSITIVE
- **Detection**: UK-specific compliance keywords

## 🔍 Troubleshooting

### Common Issues

#### OCI CLI Not Configured
```bash
Error: No config file found
Solution: Run 'oci setup config'
```

#### Empty Data Files
```bash
Error: No marketplace data found
Solution: Check OCI permissions and re-run extraction
```

#### Government Region Access Denied
```bash
Error: Region not accessible
Solution: Normal - use government bypass mode
```

#### Python Package Missing
```bash
Error: ModuleNotFoundError: No module named 'pandas'
Solution: pip3 install pandas openpyxl
```

### Debugging Commands

```bash
# Test OCI connectivity
oci iam user list

# Check data extraction
ls -la marketplace_data/
head marketplace_data/all_listings.json

# Validate JSON files
python3 -c "import json; print(json.load(open('marketplace_data/all_listings.json'))['data'][:1])"

# Check Python environment
python3 -c "import pandas; print('OK')"
```

## 📈 Performance

### Extraction Times
- **Complete extraction**: 5-10 minutes
- **Data processing**: 2-5 minutes
- **Total runtime**: 10-15 minutes

### Data Volume
- **562+ marketplace listings**
- **70+ data points per listing**
- **JSON files**: ~50-100MB total
- **Excel output**: ~5-15MB

### Rate Limiting
- **Respectful delays**: 2-second intervals between API calls
- **Automatic retry**: Built-in error recovery
- **Batch processing**: Efficient data collection

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

### Testing

```bash
# Unit tests
python -m pytest tests/unit/

# Integration tests (requires OCI access)
python -m pytest tests/integration/

# Linting
flake8 process_oci_data.py
black process_oci_data.py
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
