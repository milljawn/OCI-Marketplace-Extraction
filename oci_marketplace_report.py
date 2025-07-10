import oci
import pandas as pd
from datetime import datetime

PROFILES = {
    "OC1": "OC1",
    "OC2": "OC2",
    "OC3": "OC3"
}

FIELDS = [
    'listing_id', 'display_name', 'publisher_name', 'summary', 
    'package_version', 'pricing_type', 'regions'
]

def get_marketplace_data(profile):
    config = oci.config.from_file("~/.oci/config", profile_name=profile)
    marketplace_client = oci.marketplace.MarketplaceClient(config)
    listings = []

    try:
        response = marketplace_client.list_listings(sort_by="TIMECREATED", sort_order="DESC")
        for listing in response.data:
            packages = marketplace_client.list_listing_packages(listing.id)
            for package in packages.data:
                listings.append({
                    "listing_id": listing.id,
                    "display_name": listing.name,
                    "publisher_name": listing.publisher_name,
                    "summary": listing.summary,
                    "package_version": package.version,
                    "pricing_type": package.pricing,
                    "regions": ', '.join(package.regions)
                })
    except Exception as e:
        print(f"Error fetching listings for {profile}: {e}")

    return listings

def generate_report():
    all_data = []
    for label, profile in PROFILES.items():
        print(f"Fetching data from profile: {label}")
        data = get_marketplace_data(profile)
        for entry in data:
            entry["source_profile"] = label
        all_data.extend(data)

    df = pd.DataFrame(all_data, columns=FIELDS + ['source_profile'])

    today = datetime.today().strftime("%Y-%m-%d")
    filename = f"OCI_Marketplace_Report_{today}.xlsx"
    df.to_excel(filename, index=False)
    print(f"✅ Report generated: {filename}")

if __name__ == "__main__":
    generate_report()
