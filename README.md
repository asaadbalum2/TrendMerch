# 👕 TrendMerch

**Automated T-Shirt Design Generator from Google Trends**

Turn trending topics into print-ready T-shirt designs automatically using AI—completely free!

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Cost](https://img.shields.io/badge/Cost-$0-brightgreen?style=flat-square)

## 🚀 Features

- **Zero-Cost**: Uses free HuggingFace API + pytrends + rembg
- **Trend Detection**: Automatically fetches rising Google Trends
- **AI Art Generation**: Uses FLUX.1-schnell (excellent at text rendering)
- **Background Removal**: Clean transparent PNGs ready for POD
- **Print-Ready**: Auto-resizes to 4500x5400 (standard T-shirt size)
- **Multiple Styles**: Vaporwave, minimalist, graffiti, vintage, and more

## 🎨 Style Presets

| Style | Description |
|-------|-------------|
| `vaporwave` | Retro 80s neon aesthetic |
| `minimalist` | Clean, simple typography |
| `graffiti` | Street art spray paint |
| `vintage` | Distressed retro look |
| `neon` | Cyberpunk glow effect |
| `cartoon` | Fun, playful bubbles |
| `gothic` | Dark ornate lettering |
| `sports` | Athletic team style |

## 📁 Project Structure

```
TrendMerch/
├── design.py           # Main design generator
├── requirements.txt    # Python dependencies
├── output/             # Generated designs go here
└── cache/              # Trend cache (optional)
```

## 🛠️ Installation

### Prerequisites

1. **Python 3.10+**
2. **HuggingFace Account** (free): https://huggingface.co/join

### Setup

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/TrendMerch.git
cd TrendMerch

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### Get HuggingFace Token (Required)

1. Go to https://huggingface.co/settings/tokens
2. Click "New token"
3. Name it "TrendMerch" and select "Read" access
4. Copy the token
5. Set environment variable:

```bash
# Linux/Mac
export HF_TOKEN=hf_your_token_here

# Windows (PowerShell)
$env:HF_TOKEN = "hf_your_token_here"

# Or add to .env file
echo "HF_TOKEN=hf_your_token_here" > .env
```

## 📝 Usage

### Auto-Generate from Trends

```bash
# Generate 5 designs from top US trends (default)
python design.py --auto

# Generate 10 designs
python design.py --auto --count 10

# Use minimalist style
python design.py --auto --style minimalist

# UK trends instead of US
python design.py --auto --region GB
```

### Generate Custom Design

```bash
# Create design with custom text
python design.py --text "Your Custom Text"

# With specific style
python design.py --text "Hustle Mode" --style graffiti
```

### List Options

```bash
# See all available styles
python design.py --list-styles

# Check if dependencies are installed
python design.py --check
```

### Full Options

```bash
python design.py --auto \
    --count 10 \
    --style vaporwave \
    --region US \
    --no-bg-remove \  # Skip background removal
    --no-resize       # Keep original size
```

## 🖼️ Output

Generated designs are saved to `./output/`:
- **Format**: PNG with transparency
- **Size**: 4500x5400 pixels (print-ready)
- **Naming**: `{trend_slug}_{timestamp}.png`

## ⚙️ Configuration

Edit `design.py` to customize:

```python
# Output dimensions
TSHIRT_WIDTH = 4500   # pixels
TSHIRT_HEIGHT = 5400  # pixels

# AI Model
HF_MODEL = "black-forest-labs/FLUX.1-schnell"

# Add custom style presets
STYLE_PRESETS["mystyle"] = "Your custom prompt with {trend}..."
```

## 🚀 Deployment (Oracle Cloud Free Tier)

```bash
# SSH into Oracle instance
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip git -y

# Clone and setup
git clone https://github.com/YOUR_USERNAME/TrendMerch.git
cd TrendMerch
pip3 install -r requirements.txt

# Set token
export HF_TOKEN=your_token_here

# Run
python3 design.py --auto --count 10
```

## 💰 Monetization Strategy

### Print-on-Demand Platforms (Free to list)

1. **Redbubble** - Best for beginners, handles everything
2. **TeePublic** - Good royalties, easy upload
3. **Merch by Amazon** - Highest traffic (requires approval)
4. **Printful** - Best quality, integrates with Shopify
5. **Spreadshirt** - European market

### Tips for Success

1. **Speed**: Generate designs for trending topics FAST
2. **Volume**: More designs = more chances for sales
3. **Niches**: Focus on specific audiences (gamers, fitness, etc.)
4. **Quality**: Review AI output before uploading
5. **Keywords**: Use trending terms in product titles/tags

### Scaling

```bash
# Cron job for daily generation (Linux)
0 9 * * * cd /path/to/TrendMerch && python3 design.py --auto --count 20
```

## ⚠️ Important Notes

### Rate Limits

- HuggingFace free tier has rate limits
- Script automatically waits and retries on 503 errors
- Generate during off-peak hours for better success

### Copyright Considerations

- Avoid trademarked terms
- Don't use celebrity names without rights
- Check trend terms before uploading to POD platforms
- When in doubt, skip that design

### API Limitations

- pytrends may occasionally be blocked by Google
- Script includes fallback topics for this case
- VPN or proxy may help if blocked frequently

## 🔧 Troubleshooting

### "HF_TOKEN not set"
Set your HuggingFace token as environment variable.

### "503 Service Unavailable"
HuggingFace is busy. Script will retry automatically.

### "No trends found"
Google may be blocking requests. Try again later or use VPN.

### Background removal fails
First run downloads rembg model (~170MB). Ensure internet connection.

## 🤝 Contributing

Pull requests welcome! Ideas for improvement:
- More style presets
- Batch upload to POD platforms
- Trend analysis/filtering
- Multi-language support

## 📄 License

MIT License - use commercially, modify freely!

---

**Made with ❤️ for the print-on-demand hustle**

