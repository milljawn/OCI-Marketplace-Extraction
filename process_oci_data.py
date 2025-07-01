#!/usr/bin/env python3
"""
OCI Marketplace Data Processor
Converts OCI CLI JSON output to comprehensive Excel spreadsheet
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
        self.government_analysis = []
        
    def load_oci_data(self):
        """Load all OCI CLI JSON files"""
        print("Loading OCI CLI data files...")
        
        # Load main listings
        main_file = os.path.join(self.data_dir, "all_listings.json")
        if os.path.exists(main_file):
            with open(main_file, 'r') as f:
                main_data = json.load(f)
                self.listings_data = main_data.get('data', [])
                print(f"✓ Loaded {len(self.listings_data)} main listings")
        
        # Load detailed data and merge
        detailed_file = os.path.join(self.data_dir, "listings_detailed.json")
        if os.path.exists(detailed_file):
            with open(detailed_file, 'r') as f:
                detailed_data = json.load(f)
                self.merge_detailed_data(detailed_data.get('data', []))
                print(f"✓ Merged detailed data")
        
        # Load government region data
        self.load_government_data()
        
        return len(self.listings_data)
    
    def merge_detailed_data(self, detailed_data):
        """Merge detailed search data with main listings"""
        detailed_dict = {item.get('id'): item for item in detailed_data}
        
        for listing in self.listings_data:
            listing_id = listing.get('id')
            if listing_id in detailed_dict:
                # Merge additional fields from detailed data
                detailed_item = detailed_dict[listing_id]
                for key, value in detailed_item.items():
                    if key not in listing or listing[key] is None:
                        listing[key] = value
    
    def load_government_data(self):
        """Load government region availability data"""
        gov_files = {
            'us_gov': 'us_gov_listings.json',
            'us_gov_west': 'us_gov_west_listings.json',
            'uk_gov': 'uk_gov_listings.json'
        }
        
        gov_availability = {}
        
        for region, filename in gov_files.items():
            filepath = os.path.join(self.data_dir, filename)
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                        gov_listings = data.get('data', [])
                        gov_ids = {item.get('id') for item in gov_listings}
                        gov_availability[region] = gov_ids
                        print(f"✓ Loaded {len(gov_ids)} listings for {region}")
                except:
                    print(f"⚠ Could not load {filename} (region may not be accessible)")
        
        # Add government availability to main data
        for listing in self.listings_data:
            listing_id = listing.get('id')
            listing['government_availability'] = {
                region: listing_id in ids 
                for region, ids in gov_availability.items()
            }
    
    def process_to_spreadsheet_format(self):
        """Convert OCI data to comprehensive spreadsheet format"""
        print("Processing data to spreadsheet format...")
        
        processed_data = []
        
        for listing in self.listings_data:
            # Extract core information
            row = {
                # Basic Information
                'listing_id': listing.get('id', '').replace('ocid1.marketplace.listing.', ''),
                'listing_ocid': listing.get('id'),
                'product_name': listing.get('name'),
                'publisher': self.get_publisher_name(listing),
                'publisher_type': listing.get('publisher', {}).get('type'),
                'category': self.get_category(listing),
                'subcategory': self.get_subcategory(listing),
                'short_description': listing.get('short-description'),
                'long_description': listing.get('long-description'),
                
                # Technical Details
                'listing_type': listing.get('listing-type'),
                'package_type': listing.get('package-type'),
                'operating_systems': self.format_list(listing.get('supported-operating-systems')),
                'version': self.get_version(listing),
                'version_date': self.get_version_date(listing),
                
                # Pricing Information
                'pricing_model': listing.get('pricing', {}).get('type'),
                'pricing_currency': listing.get('pricing', {}).get('currency'),
                'price_per_hour': self.get_pricing(listing, 'HOUR'),
                'price_per_month': self.get_pricing(listing, 'MONTH'),
                'price_per_year': self.get_pricing(listing, 'YEAR'),
                'free_trial_available': listing.get('free-trial-available'),
                
                # Instance and Requirements
                'supported_shapes': self.format_list(listing.get('supported-compute-shapes')),
                'minimum_shape': self.get_minimum_shape(listing),
                'system_requirements': listing.get('system-requirements'),
                'usage_information': listing.get('usage-information'),
                
                # Documentation and Support
                'documentation_url': listing.get('documentation-url'),
                'support_url': listing.get('support-url'),
                'video_url': listing.get('video-url'),
                'icon_url': self.get_icon_url(listing),
                'banner_url': listing.get('banner', {}).get('url'),
                
                # Metadata
                'tags': self.format_list(listing.get('tags')),
                'keywords': self.format_list(listing.get('keywords')),
                'time_created': listing.get('time-created'),
                'time_updated': listing.get('time-updated'),
                'regions_available': self.format_list(listing.get('regions')),
                'compatible_architectures': self.format_list(listing.get('compatible-architectures')),
                
                # Legal and Compliance
                'eula_required': listing.get('eula-required'),
                'agreement_type': listing.get('agreement', {}).get('type'),
                'third_party_licenses': self.format_list(listing.get('third-party-licenses')),
                
                # Government Compliance Analysis
                'us_government_ready': self.analyze_us_gov_readiness(listing),
                'us_government_available': listing.get('government_availability', {}).get('us_gov', False),
                'us_gov_west_available': listing.get('government_availability', {}).get('us_gov_west', False),
                'us_dod_ready': self.analyze_dod_readiness(listing),
                'dod_impact_level': self.determine_impact_level(listing),
                'fedramp_indicators': self.find_fedramp_indicators(listing),
                'cmmc_indicators': self.find_cmmc_indicators(listing),
                'uk_government_ready': self.analyze_uk_gov_readiness(listing),
                'uk_government_available': listing.get('government_availability', {}).get('uk_gov', False),
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
                'oracle_validated': listing.get('oracle-validated'),
                'oracle_recommended': listing.get('oracle-recommended'),
                'oracle_managed': listing.get('oracle-managed'),
                
                # URLs and References
                'marketplace_url': f"https://cloudmarketplace.oracle.com/marketplace/en_US/listing/{listing.get('id', '').replace('ocid1.marketplace.listing.', '')}",
                'listing_url': listing.get('listing-url'),
            }
            
            processed_data.append(row)
        
        return processed_data
    
    def get_publisher_name(self, listing):
        """Extract publisher name"""
        publisher = listing.get('publisher', {})
        if isinstance(publisher, dict):
            return publisher.get('name') or publisher.get('display-name')
        return str(publisher) if publisher else None
    
    def get_category(self, listing):
        """Get primary category"""
        categories = listing.get('categories') or listing.get('category-facet')
        if categories and isinstance(categories, list) and len(categories) > 0:
            return categories[0]
        return categories if isinstance(categories, str) else None
    
    def get_subcategory(self, listing):
        """Get subcategory"""
        categories = listing.get('categories') or listing.get('category-facet')
        if categories and isinstance(categories, list) and len(categories) > 1:
            return categories[1]
        subcategories = listing.get('subcategories') or listing.get('subcategory-facet')
        if subcategories and isinstance(subcategories, list) and len(subcategories) > 0:
            return subcategories[0]
        return None
    
    def get_version(self, listing):
        """Extract version information"""
        version = listing.get('version')
        if version:
            return version
        
        # Try to extract from package versions
        packages = listing.get('packages', [])
        if packages and len(packages) > 0:
            return packages[0].get('version')
        
        return None
    
    def get_version_date(self, listing):
        """Extract version date"""
        packages = listing.get('packages', [])
        if packages and len(packages) > 0:
            return packages[0].get('time-created')
        return listing.get('time-updated')
    
    def get_pricing(self, listing, time_unit):
        """Extract pricing for specific time unit"""
        pricing = listing.get('pricing', {})
        if pricing.get('type') in ['FREE', 'BYOL']:
            return 'FREE' if pricing.get('type') == 'FREE' else 'BYOL'
        
        # Look for specific time unit pricing
        rate = pricing.get('rate')
        if rate and pricing.get('unit'):
            unit = pricing.get('unit').upper()
            if time_unit in unit:
                return f"{rate} {pricing.get('currency', 'USD')}"
        
        return rate if rate else None
    
    def get_minimum_shape(self, listing):
        """Determine minimum compute shape"""
        shapes = listing.get('supported-compute-shapes', [])
        if shapes:
            # Sort shapes by likely resource requirements (simple heuristic)
            shapes_sorted = sorted(shapes, key=lambda x: (
                int(re.search(r'(\d+)', x).group(1)) if re.search(r'(\d+)', x) else 0
            ))
            return shapes_sorted[0] if shapes_sorted else None
        return None
    
    def get_icon_url(self, listing):
        """Extract icon URL"""
        icon = listing.get('icon')
        if isinstance(icon, dict):
            return icon.get('url')
        return icon if isinstance(icon, str) else None
    
    def format_list(self, list_data):
        """Format list data for spreadsheet"""
        if not list_data:
            return None
        if isinstance(list_data, list):
            return '; '.join(str(item) for item in list_data)
        return str(list_data)
    
    def analyze_us_gov_readiness(self, listing):
        """Analyze US Government readiness"""
        # Check if available in government regions
        gov_available = listing.get('government_availability', {})
        if gov_available.get('us_gov') or gov_available.get('us_gov_west'):
            return 'READY'
        
        # Check for government keywords
        text_content = ' '.join([
            str(listing.get('name', '')),
            str(listing.get('short-description', '')),
            str(listing.get('long-description', '')),
            str(listing.get('tags', [])),
        ]).lower()
        
        gov_keywords = ['government', 'federal', 'fedramp', 'fisma', 'gsa']
        if any(keyword in text_content for keyword in gov_keywords):
            return 'POTENTIAL'
        
        return 'UNKNOWN'
    
    def analyze_dod_readiness(self, listing):
        """Analyze DoD readiness"""
        text_content = ' '.join([
            str(listing.get('name', '')),
            str(listing.get('short-description', '')),
            str(listing.get('long-description', '')),
        ]).lower()
        
        dod_keywords = ['dod', 'defense', 'military', 'cmmc', 'scca', 'il2', 'il4', 'il5']
        high_confidence = ['dod', 'defense', 'cmmc']
        
        if any(keyword in text_content for keyword in high_confidence):
            return 'READY'
        elif any(keyword in text_content for keyword in dod_keywords):
            return 'POTENTIAL'
        
        return 'UNKNOWN'
    
    def determine_impact_level(self, listing):
        """Determine supported DoD Impact Levels"""
        text_content = ' '.join([
            str(listing.get('name', '')),
            str(listing.get('short-description', '')),
            str(listing.get('long-description', '')),
        ]).lower()
        
        levels = []
        if 'il2' in text_content or 'impact level 2' in text_content:
            levels.append('IL2')
        if 'il4' in text_content or 'impact level 4' in text_content:
            levels.append('IL4')
        if 'il5' in text_content or 'impact level 5' in text_content:
            levels.append('IL5')
        
        return '; '.join(levels) if levels else None
    
    def find_fedramp_indicators(self, listing):
        """Find FedRAMP compliance indicators"""
        text_content = ' '.join([
            str(listing.get('name', '')),
            str(listing.get('short-description', '')),
            str(listing.get('long-description', '')),
        ]).lower()
        
        return 'fedramp' in text_content or 'fed ramp' in text_content
    
    def find_cmmc_indicators(self, listing):
        """Find CMMC compliance indicators"""
        text_content = ' '.join([
            str(listing.get('name', '')),
            str(listing.get('short-description', '')),
            str(listing.get('long-description', '')),
        ]).lower()
        
        return 'cmmc' in text_content or 'cybersecurity maturity model' in text_content
    
    def analyze_uk_gov_readiness(self, listing):
        """Analyze UK Government readiness"""
        if listing.get('government_availability', {}).get('uk_gov'):
            return 'READY'
        
        text_content = ' '.join([
            str(listing.get('name', '')),
            str(listing.get('short-description', '')),
            str(listing.get('long-description', '')),
        ]).lower()
        
        uk_keywords = ['uk government', 'ncsc', 'official sensitive', 'security clearance']
        if any(keyword in text_content for keyword in uk_keywords):
            return 'POTENTIAL'
        
        return 'UNKNOWN'
    
    def analyze_export_control(self, listing):
        """Analyze export control status"""
        text_content = ' '.join([
            str(listing.get('name', '')),
            str(listing.get('short-description', '')),
            str(listing.get('long-description', '')),
        ]).lower()
        
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
        if self.analyze_us_gov_readiness(listing) in ['READY', 'POTENTIAL']:
            score += 2
        
        # Pricing model (paid solutions often higher priority)
        if listing.get('pricing', {}).get('type') == 'PAID':
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
        name = str(listing.get('name', '')).lower()
        
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
        package_type = listing.get('package-type', '').upper()
        
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
        
        # Has support URL
        if listing.get('support-url'):
            score += 1
        
        # Has documentation
        if listing.get('documentation-url'):
            score += 1
        
        # Paid/BYOL (typically more enterprise-ready)
        pricing_type = listing.get('pricing', {}).get('type')
        if pricing_type in ['PAID', 'BYOL']:
            score += 1
        
        # Oracle validated
        if listing.get('oracle-validated'):
            score += 2
        
        if score >= 4:
            return 'HIGH'
        elif score >= 2:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def is_security_focused(self, listing):
        """Check if security-focused"""
        text = ' '.join([
            str(listing.get('name', '')),
            str(self.get_category(listing) or ''),
            str(listing.get('short-description', '')),
        ]).lower()
        
        security_terms = ['security', 'firewall', 'vpn', 'encryption', 'auth', 'siem', 'vulnerability']
        return any(term in text for term in security_terms)
    
    def is_ai_ml_related(self, listing):
        """Check if AI/ML related"""
        text = ' '.join([
            str(listing.get('name', '')),
            str(self.get_category(listing) or ''),
            str(listing.get('short-description', '')),
        ]).lower()
        
        ai_terms = ['ai', 'artificial intelligence', 'machine learning', 'ml', 'deep learning', 'neural']
        return any(term in text for term in ai_terms)
    
    def is_database_related(self, listing):
        """Check if database related"""
        text = ' '.join([
            str(listing.get('name', '')),
            str(self.get_category(listing) or ''),
        ]).lower()
        
        db_terms = ['database', 'sql', 'nosql', 'mongodb', 'mysql', 'postgres', 'oracle']
        return any(term in text for term in db_terms)
    
    def is_networking_related(self, listing):
        """Check if networking related"""
        text = ' '.join([
            str(listing.get('name', '')),
            str(self.get_category(listing) or ''),
        ]).lower()
        
        net_terms = ['network', 'load balancer', 'dns', 'cdn', 'proxy', 'gateway']
        return any(term in text for term in net_terms)
    
    def extract_compliance_certifications(self, listing):
        """Extract compliance certifications mentioned"""
        text = ' '.join([
            str(listing.get('name', '')),
            str(listing.get('short-description', '')),
            str(listing.get('long-description', '')),
        ]).lower()
        
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
    
    def export_to_excel(self, filename='oracle_marketplace_oci_complete.xlsx'):
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
                
                # Government compliance summary
                gov_data = []
                for item in processed_data:
                    gov_item = {
                        'Listing ID': item['listing_id'],
                        'Product Name': item['product_name'],
                        'Publisher': item['publisher'],
                        'Category': item['category'],
                        'US Gov Ready': item['us_government_ready'],
                        'US Gov Available': '✓' if item['us_government_available'] else '✗',
                        'US DoD Ready': item['us_dod_ready'],
                        'DoD Impact Level': item['dod_impact_level'],
                        'UK Gov Ready': item['uk_government_ready'],
                        'UK Gov Available': '✓' if item['uk_government_available'] else '✗',
                        'FedRAMP': '✓' if item['fedramp_indicators'] else '✗',
                        'CMMC': '✓' if item['cmmc_indicators'] else '✗',
                        'Export Control': item['export_control_status'],
                        'Sales Priority': item['sales_priority'],
                        'Compliance Certs': item['compliance_certifications'],
                        'Marketplace URL': item['marketplace_url']
                    }
                    gov_data.append(gov_item)
                
                df_gov = pd.DataFrame(gov_data)
                df_gov.to_excel(writer, sheet_name='Government Analysis', index=False)
                
                # Sales prioritization
                sales_data = []
                for item in processed_data:
                    if item['sales_priority'] in ['HIGH', 'MEDIUM']:
                        sales_item = {
                            'Priority': item['sales_priority'],
                            'Product Name': item['product_name'],
                            'Publisher': item['publisher'],
                            'Category': item['market_category'],
                            'US Gov Ready': item['us_government_ready'],
                            'DoD Ready': item['us_dod_ready'],
                            'UK Gov Ready': item['uk_government_ready'],
                            'Pricing Model': item['pricing_model'],
                            'Enterprise Ready': item['enterprise_readiness'],
                            'Security Focus': '✓' if item['security_focused'] else '✗',
                            'AI/ML': '✓' if item['ai_ml_related'] else '✗',
                            'Database': '✓' if item['database_related'] else '✗',
                            'Networking': '✓' if item['networking_related'] else '✗',
                            'Marketplace URL': item['marketplace_url']
                        }
                        sales_data.append(sales_item)
                
                # Sort by priority
                sales_data.sort(key=lambda x: {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}[x['Priority']], reverse=True)
                df_sales = pd.DataFrame(sales_data)
                df_sales.to_excel(writer, sheet_name='Sales Priorities', index=False)
                
                # Publisher analysis
                publisher_stats = df_catalog.groupby('publisher').agg({
                    'listing_id': 'count',
                    'us_government_ready': lambda x: sum(1 for v in x if v == 'READY'),
                    'us_dod_ready': lambda x: sum(1 for v in x if v == 'READY'),
                    'sales_priority': lambda x: sum(1 for v in x if v == 'HIGH')
                }).rename(columns={
                    'listing_id': 'Total Listings',
                    'us_government_ready': 'US Gov Ready',
                    'us_dod_ready': 'DoD Ready',
                    'sales_priority': 'High Priority'
                }).reset_index()
                
                publisher_stats = publisher_stats.sort_values('Total Listings', ascending=False)
                publisher_stats.to_excel(writer, sheet_name='Publisher Analysis', index=False)
                
                # Category breakdown
                category_stats = df_catalog.groupby('category').agg({
                    'listing_id': 'count',
                    'us_government_ready': lambda x: sum(1 for v in x if v in ['READY', 'POTENTIAL']),
                    'pricing_model': lambda x: sum(1 for v in x if v == 'PAID')
                }).rename(columns={
                    'listing_id': 'Total Listings',
                    'us_government_ready': 'Gov Compatible',
                    'pricing_model': 'Paid Offerings'
                }).reset_index()
                
                category_stats = category_stats.sort_values('Total Listings', ascending=False)
                category_stats.to_excel(writer, sheet_name='Category Analysis', index=False)
                
                # Summary statistics
                summary_stats = self.generate_summary_statistics(processed_data)
                df_summary = pd.DataFrame(summary_stats)
                df_summary.to_excel(writer, sheet_name='Summary Statistics', index=False)
            
            print(f"✅ Complete marketplace catalog exported to: {filename}")
            print(f"   📊 {len(processed_data)} total listings")
            print(f"   🏛️ Government compliance analysis included")
            print(f"   📈 Sales prioritization completed")
            
        except Exception as e:
            print(f"❌ Error exporting to Excel: {e}")
            # Fallback to CSV
            df_catalog = pd.DataFrame(processed_data)
            csv_filename = filename.replace('.xlsx', '.csv')
            df_catalog.to_csv(csv_filename, index=False)
            print(f"💾 Fallback: Data saved to {csv_filename}")
    
    def generate_summary_statistics(self, processed_data):
        """Generate comprehensive summary statistics"""
        df = pd.DataFrame(processed_data)
        stats = []
        
        # Basic counts
        stats.append({'Metric': 'Total Marketplace Listings', 'Value': len(df), 'Category': 'Overview'})
        
        # Pricing breakdown
        pricing_counts = df['pricing_model'].value_counts()
        for pricing, count in pricing_counts.items():
            if pricing:
                stats.append({'Metric': f'Pricing Model: {pricing}', 'Value': count, 'Category': 'Pricing'})
        
        # Government readiness
        us_gov_ready = sum(1 for x in df['us_government_ready'] if x == 'READY')
        us_gov_potential = sum(1 for x in df['us_government_ready'] if x == 'POTENTIAL')
        stats.append({'Metric': 'US Government Ready', 'Value': us_gov_ready, 'Category': 'Government'})
        stats.append({'Metric': 'US Government Potential', 'Value': us_gov_potential, 'Category': 'Government'})
        
        dod_ready = sum(1 for x in df['us_dod_ready'] if x == 'READY')
        dod_potential = sum(1 for x in df['us_dod_ready'] if x == 'POTENTIAL')
        stats.append({'Metric': 'US DoD Ready', 'Value': dod_ready, 'Category': 'Government'})
        stats.append({'Metric': 'US DoD Potential', 'Value': dod_potential, 'Category': 'Government'})
        
        uk_ready = sum(1 for x in df['uk_government_ready'] if x == 'READY')
        stats.append({'Metric': 'UK Government Ready', 'Value': uk_ready, 'Category': 'Government'})
        
        # Government region availability
        us_gov_available = sum(1 for x in df['us_government_available'] if x)
        uk_gov_available = sum(1 for x in df['uk_government_available'] if x)
        stats.append({'Metric': 'Available in US Gov Regions', 'Value': us_gov_available, 'Category': 'Government'})
        stats.append({'Metric': 'Available in UK Gov Regions', 'Value': uk_gov_available, 'Category': 'Government'})
        
        # Compliance indicators
        fedramp_count = sum(1 for x in df['fedramp_indicators'] if x)
        cmmc_count = sum(1 for x in df['cmmc_indicators'] if x)
        stats.append({'Metric': 'FedRAMP Mentions', 'Value': fedramp_count, 'Category': 'Compliance'})
        stats.append({'Metric': 'CMMC Mentions', 'Value': cmmc_count, 'Category': 'Compliance'})
        
        # Sales priority
        priority_counts = df['sales_priority'].value_counts()
        for priority, count in priority_counts.items():
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
        top_publishers = df['publisher'].value_counts().head(5)
        for publisher, count in top_publishers.items():
            if publisher:
                stats.append({'Metric': f'Publisher: {publisher}', 'Value': count, 'Category': 'Publishers'})
        
        # Enterprise readiness
        enterprise_counts = df['enterprise_readiness'].value_counts()
        for level, count in enterprise_counts.items():
            stats.append({'Metric': f'Enterprise Ready: {level}', 'Value': count, 'Category': 'Enterprise'})
        
        return stats
    
    def generate_government_report(self):
        """Generate a focused government compliance report"""
        processed_data = self.process_to_spreadsheet_format()
        
        # Filter for government-relevant listings
        gov_relevant = []
        for item in processed_data:
            if (item['us_government_ready'] in ['READY', 'POTENTIAL'] or
                item['us_dod_ready'] in ['READY', 'POTENTIAL'] or
                item['uk_government_ready'] in ['READY', 'POTENTIAL'] or
                item['us_government_available'] or
                item['uk_government_available']):
                gov_relevant.append(item)
        
        print(f"\n🏛️ Government Compliance Report")
        print(f"================================")
        print(f"Total listings analyzed: {len(processed_data)}")
        print(f"Government-relevant listings: {len(gov_relevant)}")
        
        # US Government summary
        us_ready = sum(1 for x in gov_relevant if x['us_government_ready'] == 'READY')
        us_potential = sum(1 for x in gov_relevant if x['us_government_ready'] == 'POTENTIAL')
        us_available = sum(1 for x in gov_relevant if x['us_government_available'])
        
        print(f"\n🇺🇸 US Government:")
        print(f"   Ready: {us_ready}")
        print(f"   Potential: {us_potential}")
        print(f"   Available in Gov Regions: {us_available}")
        
        # US DoD summary
        dod_ready = sum(1 for x in gov_relevant if x['us_dod_ready'] == 'READY')
        dod_potential = sum(1 for x in gov_relevant if x['us_dod_ready'] == 'POTENTIAL')
        
        print(f"\n🛡️ US Department of Defense:")
        print(f"   Ready: {dod_ready}")
        print(f"   Potential: {dod_potential}")
        
        # UK Government summary
        uk_ready = sum(1 for x in gov_relevant if x['uk_government_ready'] == 'READY')
        uk_potential = sum(1 for x in gov_relevant if x['uk_government_ready'] == 'POTENTIAL')
        uk_available = sum(1 for x in gov_relevant if x['uk_government_available'])
        
        print(f"\n🇬🇧 UK Government:")
        print(f"   Ready: {uk_ready}")
        print(f"   Potential: {uk_potential}")
        print(f"   Available in UK Gov Regions: {uk_available}")
        
        # High priority government opportunities
        high_priority_gov = [x for x in gov_relevant if x['sales_priority'] == 'HIGH']
        print(f"\n⭐ High Priority Government Opportunities: {len(high_priority_gov)}")
        
        for item in high_priority_gov[:10]:  # Top 10
            print(f"   • {item['product_name']} ({item['publisher']})")
        
        return gov_relevant

def main():
    """Main execution function"""
    print("🚀 OCI Marketplace Data Processor")
    print("Converting OCI CLI output to comprehensive Excel spreadsheet")
    print("=" * 60)
    
    processor = OCIMarketplaceProcessor()
    
    try:
        # Load OCI data
        listings_count = processor.load_oci_data()
        
        if listings_count == 0:
            print("❌ No OCI data found. Please run the OCI CLI extractor first:")
            print("   Command: extract_marketplace_data.bat")
            return
        
        print(f"✅ Loaded {listings_count} marketplace listings from OCI CLI")
        
        # Export to Excel
        processor.export_to_excel('oracle_marketplace_complete_catalog.xlsx')
        
        # Generate government report
        processor.generate_government_report()
        
        print(f"\n🎉 Processing Complete!")
        print(f"📄 Main file: oracle_marketplace_complete_catalog.xlsx")
        print(f"📊 Multiple sheets with comprehensive analysis")
        print(f"🏛️ Government compliance analysis included")
        print(f"📈 Sales prioritization completed")
        
    except Exception as e:
        print(f"❌ Error during processing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
