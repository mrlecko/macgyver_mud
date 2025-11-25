#!/usr/bin/env node

/**
 * Test-Driven Development for Silver Gauge Mathematics
 *
 * This tests the core Pythagorean means calculations and shape coefficients
 * to ensure the visualizer works correctly.
 */

// ============================================================================
// CORE MATHEMATICS (From scoring_silver.py)
// ============================================================================

function ensurePositive(x, eps = 1e-9) {
    return Math.max(0.0, parseFloat(x)) + eps;
}

function harmonicMean(a, b) {
    a = ensurePositive(a);
    b = ensurePositive(b);
    return 2.0 / (1.0 / a + 1.0 / b);
}

function geometricMean(a, b) {
    a = ensurePositive(a);
    b = ensurePositive(b);
    return Math.sqrt(a * b);
}

function arithmeticMean(a, b) {
    a = ensurePositive(a);
    b = ensurePositive(b);
    return 0.5 * (a + b);
}

/**
 * Build silver stamp for exploration (goal vs info)
 */
function calculateExploration(goal, info) {
    const g = ensurePositive(goal);
    const i = ensurePositive(info);

    const hm_gi = harmonicMean(g, i);
    const gm_gi = geometricMean(g, i);
    const am_gi = arithmeticMean(g, i);

    // k_explore measures balance between goal and info
    const k_explore = am_gi > 0 ? (gm_gi / am_gi) : 0.0;

    return {
        H: hm_gi,
        G: gm_gi,
        A: am_gi,
        k_explore: k_explore
    };
}

/**
 * Build silver stamp for efficiency (goal+info vs cost)
 */
function calculateEfficiency(goal, info, cost) {
    const g = ensurePositive(goal);
    const i = ensurePositive(info);
    const c = ensurePositive(cost);

    const g_plus_i = ensurePositive(g + i);

    const hm_gc = harmonicMean(g_plus_i, c);
    const gm_gc = geometricMean(g_plus_i, c);
    const am_gc = arithmeticMean(g_plus_i, c);

    const k_efficiency = am_gc > 0 ? (gm_gc / am_gc) : 0.0;

    return {
        H: hm_gc,
        G: gm_gc,
        A: am_gc,
        k_efficiency: k_efficiency
    };
}

/**
 * Interpret k_explore value
 * Fixed thresholds based on actual Pythagorean mean behavior
 */
function interpretKExplore(k) {
    if (k > 0.95) return "Perfectly Balanced (Generalist)";
    if (k > 0.90) return "Very Well Balanced";
    if (k > 0.80) return "Well-Balanced";
    if (k > 0.65) return "Moderately Balanced";
    if (k > 0.40) return "Specialist (Favors One Objective)";
    return "Extreme Specialist (One-Dimensional)";
}

// ============================================================================
// TEST SUITE
// ============================================================================

let testsPassed = 0;
let testsFailed = 0;

function assert(condition, message) {
    if (condition) {
        console.log(`✓ ${message}`);
        testsPassed++;
    } else {
        console.error(`✗ ${message}`);
        testsFailed++;
    }
}

function assertClose(actual, expected, tolerance, message) {
    const diff = Math.abs(actual - expected);
    if (diff < tolerance) {
        console.log(`✓ ${message} (${actual.toFixed(4)} ≈ ${expected.toFixed(4)})`);
        testsPassed++;
    } else {
        console.error(`✗ ${message} (${actual.toFixed(4)} != ${expected.toFixed(4)}, diff=${diff.toFixed(4)})`);
        testsFailed++;
    }
}

console.log("\n" + "=".repeat(70));
console.log("SILVER GAUGE MATHEMATICS TEST SUITE");
console.log("=".repeat(70) + "\n");

// ============================================================================
// TEST 1: Pythagorean Means Properties
// ============================================================================

console.log("TEST 1: Pythagorean Means Properties (H ≤ G ≤ A)");
console.log("-".repeat(70));

// Test with equal values (H = G = A)
const h1 = harmonicMean(5, 5);
const g1 = geometricMean(5, 5);
const a1 = arithmeticMean(5, 5);

assertClose(h1, 5.0, 0.001, "H(5,5) = 5.0");
assertClose(g1, 5.0, 0.001, "G(5,5) = 5.0");
assertClose(a1, 5.0, 0.001, "A(5,5) = 5.0");
assert(h1 <= g1 && g1 <= a1, "H ≤ G ≤ A for equal values");

// Test with unequal values (H < G < A)
const h2 = harmonicMean(1, 10);
const g2 = geometricMean(1, 10);
const a2 = arithmeticMean(1, 10);

console.log(`\nH(1,10) = ${h2.toFixed(4)}, G(1,10) = ${g2.toFixed(4)}, A(1,10) = ${a2.toFixed(4)}`);
assert(h2 < g2 && g2 < a2, "H < G < A for unequal values");
assertClose(h2, 1.818, 0.01, "H(1,10) ≈ 1.818 (2/(1/1 + 1/10) = 2/1.1)");
assertClose(g2, 3.162, 0.01, "G(1,10) ≈ 3.162 (√10)");
assertClose(a2, 5.5, 0.01, "A(1,10) = 5.5 ((1+10)/2)");

console.log("");

// ============================================================================
// TEST 2: k_explore Calculation
// ============================================================================

console.log("TEST 2: k_explore = G/A Shape Coefficient");
console.log("-".repeat(70));

// Perfect balance (goal = info)
const bal1 = calculateExploration(5, 5);
assertClose(bal1.k_explore, 1.0, 0.001, "k(5,5) = 1.0 (perfect balance)");

const bal2 = calculateExploration(7, 7);
assertClose(bal2.k_explore, 1.0, 0.001, "k(7,7) = 1.0 (perfect balance)");

// Extreme specialist (one value dominates)
const spec1 = calculateExploration(10, 1);
const expectedK1 = Math.sqrt(10 * 1) / ((10 + 1) / 2); // √10 / 5.5 ≈ 0.575
assertClose(spec1.k_explore, expectedK1, 0.01, `k(10,1) ≈ ${expectedK1.toFixed(3)} (specialist)`);

const spec2 = calculateExploration(1, 10);
const expectedK2 = Math.sqrt(1 * 10) / ((1 + 10) / 2); // √10 / 5.5 ≈ 0.575
assertClose(spec2.k_explore, expectedK2, 0.01, `k(1,10) ≈ ${expectedK2.toFixed(3)} (specialist)`);

// Moderate balance
const mod = calculateExploration(7, 3);
const expectedKmod = Math.sqrt(7 * 3) / ((7 + 3) / 2); // √21 / 5 ≈ 0.917
assertClose(mod.k_explore, expectedKmod, 0.01, `k(7,3) ≈ ${expectedKmod.toFixed(3)} (moderate)`);

console.log("");

// ============================================================================
// TEST 3: Preset Scenarios (The Bug Cases!)
// ============================================================================

console.log("TEST 3: Preset Scenarios (Bug Detection)");
console.log("-".repeat(70));

// Pure Explorer: goal=1, info=10, cost=2
console.log("\nPure Explorer (goal=1, info=10):");
const explorer = calculateExploration(1, 10);
console.log(`  H=${explorer.H.toFixed(3)}, G=${explorer.G.toFixed(3)}, A=${explorer.A.toFixed(3)}`);
console.log(`  k_explore = ${explorer.k_explore.toFixed(3)}`);
console.log(`  Interpretation: ${interpretKExplore(explorer.k_explore)}`);
assert(explorer.k_explore < 0.6, "Pure Explorer should be Specialist (k < 0.6)");
assert(interpretKExplore(explorer.k_explore).includes("Specialist"),
    "Pure Explorer interpretation should include 'Specialist'");

// Pure Exploiter: goal=10, info=1, cost=2
console.log("\nPure Exploiter (goal=10, info=1):");
const exploiter = calculateExploration(10, 1);
console.log(`  H=${exploiter.H.toFixed(3)}, G=${exploiter.G.toFixed(3)}, A=${exploiter.A.toFixed(3)}`);
console.log(`  k_explore = ${exploiter.k_explore.toFixed(3)}`);
console.log(`  Interpretation: ${interpretKExplore(exploiter.k_explore)}`);
assert(exploiter.k_explore < 0.6, "Pure Exploiter should be Specialist (k < 0.6)");
assert(interpretKExplore(exploiter.k_explore).includes("Specialist"),
    "Pure Exploiter interpretation should include 'Specialist'");

// Balanced Agent: goal=7, info=7, cost=3
console.log("\nBalanced Agent (goal=7, info=7):");
const balanced = calculateExploration(7, 7);
console.log(`  H=${balanced.H.toFixed(3)}, G=${balanced.G.toFixed(3)}, A=${balanced.A.toFixed(3)}`);
console.log(`  k_explore = ${balanced.k_explore.toFixed(3)}`);
console.log(`  Interpretation: ${interpretKExplore(balanced.k_explore)}`);
assert(balanced.k_explore > 0.95, "Balanced Agent should be Perfectly Balanced (k > 0.95)");
assert(interpretKExplore(balanced.k_explore).includes("Perfectly Balanced"),
    "Balanced Agent interpretation should include 'Perfectly Balanced'");

// Confused Agent: goal=0.5, info=0.5, cost=8
console.log("\nConfused Agent (goal=0.5, info=0.5):");
const confused = calculateExploration(0.5, 0.5);
console.log(`  H=${confused.H.toFixed(3)}, G=${confused.G.toFixed(3)}, A=${confused.A.toFixed(3)}`);
console.log(`  k_explore = ${confused.k_explore.toFixed(3)}`);
console.log(`  Interpretation: ${interpretKExplore(confused.k_explore)}`);
assert(confused.k_explore > 0.95, "Confused Agent (equal low values) should be Perfectly Balanced (k > 0.95)");

console.log("");

// ============================================================================
// TEST 4: The Bug Case - goal=0.6, info=9.2
// ============================================================================

console.log("TEST 4: Reported Bug Case (goal=0.6, info=9.2)");
console.log("-".repeat(70));

const bugCase = calculateExploration(0.6, 9.2);
console.log(`H=${bugCase.H.toFixed(3)}, G=${bugCase.G.toFixed(3)}, A=${bugCase.A.toFixed(3)}`);
console.log(`k_explore = ${bugCase.k_explore.toFixed(3)}`);
console.log(`Interpretation: ${interpretKExplore(bugCase.k_explore)}`);

// Calculate expected values manually
const expectedG = Math.sqrt(0.6 * 9.2); // ≈ 2.349
const expectedA = (0.6 + 9.2) / 2; // = 4.9
const expectedK = expectedG / expectedA; // ≈ 0.479

assertClose(bugCase.G, expectedG, 0.01, `G(0.6, 9.2) ≈ ${expectedG.toFixed(3)}`);
assertClose(bugCase.A, expectedA, 0.01, `A(0.6, 9.2) = ${expectedA.toFixed(3)}`);
assertClose(bugCase.k_explore, expectedK, 0.01, `k(0.6, 9.2) ≈ ${expectedK.toFixed(3)}`);

// k ≈ 0.479 should be "Specialist"
assert(bugCase.k_explore > 0.3 && bugCase.k_explore < 0.5,
    "k ≈ 0.479 should be in Specialist range (0.3 < k < 0.5)");
assert(interpretKExplore(bugCase.k_explore).includes("Specialist"),
    "Interpretation should be 'Specialist'");

console.log("");

// ============================================================================
// TEST 5: Gauge Position Calculation
// ============================================================================

console.log("TEST 5: Gauge Indicator Position");
console.log("-".repeat(70));

function calculateGaugePosition(k) {
    // Gauge goes from 0.0 (left) to 1.0 (right)
    // Position as percentage
    return k * 100;
}

// Test gauge positions
const gaugeBalanced = calculateGaugePosition(balanced.k_explore);
const gaugeExplorer = calculateGaugePosition(explorer.k_explore);
const gaugeBugCase = calculateGaugePosition(bugCase.k_explore);

console.log(`Balanced (k=1.0) → gauge at ${gaugeBalanced.toFixed(1)}% (should be ~100%)`);
console.log(`Explorer (k=${explorer.k_explore.toFixed(3)}) → gauge at ${gaugeExplorer.toFixed(1)}% (should be ~57%)`);
console.log(`Bug case (k=${bugCase.k_explore.toFixed(3)}) → gauge at ${gaugeBugCase.toFixed(1)}% (should be ~48%)`);

assertClose(gaugeBalanced, 100, 1, "Balanced gauge should be at 100%");
assertClose(gaugeExplorer, 57.5, 5, "Explorer gauge should be around 57%");
assertClose(gaugeBugCase, 48, 5, "Bug case gauge should be around 48%");

console.log("");

// ============================================================================
// TEST 6: Edge Cases
// ============================================================================

console.log("TEST 6: Edge Cases");
console.log("-".repeat(70));

// Zero values (with epsilon handling)
const zero1 = calculateExploration(0, 0);
console.log(`k(0,0) = ${zero1.k_explore.toFixed(3)}`);
assert(!isNaN(zero1.k_explore), "k(0,0) should not be NaN");

const zero2 = calculateExploration(0, 5);
console.log(`k(0,5) = ${zero2.k_explore.toFixed(3)}`);
assert(!isNaN(zero2.k_explore), "k(0,5) should not be NaN");

// Very small values
const tiny = calculateExploration(0.001, 0.001);
console.log(`k(0.001, 0.001) = ${tiny.k_explore.toFixed(3)}`);
assertClose(tiny.k_explore, 1.0, 0.01, "k(tiny, tiny) should be ≈ 1.0");

// Very large values
const large = calculateExploration(1000, 1000);
console.log(`k(1000, 1000) = ${large.k_explore.toFixed(3)}`);
assertClose(large.k_explore, 1.0, 0.01, "k(large, large) should be ≈ 1.0");

console.log("");

// ============================================================================
// SUMMARY
// ============================================================================

console.log("=".repeat(70));
console.log("TEST SUMMARY");
console.log("=".repeat(70));
console.log(`Tests passed: ${testsPassed}`);
console.log(`Tests failed: ${testsFailed}`);
console.log(`Total tests: ${testsPassed + testsFailed}`);

if (testsFailed === 0) {
    console.log("\n✓ ALL TESTS PASSED\n");
    process.exit(0);
} else {
    console.log(`\n✗ ${testsFailed} TEST(S) FAILED\n`);
    process.exit(1);
}
