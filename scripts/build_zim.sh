#!/bin/bash
set -e
HTML_DIR="src/html"
ZIM_FILE="laws_$(date +%Y%m%d_%H%M%S).zim"

# Copy icon into the HTML directory so it's relative to HTML_DIR
if [ -f "src/static/icon_48.png" ]; then
    cp src/static/icon_48.png "$HTML_DIR/icon_48.png"
    ILLUSTRATION="icon_48.png"
else
    # If no icon, create a transparent placeholder inside HTML_DIR
    if command -v convert &> /dev/null; then
        convert -size 48x48 xc:transparent "$HTML_DIR/icon_48.png"
    else
        touch "$HTML_DIR/icon_48.png"
    fi
    ILLUSTRATION="icon_48.png"
fi

zimwriterfs \
  --welcome=index.html \
  --illustration="$ILLUSTRATION" \
  --language=per \
  --name="iranian-laws" \
  --title="Iranian Laws & Rulings" \
  --description="Collaborative legal wiki" \
  --creator="Contributors" \
  --publisher="GitHub Actions" \
  "$HTML_DIR" "$ZIM_FILE"

echo "ZIM_FILE=$ZIM_FILE" >> $GITHUB_ENV
