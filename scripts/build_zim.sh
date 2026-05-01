#!/bin/bash
set -e
HTML_DIR="src/html"
ZIM_FILE="laws_$(date +%Y%m%d_%H%M%S).zim"

# Make sure we have a 48x48 icon
if [ ! -f "src/static/icon_48.png" ]; then
    echo "Warning: No 48x48 icon found. Creating a default one."
    # Create a simple placeholder icon (48x48 transparent)
    convert -size 48x48 xc:transparent src/static/icon_48.png 2>/dev/null || touch src/static/icon_48.png
fi

zimwriterfs \
  --welcome=index.html \
  --illustration=src/static/icon_48.png \
  --language=per \
  --name="iranian-laws" \
  --title="Iranian Laws & Rulings" \
  --description="Collaborative legal wiki" \
  --creator="Contributors" \
  --publisher="GitHub Actions" \
  "$HTML_DIR" "$ZIM_FILE"

echo "ZIM_FILE=$ZIM_FILE" >> $GITHUB_ENV
