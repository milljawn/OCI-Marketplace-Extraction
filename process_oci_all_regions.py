#!/usr/bin/env python3
"""
OCI Marketplace Data Processor - All Regions Sales Focus
Processes Commercial, US Government, and DoD marketplace data into sales-focused CSV
"""

import json
import pandas as pd
import os
from datetime import datetime
import re
from collections import defaultdict

class OCIMarketplaceSalesProcessor:
    def __init__(self, data_dir="marketplace_data"):
        self.data_dir = data_dir
        self.all_listings = {}  # Dict of region -> listings
        self.unique_listings = {}  # Dict of listing_id -> consolidated listing info
        
    def safe_load_json(self, filepath):
        """Safely load JSON file with error handling"""
        if not os.path.exists(filepath):
            print(f"⚠️  File not found: {filepath}")
            return {}
        
        if os.path.getsize(filepath) == 0:
            print(f"⚠️  File is empty: {filepath}")
            return {}
        
        try:
            with open(filepath, 'r') as f:
                content = f.read().strip()
                if not content:
                    return {}
                
                data = json.loads(content)
                return data
                
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error in {filepath}: {e}")
            return {}
        except Exception as e:
            print(f"❌ Error loading {filepath}: {e}")
            return {}
    
    def load_all_regional_data(self):
        """Load marketplace data from all regions"""
        print("Loading marketplace data from all regions...")
        
        regions = [
            ("commercial", "all_listings_commercial.json", "Commercial"),
            ("us_gov_east", "us_gov_east_listings.json", "US Government East"),
            ("us_gov_west", "us_gov_west_listings.json", "US Government West"),
            ("us_dod_east", "us_dod_east_listings.json", "US DoD East"),
            ("us_dod_central", "us_dod_central_listings.json", "US DoD Central"),
            ("us_dod_west", "us_dod_west_listings.json", "US DoD West"),
            ("uk_gov", "uk_gov_listings.json", "UK Government")
        ]
        
        total_listings = 0
        
        for region_key, filename, region_name in regions:
            filepath = os.path.join(self.data_dir, filename)
            data = self.safe_load_json(filepath)
            
            if data and 'data' in data:
                self.all_listings[region_key] = data['data']
                count = len(data['data'])
                total_listings += count
                print(f"✅ {region_name}: {count} listings")
                
                # Load detailed data if available
                detailed_file = filepath.replace("_listings.json", "_detailed.json")
                detailed_data = self.safe_load_json(detailed_file)
                if detailed_data and 'data' in detailed_data:
                    self.merge_detailed_data(region_key, detailed_data['data'])
            else:
                self.all_listings[region_key] = []
                print(f"⚠️  {region_name}: No data available")
        
        print(f"\n📊 Total regional listings loaded: {total_listings}")
        return total_listings
    
    def merge_detailed_data(self, region_key, detailed_data):
        """Merge detailed data with main listings"""
        if not detailed_data or region_key not in self.all_listings:
            return
            
        detailed_dict = {item.get('id'): item for item in detailed_data if item.get('id')}
        
        for listing in self.all_listings[region_key]:
            listing_id = listing.get('id')
            if listing_id in detailed_dict:
                detailed_item = detailed_dict[listing_id]
                for key, value in detailed_item.items():
                    if key not in listing or listing[key] is None:
                        listing[key] = value
    
    def consolidate_unique_listings(self):
        """Consolidate listings across regions to identify unique products"""
        print("\nConsolidating unique listings across regions...")
        
        for region_key, listings in self.all_listings.items():
            for listing in listings:
                listing_id = listing.get('id', '')
                
                if listing_id not in self.unique_listings:
                    # First time seeing this listing
                    self.unique_listings[listing_id] = {
                        'listing': listing,
                        'regions': {region_key: True},
                        'primary_region': region_key
                    }
                else:
                    # Listing exists in multiple regions
                    self.unique_listings[listing_id]['regions'][region_key] = True
                    
                    # Merge any additional data from this region's version
                    existing = self.unique_listings[listing_id]['listing']
                    for key, value in listing.items():
                        if key not in existing or existing[key] is None:
                            existing[key] = value
        
        print(f"✅ Identified {len(self.unique_listings)} unique marketplace listings")
        return len(self.unique_listings)
    
    def process_to_sales_csv(self):
        """Convert consolidated data to sales-focused CSV format"""
        print("\nProcessing data for sales team CSV...")
        
        sales_data = []
        
        for listing_id, listing_info in self.unique_listings.items():
            listing = listing_info['listing']
            regions = listing_info['regions']
            
            try:
                # Extract key information for sales
                row = {
                    # Core Product Information
                    'Product_Name': self.safe_get(listing, 'name'),
                    'Publisher': self.get_publisher_name(listing),
                    'Category': self.get_category(listing),
                    'Brief_Description': self.clean_text(self.safe_get(listing, 'short-description'), 200),
                    
                    # Sales-Critical Information
                    'Pricing_Model': self.get_pricing_model(listing),
                    'Estimated_Price': self.get_estimated_price(listing),
                    'Free_Trial': 'Yes' if self.safe_get(listing, 'free-trial-available') else 'No',
                    
                    # Regional Availability
                    'Commercial_Available': 'Yes' if regions.get('commercial') else 'No',
                    'US_Gov_Available': 'Yes' if (regions.get('us_gov_east') or regions.get('us_gov_west')) else 'No',
                    'US_DoD_Available': 'Yes' if any(k.startswith('us_dod') for k in regions) else 'No',
                    'UK_Gov_Available': 'Yes' if regions.get('uk_gov') else 'No',
                    
                    # Compliance & Certifications
                    'FedRAMP_Status': self.determine_fedramp_status(listing),
                    'DoD_Impact_Level': self.determine_impact_level(listing),
                    'CMMC_Level': self.determine_cmmc_level(listing),
                    'Security_Certifications': self.get_security_certifications(listing),
                    
                    # Sales Intelligence
                    'Sales_Priority': self.calculate_sales_priority_score(listing, regions),
                    'Target_Customer_Size': self.determine_target_customer_size(listing),
                    'Industry_Focus': self.determine_industry_focus(listing),
                    'Use_Case': self.extract_primary_use_case(listing),
                    
                    # Technical Requirements
                    'Deployment_Method': self.get_deployment_method(listing),
                    'Integration_Complexity': self.assess_integration_complexity(listing),
                    'Supported_Platforms': self.get_supported_platforms(listing),
                    
                    # Contact & Support
                    'Support_Type': self.determine_support_type(listing),
                    'Documentation_Available': 'Yes' if self.safe_get(listing, 'documentation-url') else 'No',
                    'Oracle_Validated': 'Yes' if self.safe_get(listing, 'oracle-validated') else 'No',
                    
                    # Competitive Intelligence
                    'Competitor_Products': self.identify_competitors(listing),
                    'Unique_Value_Prop': self.extract_value_proposition(listing),
                    
                    # Sales Enablement
                    'Demo_Available': self.check_demo_availability(listing),
                    'POC_Duration': self.estimate_poc_duration(listing),
                    'Reference_Customers': self.check_reference_availability(listing),
                    
                    # URLs for Sales Team
                    'Marketplace_URL': self.generate_marketplace_url(listing_id),
                    'Documentation_URL': self.safe_get(listing, 'documentation-url'),
                    'Video_Demo_URL': self.safe_get(listing, 'video-url'),
                    
                    # Internal Use
                    'Listing_ID': listing_id.replace('ocid1.marketplace.listing.', ''),
                    'Last_Updated': self.format_date(self.safe_get(listing, 'time-updated')),
                    'Oracle_Partner_Level': self.determine_partner_level(listing),
                    
                    # Sales Notes
                    'Gov_Sales_Notes': self.generate_gov_sales_notes(listing, regions),
                    'Key_Features': self.extract_key_features(listing),
                    'Implementation_Timeline': self.estimate_implementation_timeline(listing)
                }
                
                sales_data.append(row)
                
            except Exception as e:
                print(f"⚠️  Error processing listing {listing_id}: {e}")
                continue
        
        print(f"✅ Processed {len(sales_data)} listings for sales team")
        return sales_data
    
    def safe_get(self, data, keys, default=''):
        """Safely extract nested data"""
        if isinstance(keys, str):
            return data.get(keys, default) or default
        
        current = data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current if current is not None else default
    
    def clean_text(self, text, max_length=None):
        """Clean text for CSV output"""
        if not text:
            return ''
        
        # Remove excessive whitespace and newlines
        text = ' '.join(str(text).split())
        
        # Truncate if needed
        if max_length and len(text) > max_length:
            text = text[:max_length-3] + '...'
        
        return text
    
    def get_publisher_name(self, listing):
        """Extract publisher name"""
        publisher = self.safe_get(listing, 'publisher', {})
        if isinstance(publisher, dict):
            return publisher.get('name') or publisher.get('display-name') or 'Unknown'
        return str(publisher) if publisher else 'Unknown'
    
    def get_category(self, listing):
        """Get primary category"""
        categories = self.safe_get(listing, 'categories') or self.safe_get(listing, 'category-facet')
        if categories and isinstance(categories, list) and len(categories) > 0:
            return categories[0]
        return categories if isinstance(categories, str) else 'Uncategorized'
    
    def get_pricing_model(self, listing):
        """Determine pricing model for sales"""
        pricing = self.safe_get(listing, ['pricing', 'type'])
        
        pricing_map = {
            'FREE': 'Free',
            'BYOL': 'Bring Your Own License',
            'PAID': 'Pay-As-You-Go',
            'SUBSCRIPTION': 'Subscription'
        }
        
        return pricing_map.get(pricing, pricing or 'Contact Sales')
    
    def get_estimated_price(self, listing):
        """Get estimated price for sales reference"""
        pricing = self.safe_get(listing, 'pricing', {})
        pricing_type = pricing.get('type')
        
        if pricing_type == 'FREE':
            return 'Free'
        elif pricing_type == 'BYOL':
            return 'License Required'
        
        rate = pricing.get('rate')
        if rate:
            unit = pricing.get('unit', 'hour')
            currency = pricing.get('currency', 'USD')
            return f"{rate} {currency}/{unit}"
        
        return 'Contact for Pricing'
    
    def determine_fedramp_status(self, listing):
        """Determine FedRAMP status"""
        text_content = self.get_listing_text_content(listing)
        
        if 'fedramp high' in text_content:
            return 'FedRAMP High'
        elif 'fedramp moderate' in text_content:
            return 'FedRAMP Moderate'
        elif 'fedramp low' in text_content or 'fedramp' in text_content:
            return 'FedRAMP Ready'
        elif any(term in text_content for term in ['federal', 'government certified', 'fisma']):
            return 'FedRAMP Candidate'
        
        return 'Not Specified'
    
    def determine_impact_level(self, listing):
        """Determine DoD Impact Level support"""
        text_content = self.get_listing_text_content(listing)
        
        levels = []
        if 'il6' in text_content or 'impact level 6' in text_content:
            return 'IL6 (Secret)'
        elif 'il5' in text_content or 'impact level 5' in text_content:
            return 'IL5'
        elif 'il4' in text_content or 'impact level 4' in text_content:
            return 'IL4'
        elif 'il2' in text_content or 'impact level 2' in text_content:
            return 'IL2'
        
        return 'Not Specified'
    
    def determine_cmmc_level(self, listing):
        """Determine CMMC Level"""
        text_content = self.get_listing_text_content(listing)
        
        if 'cmmc level 3' in text_content or 'cmmc l3' in text_content:
            return 'CMMC Level 3'
        elif 'cmmc level 2' in text_content or 'cmmc l2' in text_content:
            return 'CMMC Level 2'
        elif 'cmmc level 1' in text_content or 'cmmc l1' in text_content or 'cmmc' in text_content:
            return 'CMMC Level 1+'
        
        return 'Not Specified'
    
    def get_security_certifications(self, listing):
        """Extract security certifications"""
        text_content = self.get_listing_text_content(listing)
        
        certs = []
        cert_map = {
            'SOC 2': ['soc 2', 'soc2', 'soc ii'],
            'ISO 27001': ['iso 27001', 'iso27001'],
            'PCI DSS': ['pci dss', 'pci-dss', 'payment card'],
            'HIPAA': ['hipaa'],
            'HITRUST': ['hitrust'],
            'StateRAMP': ['stateramp', 'state ramp'],
            'NIST 800-53': ['nist 800-53', 'nist 800'],
            'FIPS 140-2': ['fips 140-2', 'fips 140']
        }
        
        for cert_name, keywords in cert_map.items():
            if any(keyword in text_content for keyword in keywords):
                certs.append(cert_name)
        
        return '; '.join(certs) if certs else 'Standard'
    
    def calculate_sales_priority_score(self, listing, regions):
        """Calculate sales priority score (1-10)"""
        score = 5  # Base score
        
        # Publisher weight
        publisher = str(self.get_publisher_name(listing)).lower()
        tier1_publishers = ['microsoft', 'vmware', 'palo alto', 'fortinet', 'splunk', 'cisco']
        tier2_publishers = ['red hat', 'citrix', 'f5', 'checkpoint', 'crowdstrike']
        
        if any(pub in publisher for pub in tier1_publishers):
            score += 2
        elif any(pub in publisher for pub in tier2_publishers):
            score += 1
        
        # Government availability boost
        if regions.get('us_gov_east') or regions.get('us_gov_west'):
            score += 1
        if any(k.startswith('us_dod') for k in regions):
            score += 2
        
        # Category importance
        category = str(self.get_category(listing)).lower()
        high_value_categories = ['security', 'networking', 'database', 'analytics']
        if any(cat in category for cat in high_value_categories):
            score += 1
        
        # Compliance certifications
        if self.determine_fedramp_status(listing) != 'Not Specified':
            score += 1
        
        return min(10, max(1, score))
    
    def determine_target_customer_size(self, listing):
        """Determine target customer size"""
        pricing_model = self.get_pricing_model(listing)
        text_content = self.get_listing_text_content(listing)
        
        enterprise_indicators = ['enterprise', 'scalable', 'high availability', 'multi-tenant']
        smb_indicators = ['small business', 'starter', 'basic', 'simple']
        
        if any(term in text_content for term in enterprise_indicators):
            return 'Enterprise'
        elif any(term in text_content for term in smb_indicators):
            return 'SMB'
        elif pricing_model == 'Free':
            return 'All Sizes'
        
        return 'Mid-Market'
    
    def determine_industry_focus(self, listing):
        """Determine industry focus"""
        text_content = self.get_listing_text_content(listing)
        
        industry_keywords = {
            'Healthcare': ['healthcare', 'medical', 'hipaa', 'patient', 'clinical'],
            'Financial': ['financial', 'banking', 'fintech', 'payment', 'trading'],
            'Government': ['government', 'federal', 'public sector', 'civic'],
            'Retail': ['retail', 'ecommerce', 'pos', 'inventory', 'customer'],
            'Manufacturing': ['manufacturing', 'industrial', 'iot', 'scada', 'supply chain'],
            'Education': ['education', 'academic', 'learning', 'student', 'university'],
            'Energy': ['energy', 'utility', 'oil', 'gas', 'renewable']
        }
        
        industries = []
        for industry, keywords in industry_keywords.items():
            if any(keyword in text_content for keyword in keywords):
                industries.append(industry)
        
        return '; '.join(industries) if industries else 'Cross-Industry'
    
    def extract_primary_use_case(self, listing):
        """Extract primary use case"""
        category = str(self.get_category(listing)).lower()
        name = str(self.safe_get(listing, 'name', '')).lower()
        
        use_case_map = {
            'security': 'Cybersecurity & Compliance',
            'database': 'Data Management',
            'analytics': 'Business Intelligence',
            'networking': 'Network Infrastructure',
            'compute': 'Cloud Infrastructure',
            'storage': 'Data Storage & Backup',
            'monitoring': 'Performance Monitoring',
            'integration': 'System Integration',
            'machine-learning': 'AI/ML Workloads',
            'developer-tools': 'Application Development'
        }
        
        for key, use_case in use_case_map.items():
            if key in category or key in name:
                return use_case
        
        return 'General Purpose'
    
    def get_deployment_method(self, listing):
        """Get deployment method"""
        package_type = str(self.safe_get(listing, 'package-type', '')).upper()
        
        deployment_map = {
            'IMAGE': 'VM Image',
            'STACK': 'Stack Template',
            'TERRAFORM': 'Terraform',
            'CONTAINER': 'Container',
            'HELM': 'Helm Chart',
            'ORCHESTRATION': 'Orchestration'
        }
        
        return deployment_map.get(package_type, 'Standard Deployment')
    
    def assess_integration_complexity(self, listing):
        """Assess integration complexity"""
        package_type = str(self.safe_get(listing, 'package-type', '')).upper()
        text_content = self.get_listing_text_content(listing)
        
        if package_type == 'IMAGE':
            return 'Low'
        elif any(term in text_content for term in ['complex', 'enterprise', 'custom']):
            return 'High'
        elif package_type in ['STACK', 'TERRAFORM', 'HELM']:
            return 'Medium'
        
        return 'Medium'
    
    def get_supported_platforms(self, listing):
        """Get supported platforms"""
        os_list = self.safe_get(listing, 'supported-operating-systems', [])
        if os_list and isinstance(os_list, list):
            return '; '.join(os_list)
        
        return 'Oracle Linux Compatible'
    
    def determine_support_type(self, listing):
        """Determine support type"""
        support_url = self.safe_get(listing, 'support-url')
        publisher = str(self.get_publisher_name(listing)).lower()
        
        if 'oracle' in publisher:
            return 'Oracle Support'
        elif support_url:
            return 'Vendor Support'
        else:
            return 'Community Support'
    
    def identify_competitors(self, listing):
        """Identify competitor products"""
        name = str(self.safe_get(listing, 'name', '')).lower()
        category = str(self.get_category(listing)).lower()
        
        competitor_map = {
            'firewall': 'Cisco ASA, Fortinet, Check Point',
            'load balancer': 'F5, Citrix ADC, HAProxy',
            'database': 'AWS RDS, Azure SQL, MongoDB Atlas',
            'analytics': 'Tableau, PowerBI, Qlik',
            'monitoring': 'Datadog, New Relic, Splunk',
            'backup': 'Veeam, Commvault, Veritas'
        }
        
        for key, competitors in competitor_map.items():
            if key in name or key in category:
                return competitors
        
        return 'Various'
    
    def extract_value_proposition(self, listing):
        """Extract unique value proposition"""
        description = self.safe_get(listing, 'short-description', '')
        if not description:
            return 'Enterprise-grade solution'
        
        # Extract first sentence as value prop
        sentences = description.split('.')
        if sentences:
            return self.clean_text(sentences[0], 100)
        
        return self.clean_text(description, 100)
    
    def check_demo_availability(self, listing):
        """Check if demo is available"""
        video_url = self.safe_get(listing, 'video-url')
        free_trial = self.safe_get(listing, 'free-trial-available')
        
        if video_url:
            return 'Video Demo'
        elif free_trial:
            return 'Free Trial'
        else:
            return 'Contact Sales'
    
    def estimate_poc_duration(self, listing):
        """Estimate POC duration"""
        complexity = self.assess_integration_complexity(listing)
        
        if complexity == 'Low':
            return '1-2 weeks'
        elif complexity == 'Medium':
            return '2-4 weeks'
        else:
            return '4-8 weeks'
    
    def check_reference_availability(self, listing):
        """Check reference customer availability"""
        publisher = str(self.get_publisher_name(listing)).lower()
        tier1_publishers = ['microsoft', 'vmware', 'oracle', 'palo alto', 'fortinet']
        
        if any(pub in publisher for pub in tier1_publishers):
            return 'Available'
        
        return 'Upon Request'
    
    def generate_marketplace_url(self, listing_id):
        """Generate marketplace URL"""
        clean_id = listing_id.replace('ocid1.marketplace.listing.', '')
        return f"https://cloudmarketplace.oracle.com/marketplace/en_US/listing/{clean_id}"
    
    def format_date(self, date_string):
        """Format date for readability"""
        if not date_string:
            return ''
        
        try:
            # Handle ISO format dates
            if 'T' in str(date_string):
                date_obj = datetime.fromisoformat(str(date_string).replace('Z', '+00:00'))
                return date_obj.strftime('%Y-%m-%d')
        except:
            pass
        
        return str(date_string)[:10] if date_string else ''
    
    def determine_partner_level(self, listing):
        """Determine Oracle partner level"""
        publisher = self.safe_get(listing, 'publisher', {})
        if isinstance(publisher, dict):
            partner_type = publisher.get('type', '')
            if 'ORACLE' in str(partner_type).upper():
                return 'Oracle'
            elif self.safe_get(listing, 'oracle-validated'):
                return 'Oracle Validated'
        
        return 'ISV Partner'
    
    def generate_gov_sales_notes(self, listing, regions):
        """Generate government sales notes"""
        notes = []
        
        if regions.get('us_gov_east') or regions.get('us_gov_west'):
            notes.append('US Gov Cloud ready')
        
        if any(k.startswith('us_dod') for k in regions):
            notes.append('DoD authorized')
        
        if regions.get('uk_gov'):
            notes.append('UK Gov compatible')
        
        fedramp = self.determine_fedramp_status(listing)
        if fedramp != 'Not Specified':
            notes.append(fedramp)
        
        return '; '.join(notes) if notes else 'Commercial only'
    
    def extract_key_features(self, listing):
        """Extract key features"""
        description = self.safe_get(listing, 'long-description', '')
        if not description:
            description = self.safe_get(listing, 'short-description', '')
        
        # Simple feature extraction - look for bullet points or key phrases
        features = []
        
        # Common feature patterns
        feature_keywords = ['provides', 'enables', 'includes', 'features', 'supports']
        sentences = str(description).split('.')
        
        for sentence in sentences[:3]:  # First 3 sentences often contain key features
            if any(keyword in sentence.lower() for keyword in feature_keywords):
                features.append(self.clean_text(sentence, 50))
        
        return '; '.join(features) if features else 'See product description'
    
    def estimate_implementation_timeline(self, listing):
        """Estimate implementation timeline"""
        complexity = self.assess_integration_complexity(listing)
        package_type = str(self.safe_get(listing, 'package-type', '')).upper()
        
        if package_type == 'IMAGE' and complexity == 'Low':
            return 'Same day'
        elif complexity == 'Low':
            return '1-3 days'
        elif complexity == 'Medium':
            return '1-2 weeks'
        else:
            return '2-4 weeks'
    
    def get_listing_text_content(self, listing):
        """Get all text content from listing for analysis"""
        text_parts = [
            str(self.safe_get(listing, 'name', '')),
            str(self.safe_get(listing, 'short-description', '')),
            str(self.safe_get(listing, 'long-description', '')),
            str(self.safe_get(listing, 'tags', [])),
            str(self.safe_get(listing, 'keywords', []))
        ]
        return ' '.join(text_parts).lower()
    
    def export_to_sales_csv(self, filename='oracle_marketplace_sales_catalog.csv'):
        """Export to sales-focused CSV"""
        sales_data = self.process_to_sales_csv()
        
        if not sales_data:
            print("❌ No data to export")
            return
        
        print(f"\nExporting to sales-focused CSV...")
        
        try:
            # Create DataFrame
            df = pd.DataFrame(sales_data)
            
            # Sort by Sales Priority (descending)
            df['Sales_Priority_Numeric'] = pd.to_numeric(df['Sales_Priority'], errors='coerce')
            df = df.sort_values('Sales_Priority_Numeric', ascending=False)
            df = df.drop('Sales_Priority_Numeric', axis=1)
            
            # Export to CSV
            df.to_csv(filename, index=False, encoding='utf-8')
            
            print(f"✅ Sales catalog exported to: {filename}")
            print(f"📊 Total products: {len(df)}")
            print(f"🏛️ Government products: {len(df[df['US_Gov_Available'] == 'Yes'])}")
            print(f"🎖️ DoD products: {len(df[df['US_DoD_Available'] == 'Yes'])}")
            print(f"🇬🇧 UK Gov products: {len(df[df['UK_Gov_Available'] == 'Yes'])}")
            
            # Also create a summary report
            self.create_sales_summary_report(df)
            
        except Exception as e:
            print(f"❌ Error exporting to CSV: {e}")
    
    def create_sales_summary_report(self, df):
        """Create a sales summary report"""
        print("\nGenerating sales summary report...")
        
        summary = {
            'Total Products': len(df),
            'By Region': {
                'Commercial Only': len(df[(df['US_Gov_Available'] == 'No') & 
                                        (df['US_DoD_Available'] == 'No') & 
                                        (df['UK_Gov_Available'] == 'No')]),
                'US Government': len(df[df['US_Gov_Available'] == 'Yes']),
                'US DoD': len(df[df['US_DoD_Available'] == 'Yes']),
                'UK Government': len(df[df['UK_Gov_Available'] == 'Yes'])
            },
            'By Priority': df['Sales_Priority'].value_counts().to_dict(),
            'By Category': df['Category'].value_counts().head(10).to_dict(),
            'By Pricing Model': df['Pricing_Model'].value_counts().to_dict(),
            'FedRAMP Products': len(df[~df['FedRAMP_Status'].str.contains('Not Specified')]),
            'Top Publishers': df['Publisher'].value_counts().head(10).to_dict()
        }
        
        # Write summary to file
        with open('oracle_marketplace_sales_summary.txt', 'w') as f:
            f.write("Oracle Cloud Marketplace Sales Summary\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
            
            for key, value in summary.items():
                f.write(f"{key}:\n")
                if isinstance(value, dict):
                    for k, v in value.items():
                        f.write(f"  - {k}: {v}\n")
                else:
                    f.write(f"  {value}\n")
                f.write("\n")
        
        print("✅ Sales summary report created: oracle_marketplace_sales_summary.txt")

def main():
    """Main execution function"""
    print("🚀 Oracle Cloud Marketplace Sales Processor")
    print("Processing all regions for sales team")
    print("=" * 50)
    
    processor = OCIMarketplaceSalesProcessor()
    
    try:
        # Load data from all regions
        total_loaded = processor.load_all_regional_data()
        
        if total_loaded == 0:
            print("\n❌ No marketplace data found in any region.")
            print("\n🔧 Troubleshooting steps:")
            print("   1. Run extraction script: ./extract_marketplace_all_regions.sh")
            print("   2. Check OCI CLI access to government regions")
            return
        
        # Consolidate unique listings
        unique_count = processor.consolidate_unique_listings()
        
        # Export to sales CSV
        processor.export_to_sales_csv('oracle_marketplace_sales_catalog.csv')
        
        print(f"\n🎉 Processing Complete!")
        print(f"📄 Main file: oracle_marketplace_sales_catalog.csv")
        print(f"📊 Summary: oracle_marketplace_sales_summary.txt")
        print(f"\n✅ Ready for Confluence dashboard integration!")
        
    except Exception as e:
        print(f"\n❌ Error during processing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()