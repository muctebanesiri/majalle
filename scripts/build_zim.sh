#!/bin/bash
set -e
HTML_DIR="src/html"
ZIM_FILE="laws_$(date +%Y%m%d_%H%M%S).zim"

# Copy icon into the HTML directory
if [ -f "src/static/icon_48.png" ]; then
    cp src/static/icon_48.png "$HTML_DIR/icon_48.png"
    ILLUSTRATION="icon_48.png"
else
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
  --longDescription="This ZIM file contains a collection of Iranian laws, regulations, and judicial rulings, formatted for offline reading with Kiwix. All content is derived from the rc.majlis dataset and user contributions, with full text search and responsive design." \
  --creator="Contributors" \
  --publisher="GitHub Actions" \
  "$HTML_DIR" "$ZIM_FILE"

echo "ZIM_FILE=$ZIM_FILE" >> $GITHUB_ENV
