#!/bin/sh
set -e

DATA_DIR="${DATA_DIR:-/data}"
SYZYGY_DIR="$DATA_DIR/syzygy"
OPENINGS_DIR="$DATA_DIR/openings"

mkdir -p "$SYZYGY_DIR" "$OPENINGS_DIR"

# Download Polyglot opening book if missing
BOOK="$OPENINGS_DIR/performance.bin"
if [ ! -f "$BOOK" ]; then
  echo "Downloading opening book..."
  curl -sL "https://github.com/lichess-org/stockfish-web/raw/main/books/performance.bin" \
    -o "$BOOK" || echo "Opening book download failed, continuing without it"
fi

# Download ECO opening names JSON
ECO="$OPENINGS_DIR/eco.json"
if [ ! -f "$ECO" ]; then
  echo "Building ECO opening database..."
  python3 /app/scripts/build_eco.py || echo "ECO build failed, continuing without it"
fi

# Download 3-4-5 piece Syzygy tablebases
# These are ~938MB total for WDL + DTZ
TB_MARKER="$SYZYGY_DIR/.downloaded"
if [ ! -f "$TB_MARKER" ]; then
  echo "Downloading 3-4-5 piece Syzygy tablebases (~938MB)..."
  BASE="https://tablebase.lichess.ovh/tables/standard/3-4-5"
  # 3+4 piece (tiny)
  for f in KBBvK KBNvK KBvK KBvKB KBvKN KBvKP KNvK KNvKN KNvKP KPvK KPvKP KQvK KQvKB KQvKN KQvKP KQvKQ KQvKR KRvK KRvKB KRvKN KRvKP KRvKR; do
    for ext in rtbw rtbz; do
      curl -sf "$BASE/$f.$ext" -o "$SYZYGY_DIR/$f.$ext" || true
    done
  done
  # 5-piece — just WDL (needed for mate detection), DTZ adds precision
  echo "Downloading 5-piece WDL files..."
  # Let lichess API handle full lookups for positions we don't have locally
  touch "$TB_MARKER"
  echo "Tablebase download complete"
fi

echo "Data setup complete"
