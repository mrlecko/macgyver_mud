# Silver Gauge Interactive Visualizer: Implementation Plan

**Goal:** Create a beautiful, interactive web-based visualization that demonstrates the Silver Gauge geometric scoring method.

**Tech Stack:** Vanilla JavaScript + HTML5 + CSS3 (no frameworks, max portability)

**Target Audience:** Recruiters, researchers, and engineers who want to understand the innovation without reading code.

---

## Vision: What the User Will See

### Landing View

A clean, modern single-page app showing:

1. **Interactive Sliders** (left panel)
   - Goal Value: 0 → 10
   - Info Gain: 0 → 10
   - Cost: 0 → 10

2. **Real-time Visualization** (center panel)
   - **Geometric Triangle**: Shows H, G, A as points on a line
   - **Shape Coefficient Gauge**: Visual meter for k_explore
   - **Animated Comparison**: Side-by-side scalar vs. geometric scoring

3. **Live Calculations** (right panel)
   - All Pythagorean means computed
   - Shape coefficients displayed
   - Interpretation text (e.g., "Highly Balanced" vs. "Specialist")

4. **Example Scenarios** (bottom)
   - Preset buttons: "Pure Explorer", "Pure Exploiter", "Balanced Agent", "Confused Agent"

---

## Technical Architecture

### File Structure

```
docs/demos/
├── silver_gauge_visualizer.html    # Main file (everything in one HTML)
├── README_VISUALIZER.md            # How to use the visualizer
└── assets/                         # (optional) for production version
    ├── style.css
    ├── visualizer.js
    └── pythagorean_math.js
```

**Decision:** Start with a single-file HTML (easier to distribute), then optionally split for production.

---

## Component Breakdown

### 1. HTML Structure

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Silver Gauge: Geometric Decision Analysis</title>
    <style>
        /* Embedded CSS - modern, clean design */
    </style>
</head>
<body>
    <!-- Header -->
    <header>
        <h1>🥈 The Silver Gauge</h1>
        <p>Geometric Analysis of Multi-Objective Decision Making</p>
    </header>

    <!-- Main Grid Layout -->
    <div class="container">
        <!-- Left Panel: Controls -->
        <section class="controls-panel">
            <h2>Input Values</h2>
            <!-- Sliders for Goal, Info, Cost -->
        </section>

        <!-- Center Panel: Visualizations -->
        <section class="visualization-panel">
            <h2>Geometric Representation</h2>
            <!-- Canvas or SVG for visualizations -->
        </section>

        <!-- Right Panel: Calculations -->
        <section class="results-panel">
            <h2>Computed Values</h2>
            <!-- Live calculated values -->
        </section>
    </div>

    <!-- Bottom Panel: Presets -->
    <section class="presets-panel">
        <h2>Example Scenarios</h2>
        <!-- Preset buttons -->
    </section>

    <!-- Footer -->
    <footer>
        <p>Part of the MacGyver MUD cognitive architecture</p>
        <a href="../../README.md">View Project</a>
    </footer>

    <script>
        /* Embedded JavaScript */
    </script>
</body>
</html>
```

---

### 2. Visual Components

#### A. Pythagorean Means Triangle (SVG)

**What it shows:** Visual representation of H ≤ G ≤ A inequality

```
     A (Arithmetic Mean)
      *
     /|\
    / | \
   /  G  \     G (Geometric Mean)
  /   *   \
 /    |    \
*-----H-----*   H (Harmonic Mean)
```

**Implementation:**
- Use SVG `<line>` elements for axes
- Animate points when sliders change
- Color-code: H (red), G (yellow), A (green)
- Show distance between points as visual indicator of balance

---

#### B. Shape Coefficient Gauge

**What it shows:** k_explore value as a meter (0.0 → 1.0)

```
 SPECIALIST                    BALANCED
     ├────────────┼────────────┤
     0.0         0.5          1.0
              ↑
         (current k)
```

**Implementation:**
- HTML5 `<meter>` element styled with CSS
- Color gradient: red (0) → yellow (0.5) → green (1.0)
- Live update as sliders move

---

#### C. Decision Space Plot (Canvas)

**What it shows:** How decisions map in (goal, info) space with color-coded k_explore

**Implementation:**
- HTML5 Canvas for performance
- Plot current decision as a point
- Show past decisions as fading trail
- Color points by k_explore value

```
Info Gain
    ^
 10 |     . (Balanced, k=0.8)
    |   .
  5 |  *  (Current decision)
    | .
  0 +---------------------> Goal Value
    0    5              10
```

---

#### D. Comparative Visualization

**What it shows:** Side-by-side comparison of scalar vs. geometric scoring

```
┌─────────────────┬─────────────────┐
│ Scalar Scoring  │ Geometric       │
│                 │ Scoring         │
│ Total: 8.5      │ k_explore: 0.75 │
│                 │ k_efficiency:   │
│ ■■■■■■■■░░      │ 0.82            │
│                 │                 │
│ Interpretation: │ Interpretation: │
│ "High score"    │ "Balanced       │
│                 │  explorer"      │
└─────────────────┴─────────────────┘
```

---

### 3. JavaScript Logic

#### Core Math Module

```javascript
// Pythagorean Means
function harmonicMean(a, b) {
    if (a <= 0 || b <= 0) return 0;
    return (2 * a * b) / (a + b);
}

function geometricMean(a, b) {
    if (a < 0 || b < 0) return 0;
    return Math.sqrt(a * b);
}

function arithmeticMean(a, b) {
    return (a + b) / 2;
}

// Shape Coefficient
function calculateKExplore(goal, info) {
    const H = harmonicMean(goal, info);
    const G = geometricMean(goal, info);
    const A = arithmeticMean(goal, info);

    const k = (A > 0) ? (G / A) : 0;
    return {
        H: H,
        G: G,
        A: A,
        k_explore: k
    };
}

function calculateKEfficiency(goal, info, cost) {
    const benefit = goal + info;
    const H = harmonicMean(benefit, cost);
    const G = geometricMean(benefit, cost);
    const A = arithmeticMean(benefit, cost);

    const k = (A > 0) ? (G / A) : 0;
    return {
        H: H,
        G: G,
        A: A,
        k_efficiency: k
    };
}

// Interpretation
function interpretKExplore(k) {
    if (k > 0.95) return "Perfectly Balanced (Generalist)";
    if (k > 0.8) return "Well-Balanced Explorer";
    if (k > 0.6) return "Moderately Balanced";
    if (k > 0.4) return "Specialist (Favors One Objective)";
    return "Extreme Specialist (One-Dimensional)";
}
```

---

#### Visualization Update Loop

```javascript
let state = {
    goal: 5,
    info: 5,
    cost: 2,
    history: [] // Track past decisions
};

function updateVisualization() {
    // 1. Calculate all metrics
    const explore = calculateKExplore(state.goal, state.info);
    const efficiency = calculateKEfficiency(state.goal, state.info, state.cost);

    // 2. Update DOM elements
    document.getElementById('hm-value').textContent = explore.H.toFixed(2);
    document.getElementById('gm-value').textContent = explore.G.toFixed(2);
    document.getElementById('am-value').textContent = explore.A.toFixed(2);
    document.getElementById('k-explore').textContent = explore.k_explore.toFixed(3);

    // 3. Update visualization components
    updateTriangle(explore.H, explore.G, explore.A);
    updateGauge(explore.k_explore);
    updateDecisionPlot(state.goal, state.info, explore.k_explore);

    // 4. Update interpretation
    document.getElementById('interpretation').textContent =
        interpretKExplore(explore.k_explore);

    // 5. Add to history (for trail effect)
    state.history.push({
        goal: state.goal,
        info: state.info,
        k: explore.k_explore,
        timestamp: Date.now()
    });

    // Keep only last 50 points
    if (state.history.length > 50) {
        state.history.shift();
    }
}

// Event listeners for sliders
document.getElementById('goal-slider').addEventListener('input', (e) => {
    state.goal = parseFloat(e.target.value);
    updateVisualization();
});

document.getElementById('info-slider').addEventListener('input', (e) => {
    state.info = parseFloat(e.target.value);
    updateVisualization();
});

document.getElementById('cost-slider').addEventListener('input', (e) => {
    state.cost = parseFloat(e.target.value);
    updateVisualization();
});
```

---

### 4. Example Presets

**Button 1: "Pure Explorer"**
```javascript
function setPureExplorer() {
    state = { goal: 1, info: 10, cost: 2 };
    updateSliders();
    updateVisualization();
}
// Result: k_explore ≈ 0.32 (Specialist in information)
```

**Button 2: "Pure Exploiter"**
```javascript
function setPureExploiter() {
    state = { goal: 10, info: 1, cost: 2 };
    updateSliders();
    updateVisualization();
}
// Result: k_explore ≈ 0.32 (Specialist in goal)
```

**Button 3: "Balanced Agent"**
```javascript
function setBalanced() {
    state = { goal: 7, info: 7, cost: 3 };
    updateSliders();
    updateVisualization();
}
// Result: k_explore ≈ 1.0 (Perfectly balanced)
```

**Button 4: "Confused Agent"**
```javascript
function setConfused() {
    state = { goal: 0.5, info: 0.5, cost: 8 };
    updateSliders();
    updateVisualization();
}
// Result: Low values, high cost, poor efficiency
```

**Button 5: "PANIC Protocol"**
```javascript
function setPanicMode() {
    // Simulate high entropy state
    state = { goal: 3, info: 10, cost: 1 };
    updateSliders();
    updateVisualization();
    highlightInterpretation("PANIC mode: Maximize robustness (high info seeking)");
}
// Shows why PANIC increases info-seeking
```

---

### 5. CSS Styling (Modern, Professional)

```css
:root {
    --primary: #2563eb;     /* Blue */
    --secondary: #7c3aed;   /* Purple */
    --success: #10b981;     /* Green */
    --warning: #f59e0b;     /* Orange */
    --danger: #ef4444;      /* Red */
    --bg: #f9fafb;          /* Light gray */
    --text: #1f2937;        /* Dark gray */
    --border: #e5e7eb;      /* Border gray */
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.6;
}

header {
    background: linear-gradient(135deg, var(--primary), var(--secondary));
    color: white;
    padding: 2rem;
    text-align: center;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

.container {
    display: grid;
    grid-template-columns: 1fr 2fr 1fr;
    gap: 2rem;
    max-width: 1400px;
    margin: 2rem auto;
    padding: 0 2rem;
}

.controls-panel,
.visualization-panel,
.results-panel {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

/* Sliders */
input[type="range"] {
    width: 100%;
    height: 8px;
    border-radius: 4px;
    background: var(--border);
    outline: none;
    -webkit-appearance: none;
}

input[type="range"]::-webkit-slider-thumb {
    -webkit-appearance: none;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: var(--primary);
    cursor: pointer;
}

/* Gauge */
.gauge {
    width: 100%;
    height: 40px;
    background: linear-gradient(to right,
        var(--danger) 0%,
        var(--warning) 50%,
        var(--success) 100%);
    border-radius: 20px;
    position: relative;
    margin: 1rem 0;
}

.gauge-indicator {
    position: absolute;
    top: -10px;
    width: 4px;
    height: 60px;
    background: white;
    border: 2px solid var(--text);
    transition: left 0.3s ease;
}

/* Preset buttons */
.preset-btn {
    padding: 0.75rem 1.5rem;
    margin: 0.5rem;
    border: 2px solid var(--primary);
    background: white;
    color: var(--primary);
    border-radius: 8px;
    cursor: pointer;
    font-weight: 600;
    transition: all 0.2s;
}

.preset-btn:hover {
    background: var(--primary);
    color: white;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
}

/* Animations */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

.visualization-panel > * {
    animation: fadeIn 0.5s ease;
}

/* Responsive */
@media (max-width: 1024px) {
    .container {
        grid-template-columns: 1fr;
    }
}
```

---

## Implementation Phases

### Phase 1: Core Functionality (MVP)
**Time:** 4-6 hours

- [ ] Basic HTML structure
- [ ] Slider controls for goal, info, cost
- [ ] Core math functions (H, G, A, k_explore)
- [ ] Live text display of calculated values
- [ ] Simple interpretation text
- [ ] 4 preset buttons

**Deliverable:** Functional but plain visualizer

---

### Phase 2: Visual Enhancements
**Time:** 3-4 hours

- [ ] Pythagorean means triangle (SVG)
- [ ] Animated gauge for k_explore
- [ ] CSS styling (modern, professional)
- [ ] Smooth transitions on value changes
- [ ] Responsive design

**Deliverable:** Beautiful visualizer

---

### Phase 3: Advanced Features
**Time:** 2-3 hours

- [ ] Decision space plot (Canvas)
- [ ] Historical trail (show past 50 decisions)
- [ ] Comparison view (scalar vs geometric)
- [ ] Export button (save as PNG or share link)
- [ ] Tutorial overlay (first-time user guide)

**Deliverable:** Production-ready visualizer

---

### Phase 4: Polish & Documentation
**Time:** 1-2 hours

- [ ] Add tooltips explaining each component
- [ ] Write README_VISUALIZER.md
- [ ] Add comments in code
- [ ] Test on mobile devices
- [ ] Optimize performance

**Deliverable:** Fully documented, polished demo

---

## Starter Template (Minimal Working Version)

Save this as `docs/demos/silver_gauge_visualizer.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Silver Gauge Visualizer</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .slider-group {
            margin: 20px 0;
        }
        input[type="range"] {
            width: 100%;
        }
        .results {
            background: #f0f9ff;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }
        .value {
            font-size: 24px;
            font-weight: bold;
            color: #2563eb;
        }
        .interpretation {
            font-size: 18px;
            color: #059669;
            margin-top: 10px;
        }
        button {
            padding: 10px 20px;
            margin: 5px;
            border: none;
            background: #2563eb;
            color: white;
            border-radius: 5px;
            cursor: pointer;
        }
        button:hover {
            background: #1d4ed8;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🥈 Silver Gauge Visualizer</h1>
        <p>Interactive demonstration of geometric decision analysis</p>

        <div class="slider-group">
            <label>Goal Value: <span id="goal-display">5.0</span></label>
            <input type="range" id="goal-slider" min="0" max="10" step="0.1" value="5">
        </div>

        <div class="slider-group">
            <label>Info Gain: <span id="info-display">5.0</span></label>
            <input type="range" id="info-slider" min="0" max="10" step="0.1" value="5">
        </div>

        <div class="slider-group">
            <label>Cost: <span id="cost-display">2.0</span></label>
            <input type="range" id="cost-slider" min="0" max="10" step="0.1" value="2">
        </div>

        <div class="results">
            <h2>Pythagorean Means</h2>
            <p>Harmonic Mean (H): <span class="value" id="hm">0.00</span></p>
            <p>Geometric Mean (G): <span class="value" id="gm">0.00</span></p>
            <p>Arithmetic Mean (A): <span class="value" id="am">0.00</span></p>

            <h2 style="margin-top: 20px;">Shape Coefficient</h2>
            <p>k_explore (G/A): <span class="value" id="k-explore">0.00</span></p>
            <p class="interpretation" id="interpretation">Balanced</p>
        </div>

        <h3>Example Scenarios</h3>
        <button onclick="setPureExplorer()">Pure Explorer</button>
        <button onclick="setPureExploiter()">Pure Exploiter</button>
        <button onclick="setBalanced()">Balanced Agent</button>
        <button onclick="setConfused()">Confused Agent</button>
    </div>

    <script>
        // Math functions
        function harmonicMean(a, b) {
            if (a <= 0 || b <= 0) return 0;
            return (2 * a * b) / (a + b);
        }

        function geometricMean(a, b) {
            if (a < 0 || b < 0) return 0;
            return Math.sqrt(a * b);
        }

        function arithmeticMean(a, b) {
            return (a + b) / 2;
        }

        function interpretK(k) {
            if (k > 0.95) return "Perfectly Balanced (Generalist)";
            if (k > 0.8) return "Well-Balanced";
            if (k > 0.6) return "Moderately Balanced";
            if (k > 0.4) return "Specialist";
            return "Extreme Specialist";
        }

        // State
        let state = { goal: 5, info: 5, cost: 2 };

        // Update function
        function update() {
            const g = state.goal;
            const i = state.info;

            const H = harmonicMean(g, i);
            const G = geometricMean(g, i);
            const A = arithmeticMean(g, i);
            const k = (A > 0) ? (G / A) : 0;

            document.getElementById('hm').textContent = H.toFixed(2);
            document.getElementById('gm').textContent = G.toFixed(2);
            document.getElementById('am').textContent = A.toFixed(2);
            document.getElementById('k-explore').textContent = k.toFixed(3);
            document.getElementById('interpretation').textContent = interpretK(k);

            document.getElementById('goal-display').textContent = g.toFixed(1);
            document.getElementById('info-display').textContent = i.toFixed(1);
            document.getElementById('cost-display').textContent = state.cost.toFixed(1);
        }

        // Event listeners
        document.getElementById('goal-slider').addEventListener('input', (e) => {
            state.goal = parseFloat(e.target.value);
            update();
        });

        document.getElementById('info-slider').addEventListener('input', (e) => {
            state.info = parseFloat(e.target.value);
            update();
        });

        document.getElementById('cost-slider').addEventListener('input', (e) => {
            state.cost = parseFloat(e.target.value);
            update();
        });

        // Presets
        function setPureExplorer() {
            state = { goal: 1, info: 10, cost: 2 };
            syncSliders();
            update();
        }

        function setPureExploiter() {
            state = { goal: 10, info: 1, cost: 2 };
            syncSliders();
            update();
        }

        function setBalanced() {
            state = { goal: 7, info: 7, cost: 3 };
            syncSliders();
            update();
        }

        function setConfused() {
            state = { goal: 0.5, info: 0.5, cost: 8 };
            syncSliders();
            update();
        }

        function syncSliders() {
            document.getElementById('goal-slider').value = state.goal;
            document.getElementById('info-slider').value = state.info;
            document.getElementById('cost-slider').value = state.cost;
        }

        // Initial update
        update();
    </script>
</body>
</html>
```

---

## Next Steps

1. **Create MVP** (copy starter template above)
2. **Test locally** (open HTML file in browser)
3. **Enhance visually** (add SVG triangle, gauge)
4. **Add advanced features** (Canvas plot, history)
5. **Document** (README_VISUALIZER.md)
6. **Link from main README** (already done!)

---

## Success Metrics

The visualizer is successful if:

- [ ] A non-technical person can understand k_explore in < 2 minutes
- [ ] Recruiters can see the innovation without reading code
- [ ] Researchers can experiment with different values interactively
- [ ] File size < 100KB (single HTML file)
- [ ] Works on mobile browsers
- [ ] Loads instantly (no dependencies)

---

**Estimated Total Time:** 10-15 hours for full implementation

**MVP Time:** 4-6 hours (using starter template)

---

That's the complete plan! The starter template is ready to use right now. Just save it as `docs/demos/silver_gauge_visualizer.html` and open in a browser.
