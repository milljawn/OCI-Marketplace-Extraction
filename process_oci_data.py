#!/usr/bin/env python3
"""
OCI Marketplace Data Processor - Government Bypass Version
Skips government region files and focuses on commercial marketplace data
"""

import json
import pandas as pd
import os
from datetime import datetime
import re

class OCIMarketplaceProcessor:
    def __init__(self, data_dir="marketplace_data"):
        self.data_dir = data_dir
        self.listings_data = []
        
    def safe_load_json(self, filepath):
        """Safely load JSON file with error handling"""
        if not os.path.exists(filepath):
            print(f"⚠️  File not found: {filepath}")
            return {}
        
        if os.path.getsize(filepath) == 0:
            print(f"⚠️  File is empty (skipping): {filepath}")
            return {}
        
        try:
            with open(filepath, 'r') as f:
                content = f.read().strip()
                if not content:
                    print(f"⚠️  File has no content (skipping): {filepath}")
                    return {}
                
                data = json.loads(content)
                print(f"✅ Successfully loaded: {filepath}")
                return data
                
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error in {filepath}: {e}")
            return {}
        except Exception as e:
            print(f"❌ Error loading {filepath}: {e}")
            return {}
    
    def load_oci_data(self):
        """Load OCI CLI data, bypassing government files"""
        print("Loading OCI CLI data (skipping government regions)...")
        
        # Try main listings file first
        main_file = os.path.join(self.data_dir, "all_listings.json")
        main_data = self.safe_load_json(main_file)
        
        if main_data and 'data' in main_data:
            self.listings_data = main_data['data']
            print(f"✓ Loaded {len(self.listings_data)} main listings")
        else:
            print("⚠️  Main listings file empty/corrupted, loading from categories...")
            self.load_from_category_files()
        
        # Load detailed data and merge (optional)
        detailed_file = os.path.join(self.data_dir, "listings_detailed.json")
        detailed_data = self.safe_load_json(detailed_file)
        
        if detailed_data and 'data' in detailed_data:
            self.merge_detailed_data(detailed_data['data'])
            print(f"✓ Merged detailed data")
        else:
            print("⚠️  No detailed data available (proceeding without it)")
        
        # Skip government data loading entirely
        print("🏛️  Skipping government regions (access not available)")
        
        # Add empty government availability to all listings
        for listing in self.listings_data:
            listing['government_availability'] = {
                'us_gov': False,
                'us_gov_west': False,
                'uk_gov': False
            }
        
        return len(self.listings_data)
    
    def load_from_category_files(self):
        """Load from category files as backup"""
        print("🔄 Loading from category files as backup...")
        
        categories = ["analytics", "compute", "databases", "developer-tools", 
                     "integration", "iot", "machine-learning", "monitoring", 
                     "networking", "security", "storage", "business-applications"]
        
        all_listings = []
        seen_ids = set()
        
        for category in categories:
            cat_file = os.path.join(self.data_dir, f"category_{category}.json")
            cat_data = self.safe_load_json(cat_file)
            
            if cat_data and 'data' in cat_data:
                for listing in cat_data['data']:
                    listing_id = listing.get('id')
                    if listing_id and listing_id not in seen_ids:
                        all_listings.append(listing)
                        seen_ids.add(listing_id)
                        
                print(f"   ✓ Found {len(cat_data['data'])} listings in {category}")
        
        if all_listings:
            self.listings_data = all_listings
            print(f"✅ Recovered {len(all_listings)} listings from category files")
        else:
            print("❌ Could not load data from any source")
    
    def merge_detailed_data(self, detailed_data):
        """Merge detailed search data with main listings"""
        if not detailed_data:
            return
            
        detailed_dict = {item.get('id'): item for item in detailed_data if item.get('id')}
        
        for listing in self.listings_data:
            listing_id = listing.get('id')
            if listing_id in detailed_dict:
                detailed_item = detailed_dict[listing_id]
                for key, value in detailed_item.items():
                    if key not in listing or listing[key] is None:
                        listing[key] = value
    
    def process_to_spreadsheet_format(self):
        """Convert OCI data to spreadsheet format"""
        print("Processing data to spreadsheet format...")
        
        if not self.listings_data:
            print("❌ No listings data to process")
            return []
        
        processed_data = []
        
        for i, listing in enumerate(self.listings_data):
            try:
                row = {
                    # Basic Information
                    'listing_id': self.safe_get(listing, 'id', '').replace('ocid1.marketplace.listing.', ''),
                    'listing_ocid': self.safe_get(listing, 'id'),
                    'product_name': self.safe_get(listing, 'name'),
                    'publisher': self.get_publisher_name(listing),
                    'publisher_type': self.safe_get(listing, ['publisher', 'type']),
                    'category': self.get_category(listing),
                    'subcategory': self.get_subcategory(listing),
                    'short_description': self.safe_get(listing, 'short-description'),
                    'long_description': self.safe_get(listing, 'long-description'),
                    
                    # Technical Details
                    'listing_type': self.safe_get(listing, 'listing-type'),
                    'package_type': self.safe_get(listing, 'package-type'),
                    'operating_systems': self.format_list(self.safe_get(listing, 'supported-operating-systems')),
                    'version': self.get_version(listing),
                    'version_date': self.get_version_date(listing),
                    
                    # Pricing Information
                    'pricing_model': self.safe_get(listing, ['pricing', 'type']),
                    'pricing_currency': self.safe_get(listing, ['pricing', 'currency']),
                    'price_per_hour': self.get_pricing(listing, 'HOUR'),
                    'price_per_month': self.get_pricing(listing, 'MONTH'),
                    'price_per_year': self.get_pricing(listing, 'YEAR'),
                    'free_trial_available': self.safe_get(listing, 'free-trial-available'),
                    
                    # Instance and Requirements
                    'supported_shapes': self.format_list(self.safe_get(listing, 'supported-compute-shapes')),
                    'minimum_shape': self.get_minimum_shape(listing),
                    'system_requirements': self.safe_get(listing, 'system-requirements'),
                    'usage_information': self.safe_get(listing, 'usage-information'),
                    
                    # Documentation and Support
                    'documentation_url': self.safe_get(listing, 'documentation-url'),
                    'support_url': self.safe_get(listing, 'support-url'),
                    'video_url': self.safe_get(listing, 'video-url'),
                    'icon_url': self.get_icon_url(listing),
                    'banner_url': self.safe_get(listing, ['banner', 'url']),
                    
                    # Metadata
                    'tags': self.format_list(self.safe_get(listing, 'tags')),
                    'keywords': self.format_list(self.safe_get(listing, 'keywords')),
                    'time_created': self.safe_get(listing, 'time-created'),
                    'time_updated': self.safe_get(listing, 'time-updated'),
                    'regions_available': self.format_list(self.safe_get(listing, 'regions')),
                    'compatible_architectures': self.format_list(self.safe_get(listing, 'compatible-architectures')),
                    
                    # Legal and Compliance
                    'eula_required': self.safe_get(listing, 'eula-required'),
                    'agreement_type': self.safe_get(listing, ['agreement', 'type']),
                    'third_party_licenses': self.format_list(self.safe_get(listing, 'third-party-licenses')),
                    
                    # Government Compliance Analysis (Content-Based)
                    'us_government_ready': self.analyze_us_gov_readiness_content(listing),
                    'us_government_available': False,  # No access to gov regions
                    'us_gov_west_available': False,   # No access to gov regions
                    'us_dod_ready': self.analyze_dod_readiness_content(listing),
                    'dod_impact_level': self.determine_impact_level_content(listing),
                    'fedramp_indicators': self.find_fedramp_indicators(listing),
                    'cmmc_indicators': self.find_cmmc_indicators(listing),
                    'uk_government_ready': self.analyze_uk_gov_readiness_content(listing),
                    'uk_government_available': False,  # No access to gov regions
                    'export_control_status': self.analyze_export_control(listing),
                    
                    # Business Intelligence
                    'sales_priority': self.calculate_sales_priority(listing),
                    'market_category': self.categorize_market_segment(listing),
                    'deployment_complexity': self.assess_deployment_complexity(listing),
                    'enterprise_readiness': self.assess_enterprise_readiness(listing),
                    
                    # Additional Analysis
                    'security_focused': self.is_security_focused(listing),
                    'ai_ml_related': self.is_ai_ml_related(listing),
                    'database_related': self.is_database_related(listing),
                    'networking_related': self.is_networking_related(listing),
                    'compliance_certifications': self.extract_compliance_certifications(listing),
                    
                    # Oracle Specific
                    'oracle_validated': self.safe_get(listing, 'oracle-validated'),
                    'oracle_recommended': self.safe_get(listing, 'oracle-recommended'),
                    'oracle_managed': self.safe_get(listing, 'oracle-managed'),
                    
                    # URLs and References
                    'marketplace_url': f"https://cloudmarketplace.oracle.com/marketplace/en_US/listing/{self.safe_get(listing, 'id', '').replace('ocid1.marketplace.listing.', '')}",
                    'listing_url': self.safe_get(listing, 'listing-url'),
                    
                    # Government Access Notes
                    'government_notes': 'Analysis based on content only - no government region access'
                }
                
                processed_data.append(row)
                
                if (i + 1) % 50 == 0:
                    print(f"   Processed {i + 1}/{len(self.listings_data)} listings...")
                
            except Exception as e:
                print(f"⚠️  Error processing listing {i+1}: {e}")
                continue
        
        print(f"✅ Successfully processed {len(processed_data)} listings")
        return processed_data
    
    def safe_get(self, data, keys, default=None):
        """Safely extract nested data"""
        if isinstance(keys, str):
            return data.get(keys, default)
        
        current = data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current if current is not None else default
    
    def get_publisher_name(self, listing):
        """Extract publisher name"""
        publisher = self.safe_get(listing, 'publisher', {})
        if isinstance(publisher, dict):
            return publisher.get('name') or publisher.get('display-name')
        return str(publisher) if publisher else None
    
    def get_category(self, listing):
        """Get primary category"""
        categories = self.safe_get(listing, 'categories') or self.safe_get(listing, 'category-facet')
        if categories and isinstance(categories, list) and len(categories) > 0:
            return categories[0]
        return categories if isinstance(categories, str) else None
    
    def get_subcategory(self, listing):
        """Get subcategory"""
        categories = self.safe_get(listing, 'categories') or self.safe_get(listing, 'category-facet')
        if categories and isinstance(categories, list) and len(categories) > 1:
            return categories[1]
        subcategories = self.safe_get(listing, 'subcategories') or self.safe_get(listing, 'subcategory-facet')
        if subcategories and isinstance(subcategories, list) and len(subcategories) > 0:
            return subcategories[0]
        return None
    
    def get_version(self, listing):
        """Extract version information"""
        version = self.safe_get(listing, 'version')
        if version:
            return version
        
        packages = self.safe_get(listing, 'packages', [])
        if packages and len(packages) > 0:
            return packages[0].get('version')
        
        return None
    
    def get_version_date(self, listing):
        """Extract version date"""
        packages = self.safe_get(listing, 'packages', [])
        if packages and len(packages) > 0:
            return packages[0].get('time-created')
        return self.safe_get(listing, 'time-updated')
    
    def get_pricing(self, listing, time_unit):
        """Extract pricing for specific time unit"""
        pricing = self.safe_get(listing, 'pricing', {})
        if not pricing:
            return None
            
        pricing_type = pricing.get('type')
        if pricing_type in ['FREE', 'BYOL']:
            return pricing_type
        
        rate = pricing.get('rate')
        if rate and pricing.get('unit'):
            unit = str(pricing.get('unit')).upper()
            if time_unit in unit:
                currency = pricing.get('currency', 'USD')
                return f"{rate} {currency}"
        
        return str(rate) if rate else None
    
    def get_minimum_shape(self, listing):
        """Determine minimum compute shape"""
        shapes = self.safe_get(listing, 'supported-compute-shapes', [])
        if not shapes:
            return None
            
        try:
            shapes_sorted = sorted(shapes, key=lambda x: (
                int(re.search(r'(\d+)', str(x)).group(1)) if re.search(r'(\d+)', str(x)) else 0
            ))
            return shapes_sorted[0] if shapes_sorted else None
        except:
            return shapes[0] if shapes else None
    
    def get_icon_url(self, listing):
        """Extract icon URL"""
        icon = self.safe_get(listing, 'icon')
        if isinstance(icon, dict):
            return icon.get('url')
        return icon if isinstance(icon, str) else None
    
    def format_list(self, list_data):
        """Format list data for spreadsheet"""
        if not list_data:
            return None
        if isinstance(list_data, list):
            return '; '.join(str(item) for item in list_data if item is not None)
        return str(list_data)
    
    def get_listing_text_content(self, listing):
        """Get all text content from listing for analysis"""
        text_parts = [
            str(self.safe_get(listing, 'name', '')),
            str(self.safe_get(listing, 'short-description', '')),
            str(self.safe_get(listing, 'long-description', '')),
            str(self.safe_get(listing, 'tags', [])),
        ]
        return ' '.join(text_parts).lower()
    
    def analyze_us_gov_readiness_content(self, listing):
        """Analyze US Government readiness based on content only"""
        text_content = self.get_listing_text_content(listing)
        
        # High confidence keywords
        high_confidence = ['fedramp', 'federal', 'government certified']
        if any(keyword in text_content for keyword in high_confidence):
            return 'READY'
        
        # Medium confidence keywords
        gov_keywords = ['government', 'fisma', 'gsa', 'federal compliance']
        if any(keyword in text_content for keyword in gov_keywords):
            return 'POTENTIAL'
        
        return 'UNKNOWN'
    
    def analyze_dod_readiness_content(self, listing):
        """Analyze DoD readiness based on content only"""
        text_content = self.get_listing_text_content(listing)
        
        # High confidence keywords
        high_confidence = ['dod', 'defense', 'cmmc', 'scca']
        if any(keyword in text_content for keyword in high_confidence):
            return 'READY'
        
        # Medium confidence keywords
        dod_keywords = ['military', 'il2', 'il4', 'il5', 'impact level']
        if any(keyword in text_content for keyword in dod_keywords):
            return 'POTENTIAL'
        
        return 'UNKNOWN'
    
    def determine_impact_level_content(self, listing):
        """Determine supported DoD Impact Levels from content"""
        text_content = self.get_listing_text_content(listing)
        
        levels = []
        if 'il2' in text_content or 'impact level 2' in text_content:
            levels.append('IL2')
        if 'il4' in text_content or 'impact level 4' in text_content:
            levels.append('IL4')
        if 'il5' in text_content or 'impact level 5' in text_content:
            levels.append('IL5')
        
        return '; '.join(levels) if levels else None
    
    def analyze_uk_gov_readiness_content(self, listing):
        """Analyze UK Government readiness based on content only"""
        text_content = self.get_listing_text_content(listing)
        
        uk_keywords = ['uk government', 'ncsc', 'official sensitive', 'security clearance', 'gov.uk']
        if any(keyword in text_content for keyword in uk_keywords):
            return 'POTENTIAL'
        
        return 'UNKNOWN'
    
    def find_fedramp_indicators(self, listing):
        """Find FedRAMP compliance indicators"""
        text_content = self.get_listing_text_content(listing)
        return 'fedramp' in text_content or 'fed ramp' in text_content
    
    def find_cmmc_indicators(self, listing):
        """Find CMMC compliance indicators"""
        text_content = self.get_listing_text_content(listing)
        return 'cmmc' in text_content or 'cybersecurity maturity model' in text_content
    
    def analyze_export_control(self, listing):
        """Analyze export control status"""
        text_content = self.get_listing_text_content(listing)
        export_keywords = ['itar', 'ear', 'export control', 'export restriction']
        if any(keyword in text_content for keyword in export_keywords):
            return 'RESTRICTED'
        return 'UNRESTRICTED'
    
    def calculate_sales_priority(self, listing):
        """Calculate sales priority score"""
        score = 0
        
        # High-value publishers
        publisher = str(self.get_publisher_name(listing) or '').lower()
        high_value_publishers = ['microsoft', 'vmware', 'palo alto', 'fortinet', 'red hat', 'citrix']
        if any(pub in publisher for pub in high_value_publishers):
            score += 3
        
        # Popular categories
        category = str(self.get_category(listing) or '').lower()
        popular_categories = ['security', 'networking', 'database', 'analytics']
        if any(cat in category for cat in popular_categories):
            score += 2
        
        # Government readiness
        if self.analyze_us_gov_readiness_content(listing) in ['READY', 'POTENTIAL']:
            score += 2
        
        # Pricing model
        if self.safe_get(listing, ['pricing', 'type']) == 'PAID':
            score += 1
        
        if score >= 5:
            return 'HIGH'
        elif score >= 3:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def categorize_market_segment(self, listing):
        """Categorize market segment"""
        category = str(self.get_category(listing) or '').lower()
        name = str(self.safe_get(listing, 'name', '')).lower()
        
        if any(term in category + name for term in ['security', 'firewall', 'vpn']):
            return 'Security'
        elif any(term in category + name for term in ['database', 'sql', 'nosql']):
            return 'Database'
        elif any(term in category + name for term in ['analytics', 'bi', 'reporting']):
            return 'Analytics'
        elif any(term in category + name for term in ['network', 'load balancer', 'dns']):
            return 'Networking'
        elif any(term in category + name for term in ['ai', 'ml', 'machine learning']):
            return 'AI/ML'
        else:
            return 'Other'
    
    def assess_deployment_complexity(self, listing):
        """Assess deployment complexity"""
        package_type = str(self.safe_get(listing, 'package-type', '')).upper()
        
        if package_type == 'IMAGE':
            return 'LOW'
        elif package_type in ['STACK', 'TERRAFORM']:
            return 'MEDIUM'
        elif package_type in ['CONTAINER', 'HELM']:
            return 'MEDIUM'
        else:
            return 'UNKNOWN'
    
    def assess_enterprise_readiness(self, listing):
        """Assess enterprise readiness"""
        score = 0
        
        if self.safe_get(listing, 'support-url'):
            score += 1
        if self.safe_get(listing, 'documentation-url'):
            score += 1
        
        pricing_type = self.safe_get(listing, ['pricing', 'type'])
        if pricing_type in ['PAID', 'BYOL']:
            score += 1
        
        if self.safe_get(listing, 'oracle-validated'):
            score += 2
        
        if score >= 4:
            return 'HIGH'
        elif score >= 2:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def is_security_focused(self, listing):
        """Check if security-focused"""
        text = self.get_listing_text_content(listing)
        security_terms = ['security', 'firewall', 'vpn', 'encryption', 'auth', 'siem', 'vulnerability']
        return any(term in text for term in security_terms)
    
    def is_ai_ml_related(self, listing):
        """Check if AI/ML related"""
        text = self.get_listing_text_content(listing)
        ai_terms = ['ai', 'artificial intelligence', 'machine learning', 'ml', 'deep learning', 'neural']
        return any(term in text for term in ai_terms)
    
    def is_database_related(self, listing):
        """Check if database related"""
        text = self.get_listing_text_content(listing)
        db_terms = ['database', 'sql', 'nosql', 'mongodb', 'mysql', 'postgres', 'oracle']
        return any(term in text for term in db_terms)
    
    def is_networking_related(self, listing):
        """Check if networking related"""
        text = self.get_listing_text_content(listing)
        net_terms = ['network', 'load balancer', 'dns', 'cdn', 'proxy', 'gateway']
        return any(term in text for term in net_terms)
    
    def extract_compliance_certifications(self, listing):
        """Extract compliance certifications mentioned"""
        text = self.get_listing_text_content(listing)
        
        certs = []
        cert_keywords = {
            'SOC 2': 'soc 2',
            'ISO 27001': 'iso 27001',
            'PCI DSS': 'pci dss',
            'HIPAA': 'hipaa',
            'GDPR': 'gdpr',
            'FedRAMP': 'fedramp',
            'FISMA': 'fisma',
            'CMMC': 'cmmc'
        }
        
        for cert_name, keyword in cert_keywords.items():
            if keyword in text:
                certs.append(cert_name)
        
        return '; '.join(certs) if certs else None
    
    def export_to_excel(self, filename='oracle_marketplace_commercial_catalog.xlsx'):
        """Export processed data to Excel"""
        processed_data = self.process_to_spreadsheet_format()
        
        if not processed_data:
            print("❌ No data to export")
            return
        
        print(f"Exporting {len(processed_data)} listings to Excel...")
        
        try:
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # Main catalog
                df_catalog = pd.DataFrame(processed_data)
                df_catalog.to_excel(writer, sheet_name='Marketplace Catalog', index=False)
                
                # Government compliance summary (content-based)
                gov_data = []
                for item in processed_data:
                    gov_item = {
                        'Listing ID': item['listing_id'],
                        'Product Name': item['product_name'],
                        'Publisher': item['publisher'],
                        'Category': item['category'],
                        'US Gov Ready (Content)': item['us_government_ready'],
                        'US DoD Ready (Content)': item['us_dod_ready'],
                        'DoD Impact Level': item['dod_impact_level'],
                        'UK Gov Ready (Content)': item['uk_government_ready'],
                        'FedRAMP Mentioned': '✓' if item['fedramp_indicators'] else '✗',
                        'CMMC Mentioned': '✓' if item['cmmc_indicators'] else '✗',
                        'Export Control': item['export_control_status'],
                        'Sales Priority': item['sales_priority'],
                        'Compliance Certs': item['compliance_certifications'],
                        'Marketplace URL': item['marketplace_url'],
                        'Notes': 'Content analysis only - no gov region access'
                    }
                    gov_data.append(gov_item)
                
                df_gov = pd.DataFrame(gov_data)
                df_gov.to_excel(writer, sheet_name='Government Analysis', index=False)
                
                # Summary statistics
                summary_stats = self.generate_summary_stats(processed_data)
                df_summary = pd.DataFrame(summary_stats)
                df_summary.to_excel(writer, sheet_name='Summary Statistics', index=False)
            
            print(f"✅ Complete marketplace catalog exported to: {filename}")
            print(f"   📊 {len(processed_data)} total listings")
            print(f"   🏛️ Government compliance analysis (content-based)")
            print(f"   📈 Sales prioritization completed")
            print(f"   📝 Note: Government region data unavailable (normal for most users)")
            
        except Exception as e:
            print(f"❌ Error exporting to Excel: {e}")
            # Fallback to CSV
            try:
                df_catalog = pd.DataFrame(processed_data)
                csv_filename = filename.replace('.xlsx', '.csv')
                df_catalog.to_csv(csv_filename, index=False)
                print(f"💾 Fallback: Data saved to {csv_filename}")
            except Exception as csv_error:
                print(f"❌ CSV fallback also failed: {csv_error}")
    
    def generate_summary_stats(self, processed_data):
        """Generate summary statistics"""
        df = pd.DataFrame(processed_data)
        stats = []
        
        # Basic counts
        stats.append({'Metric': 'Total Commercial Listings', 'Value': len(df), 'Category': 'Overview'})
        
        # Government readiness (content-based)
        us_gov_ready = sum(1 for x in df['us_government_ready'] if x == 'READY')
        us_gov_potential = sum(1 for x in df['us_government_ready'] if x == 'POTENTIAL')
        stats.append({'Metric': 'US Gov Ready (Content)', 'Value': us_gov_ready, 'Category': 'Government'})
        stats.append({'Metric': 'US Gov Potential (Content)', 'Value': us_gov_potential, 'Category': 'Government'})
        
        dod_ready = sum(1 for x in df['us_dod_ready'] if x == 'READY')
        dod_potential = sum(1 for x in df['us_dod_ready'] if x == 'POTENTIAL')
        stats.append({'Metric': 'US DoD Ready (Content)', 'Value': dod_ready, 'Category': 'Government'})
        stats.append({'Metric': 'US DoD Potential (Content)', 'Value': dod_potential, 'Category': 'Government'})
        
        # Compliance mentions
        fedramp_count = sum(1 for x in df['fedramp_indicators'] if x)
        cmmc_count = sum(1 for x in df['cmmc_indicators'] if x)
        stats.append({'Metric': 'FedRAMP Mentioned', 'Value': fedramp_count, 'Category': 'Compliance'})
        stats.append({'Metric': 'CMMC Mentioned', 'Value': cmmc_count, 'Category': 'Compliance'})
        
        # Sales priority
        priority_counts = df['sales_priority'].value_counts()
        for priority, count in priority_counts.items():
            if priority:
                stats.append({'Metric': f'Sales Priority: {priority}', 'Value': count, 'Category': 'Sales'})
        
        # Technology categories
        security_count = sum(1 for x in df['security_focused'] if x)
        ai_count = sum(1 for x in df['ai_ml_related'] if x)
        db_count = sum(1 for x in df['database_related'] if x)
        net_count = sum(1 for x in df['networking_related'] if x)
        
        stats.append({'Metric': 'Security Solutions', 'Value': security_count, 'Category': 'Technology'})
        stats.append({'Metric': 'AI/ML Solutions', 'Value': ai_count, 'Category': 'Technology'})
        stats.append({'Metric': 'Database Solutions', 'Value': db_count, 'Category': 'Technology'})
        stats.append({'Metric': 'Networking Solutions', 'Value': net_count, 'Category': 'Technology'})
        
        # Top publishers
        top_publishers = df['publisher'].value_counts().head(10)
        for publisher, count in top_publishers.items():
            if publisher and str(publisher) != 'nan' and str(publisher) != 'None':
                stats.append({'Metric': f'Publisher: {publisher}', 'Value': count, 'Category': 'Publishers'})
        
        return stats

def main():
    """Main execution function - Government Bypass Version"""
    print("🚀 OCI Marketplace Data Processor (Government Bypass Version)")
    print("Processes commercial marketplace data, skips government regions")
    print("=" * 65)
    
    processor = OCIMarketplaceProcessor()
    
    try:
        # Load OCI data (skipping government files)
        listings_count = processor.load_oci_data()
        
        if listings_count == 0:
            print("\n❌ No commercial marketplace data found.")
            print("\n🔧 Troubleshooting steps:")
            print("   1. Check if extraction ran: ls -la marketplace_data/")
            print("   2. Re-run extraction: ./extract_marketplace_data.sh")
            print("   3. Check OCI CLI: oci iam user list")
            return
        
        print(f"\n✅ Successfully loaded {listings_count} commercial marketplace listings")
        
        # Export to Excel
        processor.export_to_excel('oracle_marketplace_commercial_catalog.xlsx')
        
        print(f"\n🎉 Processing Complete!")
        print(f"📄 File: oracle_marketplace_commercial_catalog.xlsx")
        print(f"📊 Commercial listings: {listings_count}")
        print(f"🏛️ Government analysis: Content-based (no region access required)")
        print(f"📈 Sales prioritization: Completed")
        print(f"📝 Note: Government region files skipped (normal for most Oracle employees)")
        
    except Exception as e:
        print(f"\n❌ Error during processing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
