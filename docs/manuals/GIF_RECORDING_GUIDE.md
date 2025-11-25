# How to Create Demo GIFs for MacGyver MUD

**Goal:** Create professional animated GIFs showing the agent in action for the README.

**Primary Target:** Honey Pot escape demonstration (shows meta-cognition in action)

---

## Method 1: Using asciinema + agg (Recommended)

**Pros:** High quality, programmable, works on all platforms
**Cons:** Requires two tools

### Step 1: Install Tools (One-time setup)

#### Install asciinema (Terminal Recorder)

**On macOS:**
```bash
brew install asciinema
```

**On Ubuntu/Debian:**
```bash
sudo apt-add-repository ppa:zanchey/asciinema
sudo apt-get update
sudo apt-get install asciinema
```

**On other Linux:**
```bash
pip3 install asciinema
```

#### Install agg (asciinema to GIF converter)

**All platforms (using Cargo/Rust):**
```bash
# Install Rust if you don't have it
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env

# Install agg
cargo install --git https://github.com/asciinema/agg
```

**Alternative (pre-built binaries):**
Download from: https://github.com/asciinema/agg/releases

---

### Step 2: Record the Demo

#### 2a. Prepare Environment

```bash
# Make sure you're in project root
cd /home/juancho/macgyver_mud

# Activate virtual environment
source venv/bin/activate

# Make sure Neo4j is running
make neo4j-start

# Wait for Neo4j to be ready
sleep 10
```

#### 2b. Clear Terminal & Set Size

```bash
# Clear any previous output
clear

# Set terminal to optimal size for GIF
# 80 columns x 24 rows is classic, but we need more vertical space
# Recommended: 100 columns x 30 rows
resize -s 30 100  # On Linux
# OR manually resize your terminal window to ~100x30
```

#### 2c. Record the Honey Pot Demo

```bash
# Start recording
asciinema rec honey_pot_demo.cast --overwrite

# You should see: "asciinema: recording asciicast to honey_pot_demo.cast"
# Your terminal is now being recorded!

# Run the demo
make demo-critical

# Wait for demo to complete (should take ~5-10 seconds)

# Stop recording: Press Ctrl+D or type 'exit'
exit
```

**What gets recorded:**
- All terminal output from `make demo-critical`
- Timing information (so the GIF plays at the right speed)

---

### Step 3: Convert to GIF

```bash
# Basic conversion (default settings)
agg honey_pot_demo.cast honey_pot_escape.gif

# Recommended settings for README (slower playback, better readability)
agg --speed 0.5 --font-size 14 honey_pot_demo.cast honey_pot_escape.gif

# High-quality settings (larger file, crystal clear)
agg --speed 0.5 --font-size 16 --cols 100 --rows 30 \
    honey_pot_demo.cast honey_pot_escape_hq.gif
```

**agg parameters explained:**
- `--speed 0.5` — Play at 50% speed (easier to read)
- `--font-size 14` — Bigger font for README viewing
- `--cols 100 --rows 30` — Exact terminal dimensions
- `--theme monokai` — Optional: choose color theme

**Available themes:**
```bash
agg --list-themes
# Output: asciinema, dracula, monokai, solarized-dark, solarized-light, nord, etc.
```

---

### Step 4: Optimize GIF Size (Optional but Recommended)

GIFs can be large. Optimize for web:

#### Using gifsicle (Best compression)

```bash
# Install gifsicle
# macOS:
brew install gifsicle

# Ubuntu/Debian:
sudo apt-get install gifsicle

# Optimize (lossy compression, ~50% size reduction)
gifsicle -O3 --lossy=80 honey_pot_escape.gif -o honey_pot_escape_optimized.gif

# Rename
mv honey_pot_escape_optimized.gif honey_pot_escape.gif
```

#### Using imagemagick (Alternative)

```bash
# Install imagemagick
# macOS:
brew install imagemagick

# Ubuntu/Debian:
sudo apt-get install imagemagick

# Optimize
convert honey_pot_escape.gif -fuzz 10% -layers Optimize honey_pot_escape_optimized.gif
```

---

### Step 5: Place GIF in Project

```bash
# Create demos directory if it doesn't exist
mkdir -p docs/demos

# Move the GIF
mv honey_pot_escape.gif docs/demos/

# Verify it works
open docs/demos/honey_pot_escape.gif  # macOS
xdg-open docs/demos/honey_pot_escape.gif  # Linux
```

---

## Method 2: Using Terminalizer (Alternative)

**Pros:** Simple, one tool
**Cons:** Slower, produces larger files

### Install

```bash
npm install -g terminalizer
```

### Record

```bash
# Initialize config
terminalizer init honey_pot

# Edit honey_pot.yml to set:
# - cols: 100
# - rows: 30
# - quality: 100

# Record
terminalizer record honey_pot --config honey_pot.yml

# Run your demo
make demo-critical

# Stop: Ctrl+D

# Render to GIF
terminalizer render honey_pot
```

---

## Method 3: Using ttygif (Lightweight)

**Pros:** Simple
**Cons:** macOS only, basic features

```bash
# Install
brew install ttygif

# Record
ttyrec myrecording

# Run demo
make demo-critical

# Exit
exit

# Convert
ttygif myrecording
```

---

## What to Record: Demo Scripts

### Demo 1: Honey Pot Escape (PRIMARY - for README)

**Command:**
```bash
make demo-critical
```

**Duration:** ~10 seconds
**Shows:** DEADLOCK detection and escape

**Key frames to capture:**
- Agent stuck in loop (A→B→A→B)
- ⚠️ CRITICAL STATE DETECTED message
- Protocol activation (SISYPHUS)
- Successful escape

**Expected output to record:**
```
═══════════════════════════════════════════════════════════
CRITICAL STATE DEMO: Honey Pot Escape
═══════════════════════════════════════════════════════════

Testing agent on HONEY_POT scenario...
...
✓ ESCAPED (4 steps)
```

---

### Demo 2: Full Test Suite (SECONDARY - for docs)

**Command:**
```bash
make test-full
```

**Duration:** ~30 seconds (too long for README, good for docs)

**Shows:** All 392 tests passing

**Optimization:** Speed up playback
```bash
agg --speed 2.0 test_suite.cast test_suite.gif
```

---

### Demo 3: Episodic Memory (SECONDARY - for advanced docs)

**Command:**
```bash
python3 validation/episodic_replay_demo.py
```

**Duration:** ~15 seconds

**Shows:** Counterfactual generation and regret analysis

---

### Demo 4: Silver Gauge Scoring (ADVANCED - for blog post)

**Command:**
```bash
make demo-silver
```

**Duration:** ~8 seconds

**Shows:** Geometric analysis in action (k_explore calculations)

---

## Pro Tips for Great GIFs

### 1. Clean Output
```bash
# Before recording, clear any clutter
clear

# Disable shell prompt customization that might look messy
export PS1='$ '
```

### 2. Slow Down Fast Output
```bash
# If demo runs too fast, add delays in the script
# Or use agg --speed to slow playback
agg --speed 0.3 demo.cast demo.gif  # 30% speed = very slow
```

### 3. Add Pauses for Readability
```bash
# Edit the .cast file to add pauses at key moments
# Open honey_pot_demo.cast in a text editor
# Each line is: [timestamp, "o", "text"]
# Insert pause by duplicating timestamp:
# [5.0, "o", "Key moment\n"]
# [7.0, "o", ""]  # 2-second pause
```

### 4. Highlight Important Sections
```bash
# Use ANSI colors in demo output to draw attention
# The demo already uses colors, but you can enhance:
echo -e "\033[1;31mIMPORTANT\033[0m"  # Red bold
echo -e "\033[1;32m✓ SUCCESS\033[0m"  # Green bold
```

### 5. Loop the GIF
```bash
# Make GIF loop forever (default in agg)
# To disable looping:
agg --loop 0 demo.cast demo.gif  # Play once then stop
```

---

## Recommended Final GIF Settings

For the **primary README GIF** (Honey Pot escape):

```bash
# Record
asciinema rec honey_pot.cast --overwrite -c "make demo-critical"

# Convert with optimal settings
agg \
  --speed 0.5 \
  --font-size 14 \
  --theme monokai \
  --cols 100 \
  --rows 30 \
  honey_pot.cast \
  docs/demos/honey_pot_escape.gif

# Optimize
gifsicle -O3 --lossy=80 \
  docs/demos/honey_pot_escape.gif \
  -o docs/demos/honey_pot_escape.gif
```

**Target specs:**
- **Size:** < 2MB (GitHub README optimal)
- **Dimensions:** 100x30 characters
- **Duration:** 8-12 seconds
- **FPS:** 10-15 (handled automatically by agg)
- **Loop:** Infinite

---

## Troubleshooting

### GIF too large (> 5MB)
```bash
# Reduce font size
agg --font-size 12 demo.cast demo.gif

# Reduce colors
gifsicle --colors 256 demo.gif -o demo.gif

# Crop unnecessary rows
agg --rows 25 demo.cast demo.gif  # Instead of 30
```

### GIF too fast to read
```bash
# Slow down significantly
agg --speed 0.3 demo.cast demo.gif
```

### Terminal colors look wrong
```bash
# Try different theme
agg --theme dracula demo.cast demo.gif
agg --theme solarized-dark demo.cast demo.gif
```

### Recording includes mistakes
```bash
# Just re-record! It's fast
asciinema rec demo.cast --overwrite
```

### agg not found after install
```bash
# Add Cargo bin to PATH
echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Or use full path
~/.cargo/bin/agg demo.cast demo.gif
```

---

## Checklist: Creating the Perfect Demo GIF

- [ ] Neo4j is running (`docker ps | grep neo4j`)
- [ ] Virtual environment activated (`source venv/bin/activate`)
- [ ] Terminal size set to 100x30 (`resize -s 30 100`)
- [ ] Terminal cleared (`clear`)
- [ ] Simple prompt set (`export PS1='$ '`)
- [ ] Recording started (`asciinema rec demo.cast --overwrite`)
- [ ] Demo executed (`make demo-critical`)
- [ ] Recording stopped (Ctrl+D)
- [ ] Converted to GIF with good settings (`agg --speed 0.5 --font-size 14`)
- [ ] Optimized for size (`gifsicle -O3 --lossy=80`)
- [ ] Placed in docs/demos/
- [ ] Tested in README preview
- [ ] File size < 2MB
- [ ] GIF loops smoothly

---

## Quick Reference Commands

```bash
# Complete workflow (one-liner for each demo)

# Honey Pot Demo:
asciinema rec -c "make demo-critical" honey_pot.cast --overwrite && \
agg --speed 0.5 --font-size 14 honey_pot.cast docs/demos/honey_pot_escape.gif && \
gifsicle -O3 --lossy=80 docs/demos/honey_pot_escape.gif -o docs/demos/honey_pot_escape.gif

# Test Suite Demo:
asciinema rec -c "make test-full" tests.cast --overwrite && \
agg --speed 2.0 --font-size 12 tests.cast docs/demos/test_suite.gif

# Episodic Memory Demo:
asciinema rec -c "python3 validation/episodic_replay_demo.py" episodic.cast --overwrite && \
agg --speed 0.5 --font-size 14 episodic.cast docs/demos/episodic_memory.gif
```

---

## Expected File Sizes

| Demo | Unoptimized | Optimized | Target |
|------|-------------|-----------|--------|
| Honey Pot (10s) | ~3MB | ~1.2MB | < 2MB |
| Test Suite (30s) | ~8MB | ~3MB | < 5MB |
| Episodic (15s) | ~4MB | ~1.5MB | < 3MB |

---

**That's it!** You now have everything you need to create professional demo GIFs.

**Questions?** Email: mrlecko@gmail.com
