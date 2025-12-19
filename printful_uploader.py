#!/usr/bin/env python3
"""
Printful Integration for TrendMerch
Automatically creates products on Printful (which syncs to your store)

Requirements:
1. Printful account (free): https://www.printful.com/
2. Connect a store (Etsy, Shopify, etc.) in Printful dashboard
3. Get API key from: https://www.printful.com/dashboard/developer/oauth-apps
4. Set PRINTFUL_API_KEY environment variable

Printful Free Tier:
- No monthly fees (pay per order only)
- Free product mockups
- Free storage of designs
- API access included
"""

import os
import json
import base64
import requests
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class PrintfulUploader:
    """
    Uploads designs to Printful and creates products.
    Products automatically sync to your connected store.
    """
    
    BASE_URL = "https://api.printful.com"
    
    # Popular Printful product IDs (T-Shirts)
    PRODUCTS = {
        "unisex_tshirt": 71,        # Bella+Canvas 3001 (Most popular)
        "premium_tshirt": 380,       # Comfort Colors 1717
        "womens_tshirt": 75,         # Bella+Canvas 6004
        "mens_tshirt": 586,          # Gildan 64000
        "hoodie": 146,               # Gildan 18500
        "sweatshirt": 147,           # Gildan 18000
    }
    
    # Variant IDs for common sizes/colors
    VARIANTS = {
        "unisex_tshirt": {
            "S_Black": 4012, "M_Black": 4013, "L_Black": 4014, "XL_Black": 4015,
            "S_White": 4017, "M_White": 4018, "L_White": 4019, "XL_White": 4020,
            "S_Navy": 4022, "M_Navy": 4023, "L_Navy": 4024, "XL_Navy": 4025,
        }
    }
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("PRINTFUL_API_KEY")
        if not self.api_key:
            raise ValueError("PRINTFUL_API_KEY not found. Get it from https://www.printful.com/dashboard/developer/oauth-apps")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def _request(self, method: str, endpoint: str, data: dict = None) -> dict:
        """Make API request to Printful."""
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers)
            elif method.upper() == "POST":
                response = requests.post(url, headers=self.headers, json=data)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=self.headers, json=data)
            else:
                raise ValueError(f"Unknown method: {method}")
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Printful API error: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"   Response: {e.response.text}")
            raise
    
    def get_stores(self) -> List[dict]:
        """Get connected stores."""
        result = self._request("GET", "/stores")
        return result.get("result", [])
    
    def upload_file(self, file_path: str) -> dict:
        """
        Upload a design file to Printful's file library.
        Returns file info with URL.
        """
        print(f"📤 Uploading to Printful: {file_path}")
        
        # Read and encode file
        with open(file_path, "rb") as f:
            file_data = base64.b64encode(f.read()).decode()
        
        filename = Path(file_path).name
        
        data = {
            "type": "default",
            "filename": filename,
            "contents": file_data
        }
        
        result = self._request("POST", "/files", data)
        file_info = result.get("result", {})
        
        print(f"   ✅ Uploaded! File ID: {file_info.get('id')}")
        return file_info
    
    def create_product(self, 
                      design_file: str,
                      title: str,
                      description: str = None,
                      product_type: str = "unisex_tshirt",
                      store_id: int = None,
                      price: float = 24.99) -> dict:
        """
        Create a product in Printful with the design.
        
        Args:
            design_file: Path to PNG file
            title: Product title
            description: Product description
            product_type: Type of product (unisex_tshirt, hoodie, etc.)
            store_id: Store ID (if you have multiple stores)
            price: Retail price
        
        Returns:
            Product info from Printful
        """
        print(f"\n🛍️ Creating product: {title}")
        
        # Upload design file
        file_info = self.upload_file(design_file)
        file_url = file_info.get("preview_url") or file_info.get("url")
        file_id = file_info.get("id")
        
        if not file_url:
            raise ValueError("Failed to get file URL from Printful")
        
        # Get product and variant info
        product_id = self.PRODUCTS.get(product_type, self.PRODUCTS["unisex_tshirt"])
        variants = self.VARIANTS.get(product_type, self.VARIANTS["unisex_tshirt"])
        
        # Build sync variants (different sizes/colors)
        sync_variants = []
        for variant_name, variant_id in list(variants.items())[:8]:  # Limit to 8 variants
            sync_variants.append({
                "variant_id": variant_id,
                "files": [
                    {
                        "type": "front",
                        "id": file_id,
                        "position": {
                            "area_width": 1800,
                            "area_height": 2400,
                            "width": 1800,
                            "height": 2400,
                            "top": 0,
                            "left": 0
                        }
                    }
                ],
                "retail_price": str(price)
            })
        
        # Create product data
        product_data = {
            "sync_product": {
                "name": title,
                "thumbnail": file_url
            },
            "sync_variants": sync_variants
        }
        
        # Add store ID if specified
        endpoint = f"/store/products"
        if store_id:
            self.headers["X-PF-Store-Id"] = str(store_id)
        
        result = self._request("POST", endpoint, product_data)
        product_info = result.get("result", {})
        
        print(f"   ✅ Product created!")
        print(f"   📦 ID: {product_info.get('sync_product', {}).get('id')}")
        print(f"   🔗 External ID: {product_info.get('sync_product', {}).get('external_id')}")
        
        return product_info
    
    def create_mockup(self, design_file: str, product_type: str = "unisex_tshirt") -> str:
        """
        Generate a product mockup image.
        Returns URL to mockup image.
        """
        print(f"📸 Generating mockup...")
        
        # Upload design
        file_info = self.upload_file(design_file)
        file_url = file_info.get("url")
        
        product_id = self.PRODUCTS.get(product_type, self.PRODUCTS["unisex_tshirt"])
        
        # Get mockup
        data = {
            "variant_ids": [4013],  # M_Black
            "files": [
                {
                    "placement": "front",
                    "image_url": file_url,
                    "position": {
                        "area_width": 1800,
                        "area_height": 2400,
                        "width": 1800,
                        "height": 2400,
                        "top": 0,
                        "left": 0
                    }
                }
            ]
        }
        
        result = self._request("POST", f"/mockup-generator/create-task/{product_id}", data)
        task_key = result.get("result", {}).get("task_key")
        
        if not task_key:
            raise ValueError("Failed to create mockup task")
        
        # Poll for result
        import time
        for _ in range(30):
            time.sleep(2)
            status = self._request("GET", f"/mockup-generator/task?task_key={task_key}")
            task_status = status.get("result", {}).get("status")
            
            if task_status == "completed":
                mockups = status.get("result", {}).get("mockups", [])
                if mockups:
                    mockup_url = mockups[0].get("mockup_url")
                    print(f"   ✅ Mockup ready: {mockup_url}")
                    return mockup_url
            elif task_status == "failed":
                raise ValueError("Mockup generation failed")
        
        raise TimeoutError("Mockup generation timed out")


def upload_designs_to_printful(design_paths: List[str], 
                                base_price: float = 24.99) -> List[dict]:
    """
    Batch upload designs and create products.
    
    Args:
        design_paths: List of paths to PNG files
        base_price: Retail price for products
    
    Returns:
        List of created product info
    """
    try:
        uploader = PrintfulUploader()
    except ValueError as e:
        print(f"⚠️ {e}")
        print("   Skipping Printful upload. Designs saved locally.")
        return []
    
    # Get stores
    stores = uploader.get_stores()
    if not stores:
        print("⚠️ No stores connected to Printful!")
        print("   Connect a store at: https://www.printful.com/dashboard/store")
        return []
    
    print(f"📦 Using store: {stores[0].get('name')}")
    store_id = stores[0].get("id")
    
    products = []
    for design_path in design_paths:
        try:
            # Generate title from filename
            filename = Path(design_path).stem
            title = filename.replace("_", " ").title()
            
            # Add timestamp suffix to make unique
            timestamp = datetime.now().strftime("%m%d")
            title = f"{title} {timestamp}"
            
            description = f"Trending design: {title}. High-quality print on soft, comfortable fabric."
            
            product = uploader.create_product(
                design_file=design_path,
                title=title,
                description=description,
                store_id=store_id,
                price=base_price
            )
            products.append(product)
            
        except Exception as e:
            print(f"❌ Failed to create product for {design_path}: {e}")
            continue
    
    print(f"\n✅ Created {len(products)} products on Printful!")
    return products


# For testing
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python printful_uploader.py <design.png>")
        print("\nEnvironment variables needed:")
        print("  PRINTFUL_API_KEY - Your Printful API key")
        sys.exit(1)
    
    design_file = sys.argv[1]
    results = upload_designs_to_printful([design_file])
    print(json.dumps(results, indent=2))

