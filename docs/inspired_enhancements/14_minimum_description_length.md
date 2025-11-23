# Minimum Description Length: Model Selection Criterion

> **Ancient Wisdom:** Rissanen (1978), formalization of Occam's Razor  
> **Modern Application:** Choose models that balance fit and complexity  
> **Status:** Medium-value model selection framework

---

## I. Foundation

**Origin:** Jorma Rissanen (1978)

**Core Idea:** The best model is the one that compresses the data the most.

MDL = Model Size + Compressed Data Size

---

## II. AI Application

```python
import pickle

def mdl_score(model, data):
    """Calculate MDL score."""
    model_size = len(pickle.dumps(model))
    compressed_data = compress_with_model(model, data)
    return model_size + len(compressed_data)

def select_best_model(models, data):
    """Pick model with minimum MDL."""
    return min(models, key=lambda m: mdl_score(m, data))

# Example
simple_model = LinearModel()  # 100 bytes
complex_model = DeepNN()  # 10,000 bytes

# On small dataset, simple model wins (lower MDL)
# On large dataset, complex model might win (better compression)
```

---

## III. Implementation

```python
class MDLModelSelector:
    """Select policy based on MDL criterion."""
    
    def __init__(self):
        self.candidate_policies = []
    
    def evaluate_policy(self, policy, experience):
        """Calculate MDL for policy."""
        policy_size = self.measure_complexity(policy)
        fit_quality = self.measure_fit(policy, experience)
        
        # MDL = complexity + misfit
        mdl = policy_size - fit_quality
        return mdl
    
    def select_best(self, experience):
        """Choose policy with lowest MDL."""
        scores = {p: self.evaluate_policy(p, experience) 
                  for p in self.candidate_policies}
        return min(scores, key=scores.get)
```

---

## IV. Philosophy Connection

**Principle 14 (Hubris):** If model is too simple to be wrong, it's probably wrong. MDL balances.

**Estimated Effort:** 2 days  
**Priority:** Medium
