# Continued Fractions: Rationality Detector for AI Policies

> **Ancient Wisdom:** Any real number as a nested fraction  
> **Modern Application:** Policy complexity and interpretability measure  
> **Status:** Medium-value theoretical tool

---

## I. Historical & Mathematical Foundation

### 1.1 Discovery

**Ancient Origins:** Known to Euclid (~300 BCE) for finding GCD

**Modern Theory:** Developed by Euler, Lagrange (1700s)

**Definition:**
$$x = a_0 + \cfrac{1}{a_1 + \cfrac{1}{a_2 + \cfrac{1}{a_3 + \cdots}}}$$

Notation: $x = [a_0; a_1, a_2, a_3, ...]$

### 1.2 Key Properties

**Rational Numbers:** Finite continued fractions
- Example: 3.75 = [3; 1, 3]

**Irrational Numbers:** Infinite continued fractions  
- π = [3; 7, 15, 1, 292, 1, 1, ...]
- φ = [1; 1, 1, 1, 1, ...] (most irrational)  
- √2 = [1; 2, 2, 2, 2, ...] (periodic)

**Approximation Quality:**
Truncating a continued fraction gives the best rational approximation for a given denominator size.

**Irrationality Measure:**
The depth and

 size of coefficients measure how "irrational" a number is.

---

## II. AI Application Design

### 2.1 The Core Insight

**Problem:** How do you measure the "complexity" of a learned policy?

**Traditional Metrics:**
- Number of parameters (misleading)
- Network depth (doesn't capture simplicity of weights)

**Continued Fraction Approach:**
Convert policy parameters to continued fractions. Depth = complexity.

**Why This Works:**
- Simple policies have simple (short) continued fractions
- Complex policies have deep continued fractions
- "Rational" policies are interpretable; "irrational" ones are not

### 2.2 Use Cases

#### Use Case 1: Policy Interpretability Score

```python
def interpretability_score(policy_params):
    """
    Calculate how interpretable a policy is based on
    continued fraction depth of its parameters.
    """
    depths = [cf_depth(param) for param in policy_params]
    avg_depth = np.mean(depths)
    
    # Shallow = interpretable, Deep = complex
    return 1.0 / (1.0 + avg_depth)
```

#### Use Case 2: Overfitting Detector

If parameter values require very deep continued fractions (large coefficients), the policy might be overfitting.

#### Use Case 3: Compression

Best rational approximations from continued fractions can compress policies without significant loss.

---

## III. Implementation Specification

### 3.1 Core Algorithm

```python
def continued_fraction(x, max_depth=10, tolerance=1e-10):
    """
    Convert number x to continued fraction representation.
    Returns: List of coefficients [a0, a1, a2, ...]
    """
    cf = []
    for _ in range(max_depth):
        a = int(x)
        cf.append(a)
        x = x - a
        
        if abs(x) < tolerance:
            break
        
        x = 1.0 / x
    
    return cf

def cf_depth(x, max_depth=10):
    """Return depth of continued fraction."""
    cf = continued_fraction(x, max_depth)
    return len(cf)

def cf_to_value(cf):
    """Convert continued fraction back to value."""
    if not cf:
        return 0
    
    value = cf[-1]
    for a in reversed(cf[:-1]):
        value = a + 1.0 / value
    
    return value

# Example
phi = (1 + math.sqrt(5)) / 2
cf_phi = continued_fraction(phi, max_depth=20)
# φ = [1; 1, 1, 1, 1, ...] (all 1s)

pi = math.pi
cf_pi = continued_fraction(pi, max_depth=10)
# π = [3; 7, 15, 1, 292, 1, 1, 1, 2, 1]
```

### 3.2 Policy Analysis Integration

```python
class PolicyComplexityAnalyzer:
    """Analyze policy complexity via continued fractions."""
    
    def __init__(self, max_depth=10):
        self.max_depth = max_depth
    
    def analyze_policy(self, policy_weights):
        """
        Analyze a policy's parameters.
        Returns dict with complexity metrics.
        """
        cf_depths = []
        cf_representations = []
        
        for weight in policy_weights.flatten():
            cf = continued_fraction(weight, self.max_depth)
            cf_depths.append(len(cf))
            cf_representations.append(cf)
        
        return {
            'mean_depth': np.mean(cf_depths),
            'max_depth': np.max(cf_depths),
            'interpretability_score': 1.0 / (1.0 + np.mean(cf_depths)),
            'simple_weight_ratio': sum(1 for d in cf_depths if d <= 3) / len(cf_depths),
            'cf_representations': cf_representations
        }
    
    def compress_policy(self, policy_weights, max_cf_depth=3):
        """
        Compress policy by truncating continued fractions.
        This gives best rational approximations.
        """
        compressed = []
        for weight in policy_weights.flatten():
            cf = continued_fraction(weight, max_depth=max_cf_depth)
            approx = cf_to_value(cf)
            compressed.append(approx)
        
        return np.array(compressed).reshape(policy_weights.shape)
```

### 3.3 Configuration

```python
# config.py

# Continued Fraction Analysis
ENABLE_CF_ANALYSIS = False  # Experimental
CF_MAX_DEPTH = 10
CF_INTERPRETABILITY_THRESHOLD = 0.5  # Below this = complex policy
CF_COMPRESSION_ENABLED = False
```

---

## IV. Test Development Guidance

### 4.1 Unit Tests

```python
# tests/test_continued_fractions.py

import pytest
import math
from continued_fractions import continued_fraction, cf_to_value, cf_depth

class TestContinuedFractions:
    
    def test_rational_number(self):
        """Rational numbers should have finite CF."""
        x = 3.75  # = 15/4
        cf = continued_fraction(x)
        assert cf == [3, 1, 3]  # 3 + 1/(1 + 1/3) = 3.75
    
    def test_golden_ratio(self):
        """Golden ratio should be [1; 1, 1, 1, ...]"""
        phi = (1 + math.sqrt(5)) / 2
        cf = continued_fraction(phi, max_depth=10)
        assert cf[0] == 1
        assert all(a == 1 for a in cf[1:])  # All 1s
    
    def test_sqrt_2(self):
        """√2 should be [1; 2, 2, 2, ...]"""
        sqrt2 = math.sqrt(2)
        cf = continued_fraction(sqrt2, max_depth=10)
        assert cf[0] == 1
        assert all(a == 2 for a in cf[1:])  # All 2s
    
    def test_pi(self):
        """π should have irregular CF."""
        pi = math.pi
        cf = continued_fraction(pi, max_depth=10)
        assert cf[0] == 3
        assert cf[1] == 7
        assert cf[2] == 15
        # Irregular pattern
    
    def test_reconstruction(self):
        """CF should reconstruct original value."""
        x = 2.71828  # ≈ e
        cf = continued_fraction(x, max_depth=10)
        reconstructed = cf_to_value(cf)
        assert abs(reconstructed - x) < 1e-6
    
    def test_depth_simple_vs_complex(self):
        """Simple numbers should have shallower CF."""
        simple = 0.5  # = 1/2
        complex_val = math.pi
        
        assert cf_depth(simple) < cf_depth(complex_val)
```

### 4.2 Integration Tests

```python
# tests/test_cf_policy_analysis.py

from policy_complexity import PolicyComplexityAnalyzer
import numpy as np

class TestPolicyComplexityAnalyzer:
    
    def test_simple_policy(self):
        """Test analysis of simple policy (rational weights)."""
        # Policy with simple weights
        weights = np.array([0.5, 0.25, 0.75, 1.0])
        
        analyzer = PolicyComplexityAnalyzer()
        analysis = analyzer.analyze_policy(weights)
        
        # Simple weights → high interpretability
        assert analysis['interpretability_score'] > 0.7
        assert analysis['mean_depth'] < 3
    
    def test_complex_policy(self):
        """Test analysis of complex policy (irrational weights)."""
        # Policy with complex weights
        weights = np.array([math.pi, math.e, math.sqrt(2), phi])
        
        analyzer = PolicyComplexityAnalyzer()
        analysis = analyzer.analyze_policy(weights)
        
        # Complex weights → low interpretability
        assert analysis['interpretability_score'] < 0.5
        assert analysis['mean_depth'] > 5
    
    def test_policy_compression(self):
        """Test policy compression via CF truncation."""
        original = np.array([math.pi, math.e])
        
        analyzer = PolicyComplexityAnalyzer()
        compressed = analyzer.compress_policy(original, max_cf_depth=3)
        
        # Compressed should be close but simpler
        assert np.allclose(compressed, original, atol=0.01)
        # Verify compressed has shallower CF
        for comp in compressed:
            assert cf_depth(comp) <= 3
```

---

## V. Connection to MacGyver Philosophy

### 5.1 Alignment with Principles

**Principle 2 (Humility):**
> "The map is always wrong."

Continued fractions tell you how "wrong" (complex) your approximation is.

**Principle 14 (Hubris):**
> "Sustained success without surprise is evidence of a model too simple to be wrong."

CF depth measures model complexity. Too simple = suspicious.

### 5.2 Novel Insights

**Insight 1: Interpretability ≠ Parameter Count**
A network with 1000 parameters might be interpretable if all weights are simple fractions.

**Insight 2: Overfitting Signature**
Deep continued fractions = overfitting to noise (capturing irrational patterns).

---

## VI. Red Team Analysis

### 6.1 Limitations

**Limitation 1: Computational Cost**
Computing CF for every parameter is expensive.

**Mitigation:** Sample subset of parameters.

**Limitation 2: Not Scale-Invariant**
CF depth changes if you scale parameters.

**Mitigation:** Normalize parameters first.

**Limitation 3: Limited Applicability**
Only works for scalar parameters, not discrete or categorical.

---

## VII. Implementation Checklist

- [ ] Create `continued_fractions.py`
- [ ] Implement CF conversion
- [ ] Create `PolicyComplexityAnalyzer`
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Add to agent analysis pipeline (optional)

**Estimated Effort:** 1 day

**Priority:** Low (interesting but not critical)

---

## Conclusion

Continued fractions provide a mathematical lens for measuring policy complexity and interpretability. While not as immediately practical as Golden Ratio or Fibonacci, they offer a unique perspective on what makes a policy "simple" vs. "complex."

**Key Takeaway:** The depth of a continued fraction measures how "irrational" (complex) a number is. Apply this to AI parameters to detect overfitting and measure interpretability.
