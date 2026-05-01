#!/bin/bash
set -e
HTML_DIR="src/html"
VERSION="$1"
if [ -z "$VERSION" ]; then
    VERSION="$(date +%Y-%m-%d-%H%M%S)"
fi
ZIM_FILE="majalle-${VERSION}.zim"

echo "Building ZIM with version: $VERSION"
echo "Output file: $ZIM_FILE"

# Copy or create icon
if [ -f "src/static/icon_48.png" ]; then
    cp src/static/icon_48.png "$HTML_DIR/icon_48.png"
else
    if command -v convert &> /dev/null; then
        convert -size 48x48 xc:transparent "$HTML_DIR/icon_48.png"
    else
        touch "$HTML_DIR/icon_48.png"
    fi
fi

zimwriterfs \
  --welcome=index.html \
  --illustration="icon_48.png" \
  --language=per \
  --name="مجله" \
  --title="مجله" \
  --description="مجله قوانین ایران" \
  --longDescription="This ZIM file contains Iranian laws and rulings, built from the rc.majlis dataset and user contributions." \
  --creator="Mücteba Nesiri" \
  --publisher="Mücteba Nesiri" \
  --withFulltextIndex true \
  "$HTML_DIR" "$ZIM_FILE"

# Verify and set output
if [ -f "$ZIM_FILE" ]; then
    echo "✅ ZIM file created: $ZIM_FILE"
    echo "ZIM_FILE=$ZIM_FILE" >> $GITHUB_ENV
else
    echo "❌ Failed to create $ZIM_FILE"
    exit 1
fi
