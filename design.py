#!/usr/bin/env python3
"""
TrendMerch - Automated T-Shirt Design Generator from Google Trends
Zero-Cost Stack: pytrends + HuggingFace (Flux) + rembg + PIL

Monitors trending topics and generates print-ready designs automatically.
"""

import argparse
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from PIL import Image
from io import BytesIO

# Trend fetching
try:
    from pytrends.request import TrendReq
    PYTRENDS_AVAILABLE = True
except ImportError:
    PYTRENDS_AVAILABLE = False

# HuggingFace
try:
    from huggingface_hub import InferenceClient
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False

# Background removal
try:
    from rembg import remove
    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False


# ============ CONFIGURATION ============
OUTPUT_DIR = Path("./output")
CACHE_DIR = Path("./cache")

# HuggingFace settings
HF_MODEL = "black-forest-labs/FLUX.1-schnell"  # Excellent at text rendering
HF_TIMEOUT = 120  # Seconds to wait for generation

# T-Shirt dimensions (Standard POD sizes)
TSHIRT_WIDTH = 4500   # pixels
TSHIRT_HEIGHT = 5400  # pixels

# Design style presets
STYLE_PRESETS = {
    "vaporwave": "A retro vaporwave t-shirt vector design featuring the text '{trend}' in bold typography, vibrant neon pink and cyan colors, black background, high contrast, 80s aesthetic",
    "minimalist": "A minimalist t-shirt design with the text '{trend}' in clean sans-serif typography, black text on white background, simple and elegant",
    "graffiti": "A graffiti street art style t-shirt design featuring the text '{trend}' in bold spray paint letters, urban aesthetic, colorful drips, black background",
    "vintage": "A vintage distressed t-shirt design with the text '{trend}' in retro typography, worn texture, cream and brown tones, classic americana style",
    "neon": "A neon glow t-shirt design featuring the text '{trend}' in bright glowing letters, cyberpunk style, dark background, electric colors",
    "cartoon": "A fun cartoon style t-shirt design with the text '{trend}' in playful bubble letters, bright colors, cute aesthetic, white background",
    "gothic": "A gothic dark aesthetic t-shirt design featuring the text '{trend}' in ornate blackletter typography, dark colors, mysterious vibe",
    "sports": "A bold sports team style t-shirt design with the text '{trend}' in athletic block letters, dynamic angles, team jersey aesthetic",
}

DEFAULT_STYLE = "vaporwave"


def ensure_directories():
    """Create necessary directories."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    CACHE_DIR.mkdir(exist_ok=True)


def check_dependencies():
    """Check if all required packages are installed."""
    missing = []
    
    if not PYTRENDS_AVAILABLE:
        missing.append("pytrends")
    if not HF_AVAILABLE:
        missing.append("huggingface_hub")
    if not REMBG_AVAILABLE:
        missing.append("rembg")
    
    if missing:
        print("❌ Missing required packages:")
        for pkg in missing:
            print(f"   - {pkg}")
        print("\n📦 Install with: pip install " + " ".join(missing))
        sys.exit(1)
    
    # Check for HuggingFace token
    hf_token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN")
    if not hf_token:
        print("⚠️ Warning: HF_TOKEN not set!")
        print("   Some models may not work without authentication.")
        print("   Get your free token at: https://huggingface.co/settings/tokens")
        print("   Then set: export HF_TOKEN=your_token_here")
    
    print("✅ All dependencies found!")
    return hf_token


def slugify(text: str) -> str:
    """Convert text to URL-safe slug."""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '_', text)
    return text.strip('_')


def get_trending_topics(
    region: str = "US",
    timeframe: str = "now 1-H",
    limit: int = 10
) -> List[dict]:
    """
    Fetch rising queries from Google Trends.
    
    Args:
        region: Country code (US, GB, CA, etc.)
        timeframe: 'now 1-H' (last hour), 'now 4-H', 'now 1-d', 'now 7-d'
        limit: Maximum number of trends to return
    
    Returns:
        List of dicts with 'query' and 'value' keys
    """
    print(f"\n📊 Fetching trending topics ({region}, {timeframe})...")
    
    pytrends = TrendReq(hl='en-US', tz=360, timeout=(10, 25))
    
    try:
        # Get trending searches (real-time)
        trending = pytrends.trending_searches(pn=region.lower())
        
        if trending.empty:
            print("   No trending searches found, trying realtime trends...")
            # Fallback: Get realtime trending searches
            trending = pytrends.realtime_trending_searches(pn=region)
            if not trending.empty:
                topics = trending['title'].head(limit).tolist()
                return [{"query": t, "value": 100 - i*5} for i, t in enumerate(topics)]
        else:
            topics = trending[0].head(limit).tolist()
            return [{"query": t, "value": 100 - i*5} for i, t in enumerate(topics)]
        
    except Exception as e:
        print(f"   ⚠️ Error fetching trends: {e}")
        print("   Using fallback trending topics...")
        
        # Fallback: popular evergreen topics
        fallback = [
            "AI Generated Art",
            "Viral Memes 2024", 
            "Trending Now",
            "Just Vibing",
            "No Cap",
        ]
        return [{"query": t, "value": 100 - i*10} for i, t in enumerate(fallback)]
    
    return []


def create_prompt(trend: str, style: str = DEFAULT_STYLE) -> str:
    """
    Create an optimized prompt for the AI model.
    """
    if style in STYLE_PRESETS:
        prompt = STYLE_PRESETS[style].format(trend=trend)
    else:
        # Custom style passed directly
        prompt = style.format(trend=trend) if '{trend}' in style else f"{style} with text '{trend}'"
    
    # Add quality boosters
    prompt += ", high quality, vector art, print ready, centered composition"
    
    return prompt


def generate_design(
    prompt: str,
    hf_token: Optional[str] = None,
    retries: int = 3
) -> Optional[Image.Image]:
    """
    Generate design using HuggingFace Inference API.
    
    Handles rate limits with automatic retry.
    """
    print(f"\n🎨 Generating design...")
    print(f"   Prompt: {prompt[:80]}...")
    
    # Initialize client
    client = InferenceClient(token=hf_token) if hf_token else InferenceClient()
    
    for attempt in range(retries):
        try:
            print(f"   Attempt {attempt + 1}/{retries}...")
            
            # Generate image
            image = client.text_to_image(
                prompt,
                model=HF_MODEL,
            )
            
            print("✅ Design generated!")
            return image
            
        except Exception as e:
            error_msg = str(e)
            
            if "503" in error_msg or "Service Unavailable" in error_msg:
                wait_time = 60 * (attempt + 1)  # Exponential backoff
                print(f"   ⚠️ API busy (503). Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
            elif "429" in error_msg or "rate limit" in error_msg.lower():
                wait_time = 60
                print(f"   ⚠️ Rate limited. Waiting {wait_time}s...")
                time.sleep(wait_time)
            elif "401" in error_msg or "unauthorized" in error_msg.lower():
                print("   ❌ Authentication error. Please check your HF_TOKEN.")
                return None
            else:
                print(f"   ❌ Error: {e}")
                if attempt < retries - 1:
                    print("   Retrying...")
                    time.sleep(10)
    
    print("   ❌ All retries failed.")
    return None


def remove_background(image: Image.Image) -> Image.Image:
    """
    Remove background from image using rembg.
    Returns image with transparent background.
    """
    print("🔧 Removing background...")
    
    # Convert to bytes for rembg
    img_bytes = BytesIO()
    image.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    # Remove background
    result_bytes = remove(img_bytes.read())
    
    # Convert back to PIL Image
    result = Image.open(BytesIO(result_bytes))
    
    print("✅ Background removed!")
    return result


def resize_for_print(
    image: Image.Image,
    width: int = TSHIRT_WIDTH,
    height: int = TSHIRT_HEIGHT
) -> Image.Image:
    """
    Resize image to print dimensions using high-quality resampling.
    Maintains aspect ratio and centers on canvas.
    """
    print(f"📐 Resizing to {width}x{height} for print...")
    
    # Calculate scaling to fit while maintaining aspect ratio
    img_ratio = image.width / image.height
    target_ratio = width / height
    
    if img_ratio > target_ratio:
        # Image is wider, scale by width
        new_width = width
        new_height = int(width / img_ratio)
    else:
        # Image is taller, scale by height
        new_height = height
        new_width = int(height * img_ratio)
    
    # Resize with high quality
    resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Create transparent canvas
    canvas = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    
    # Center the image
    x = (width - new_width) // 2
    y = (height - new_height) // 2
    
    # Paste (handling transparency)
    if resized.mode == 'RGBA':
        canvas.paste(resized, (x, y), resized)
    else:
        canvas.paste(resized, (x, y))
    
    print("✅ Resized for print!")
    return canvas


def process_trend(
    trend: str,
    style: str = DEFAULT_STYLE,
    remove_bg: bool = True,
    resize: bool = True,
    hf_token: Optional[str] = None
) -> Optional[str]:
    """
    Full pipeline: Trend → Design → Post-process → Save
    """
    print("\n" + "="*60)
    print(f"🎯 Processing trend: {trend}")
    print(f"   Style: {style}")
    print("="*60)
    
    # Create prompt
    prompt = create_prompt(trend, style)
    
    # Generate design
    image = generate_design(prompt, hf_token)
    
    if image is None:
        print("❌ Failed to generate design")
        return None
    
    # Post-processing
    if remove_bg:
        try:
            image = remove_background(image)
        except Exception as e:
            print(f"⚠️ Background removal failed: {e}")
            # Continue with original image
    
    if resize:
        # Convert to RGBA if not already
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        image = resize_for_print(image)
    
    # Save
    slug = slugify(trend)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{slug}_{timestamp}.png"
    output_path = OUTPUT_DIR / filename
    
    image.save(output_path, 'PNG', optimize=True)
    
    print(f"\n✅ Design saved: {output_path}")
    print(f"   Size: {image.width}x{image.height}")
    
    return str(output_path)


def auto_generate(
    count: int = 5,
    style: str = DEFAULT_STYLE,
    region: str = "US",
    hf_token: Optional[str] = None
) -> List[str]:
    """
    Automatically fetch trends and generate designs.
    """
    print("\n" + "="*60)
    print("🚀 TrendMerch - Auto Generate Mode")
    print("="*60)
    
    ensure_directories()
    
    # Fetch trends
    trends = get_trending_topics(region=region, limit=count)
    
    if not trends:
        print("❌ No trends found!")
        return []
    
    print(f"\n📈 Top {len(trends)} trends:")
    for i, t in enumerate(trends, 1):
        print(f"   {i}. {t['query']}")
    
    # Generate designs
    generated = []
    for i, trend_data in enumerate(trends, 1):
        trend = trend_data['query']
        print(f"\n{'='*60}")
        print(f"📹 Generating design {i}/{len(trends)}")
        
        try:
            output = process_trend(trend, style, hf_token=hf_token)
            if output:
                generated.append(output)
        except Exception as e:
            print(f"❌ Error: {e}")
            continue
        
        # Rate limiting between generations
        if i < len(trends):
            print("\n⏳ Waiting 10s before next generation...")
            time.sleep(10)
    
    # Summary
    print("\n" + "="*60)
    print("📊 GENERATION COMPLETE")
    print("="*60)
    print(f"   ✅ Successful: {len(generated)}/{len(trends)}")
    print(f"   📁 Output: {OUTPUT_DIR}/")
    
    return generated


def main():
    """Main entry point with CLI."""
    parser = argparse.ArgumentParser(
        description="TrendMerch - Automated T-Shirt Design Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-generate from top trends
  python design.py --auto
  
  # Generate 10 designs
  python design.py --auto --count 10
  
  # Use specific style
  python design.py --auto --style minimalist
  
  # Generate from custom text
  python design.py --text "Your Custom Text"
  
  # List available styles
  python design.py --list-styles

Available Styles:
  vaporwave  - Retro 80s neon aesthetic
  minimalist - Clean, simple typography
  graffiti   - Street art spray paint
  vintage    - Distressed retro look
  neon       - Cyberpunk glow effect
  cartoon    - Fun, playful bubbles
  gothic     - Dark ornate lettering
  sports     - Athletic team style
        """
    )
    
    parser.add_argument("--auto", "-a", action="store_true", 
                       help="Auto-fetch trends and generate designs")
    parser.add_argument("--text", "-t", help="Custom text for design")
    parser.add_argument("--style", "-s", default=DEFAULT_STYLE,
                       help=f"Design style (default: {DEFAULT_STYLE})")
    parser.add_argument("--count", "-c", type=int, default=5,
                       help="Number of designs to generate (default: 5)")
    parser.add_argument("--region", "-r", default="US",
                       help="Region for trends (default: US)")
    parser.add_argument("--no-bg-remove", action="store_true",
                       help="Skip background removal")
    parser.add_argument("--no-resize", action="store_true",
                       help="Skip resizing for print")
    parser.add_argument("--list-styles", action="store_true",
                       help="List available style presets")
    parser.add_argument("--check", action="store_true",
                       help="Check dependencies only")
    
    args = parser.parse_args()
    
    if args.list_styles:
        print("\n🎨 Available Style Presets:\n")
        for name, prompt in STYLE_PRESETS.items():
            preview = prompt.replace("{trend}", "EXAMPLE")[:60]
            print(f"   {name:12} → {preview}...")
        return
    
    # Check dependencies
    hf_token = check_dependencies()
    
    if args.check:
        return
    
    ensure_directories()
    
    if args.auto:
        auto_generate(
            count=args.count,
            style=args.style,
            region=args.region,
            hf_token=hf_token
        )
    elif args.text:
        process_trend(
            args.text,
            style=args.style,
            remove_bg=not args.no_bg_remove,
            resize=not args.no_resize,
            hf_token=hf_token
        )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

