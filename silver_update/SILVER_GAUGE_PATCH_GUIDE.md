# Silver Gauge Patch – Implementation Guide

This patch adds an **optional rational-gauge / Pythagorean-mean layer**
on top of the existing active-inference and procedural-memory demo.

It does **three** things:

1. Adds a new module `scoring_silver.py` which wraps the existing
   scoring and compresses goal vs information vs cost into a compact
   set of **Pythagorean-mean invariants** (HM/GM/AM).

2. Extends `graph_model.log_step(...)` so that each `:Step` node can
   (optionally) carry a `silver_stamp` JSON blob and a `silver_score`
   scalar. This does *not* change behaviour; it only enriches the
   graph for analysis and visualisation.

3. Leaves `agent_runtime.py`, `runner.py` and `scoring.py` untouched
   behaviour-wise. The agent still makes decisions using the existing
   active-inference scoring; the silver gauge runs in parallel as an
   **introspectable diagnostic layer**.

---

## 1. What the Silver Gauge Is (High Level)

The core active-inference policy already computes a scalar score

\[
  \text{score} = \alpha\,\text{goal} + \beta\,\text{info}
                  - \gamma\,\text{cost},
\]

where:

- **goal** ≈ expected success at escaping,
- **info** ≈ expected reduction in uncertainty (entropy),
- **cost** ≈ action cost.

The silver patch does **not** replace this. Instead it asks:

> "What *shape* does this trade-off have?"

and then uses the classic **Pythagorean means**:

- Harmonic mean (HM) — emphasises bottlenecks / series effects
- Geometric mean (GM) — emphasises balance / multiplicative trade-offs
- Arithmetic mean (AM) — simple average

We build two small bundles:

1. **Exploration bundle** – between |goal| and info
2. **Efficiency bundle** – between (|goal| + info) and cost

and from each we derive a **shape coefficient** in [0, 1] via GM/AM.

These shape coefficients tell you, per step:

- whether goal vs info are nicely balanced or very lopsided, and
- whether goal+info comfortably outweighs the cost, or not.

That entire summary is stored as a compact `silver_stamp` JSON blob
on each Step node.

---

## 2. Files in This Patch

This zip contains the following key files (all intended to drop into
the same directory as your existing demo code):

- `scoring_silver.py`

  New module. Wraps `scoring.score_skill_detailed(...)` and produces
  a dictionary with:

  - original components: goal_value, info_gain, cost, base_score
  - Pythagorean means: HM/GM/AM over (goal, info) and (goal+info, cost)
  - shape coefficients: k_explore, k_efficiency
  - entropy at this belief
  - `silver_score` (a softly rescaled version of base_score)

- `graph_model.py`

  Patched `log_step(...)` function which:

  - keeps the original episode logging behaviour intact,
  - tries to build a silver stamp if `scoring_silver` is available,
  - writes the result as:
    - `Step.silver_stamp` (JSON string)
    - `Step.silver_score` (float)
    - and also adds a convenience `Step.skill_name` property.

- `scoring.py`, `agent_runtime.py`, `runner.py`

  Included unchanged from your current working state so that this
  patch zip is self-contained. You can diff them against your repo
  to confirm that only `graph_model.py` gained the silver-specific
  code and that behaviour is otherwise unchanged.

- `cypher_init.cypher`

  Your current schema / seed script, passed through unchanged. This
  patch does **not** require any schema changes; the silver stamp
  simply adds extra properties on `:Step` nodes at runtime.

- `SILVER_GAUGE_PATCH_GUIDE.md` (this file)

  Human-readable guide and quick reference for whoever is applying
  or reviewing the patch.

---

## 3. How to Apply This Patch (Idiot-Proof Version)

1. **Backup your repo**

   - Commit your current work or copy the directory somewhere safe.
   - This patch is small, but you always want an easy rollback path.

2. **Drop in the files**

   From the zip, copy:

   - `scoring_silver.py`
   - `graph_model.py`
   - `scoring.py`
   - `agent_runtime.py`
   - `runner.py`
   - `cypher_init.cypher`
   - `SILVER_GAUGE_PATCH_GUIDE.md`

   into the root of your Neo-MacGyver demo project, overwriting
   the existing Python files as appropriate.

   > If you prefer, you can instead manually merge the changes
   > by diffing `graph_model.py` and just adding `scoring_silver.py`.

3. **Verify imports**

   - Ensure `scoring.py`, `agent_runtime.py`, `runner.py` still run
     their basic unit tests or manual smoke tests.
   - The new `scoring_silver.py` has no external dependencies beyond
     `scoring.py` and the standard library.

4. **Run a smoke test**

   - Start Neo4j and seed the graph using your usual command
     (e.g. via `cypher_init.cypher`).
   - Run a single demo episode, e.g.:

     ```bash
     python runner.py --door-state locked
     ```

   - Confirm that behaviour looks unchanged (same type of trace,
     same number of steps, etc.).

5. **Inspect the silver stamp in Neo4j**

   In Neo4j Browser, run:

   ```cypher
   MATCH (e:Episode)-[:HAS_STEP]->(s:Step)
   RETURN e, s
   ORDER BY s.step_index;
   ```

   - Click on a `Step` node.
   - You should now see additional properties:
     - `skill_name`
     - `silver_stamp` (a JSON string)
     - `silver_score` (float)

   You can also inspect specific properties:

   ```cypher
   MATCH (e:Episode)-[:HAS_STEP]->(s:Step)
   RETURN s.step_index,
          s.skill_name,
          s.silver_score,
          s.silver_stamp
   ORDER BY s.step_index;
   ```

   The JSON blob contains all the HM/GM/AM fields and shape
   coefficients described above.

---

## 4. How the Code Fits Together

### 4.1 `scoring_silver.build_silver_stamp(...)`

- Input: `skill_name`, `cost`, `p_unlocked`
- Calls: `scoring.score_skill_detailed(...)` to reuse the exact
  same logic the agent uses for decision-making.
- Computes Pythagorean means and shape coefficients.
- Returns a pure dict ready to be JSON-encoded.

### 4.2 `graph_model.log_step(...)`

The signature is now:

```python
def log_step(session, episode_id, step_index,
             skill_name, observation,
             p_before, p_after,
             silver_stamp: Optional[Dict[str, Any]] = None)
```

- Existing callers that pass only the original 7 arguments work
  unchanged; `silver_stamp` defaults to `None`.
- Inside, the function:

  1. Tries to import `scoring_silver.build_silver_stamp`.
  2. If that succeeds *and* no `silver_stamp` was provided:
     - queries Neo4j for `Skill.cost` by `skill_name`,
     - builds a silver stamp using `p_before`,
     - JSON-encodes it.
  3. If anything fails (module missing, query error, etc.), it
     silently falls back to "no silver" and just logs the basic step.
  4. In the write transaction, it creates or merges the Step and
     related nodes as before, then conditionally attaches:
     - `s.silver_stamp = $silver_json`
     - `s.silver_score = $silver_score`

---

## 5. How to Talk About This in a Demo / Interview

In a 30–60 second explanation, you can say:

> "On top of the active inference policy we already discussed, I
> added a *silver gauge* layer which uses Pythagorean means to
> compress the trade-off between goal, information gain, and cost
> into a compact stamp on each step. This doesn’t change behaviour,
> but it gives us a principled way to *measure* and *visualise* how
> exploratory or efficient each decision was. We log that into the
> graph so we can query it later, plot it, or compare different
> policies side-by-side."

And if someone asks "Why Pythagorean means?", you can say:

> "They’re a very old but very robust trio of averages. The harmonic
> mean picks up bottlenecks, the geometric mean is the natural
> multiplicative average, and the arithmetic mean is the usual one.
> By looking at HM/GM/AM together we can see whether the policy is
> balanced or lopsided in how it trades goal vs information vs cost,
> and we can do that without changing the existing agent code."

---

## 6. Optional Next Steps (If You Want to Extend)

None of this is required for the patch to be useful, but if you or
the implementation agent want to go a bit further, here are safe and
incremental extensions:

1. **Expose a CLI flag**

   Add an option like `--log-silver` to `runner.py` that toggles
   whether `log_step` should be asked to build a silver stamp.
   Right now it tries by default; you could make that explicit.

2. **Expose the silver score in traces**

   When printing the episode trace, include the `silver_score` and/or
   `k_explore`, `k_efficiency` from the JSON blob so you can see
   how "explorey" or "efficient" each step was in plain text.

3. **Graph analytics**

   Add a small `analysis_silver.py` script that:

   - pulls all Steps and parses `silver_stamp`,
   - plots k_explore / k_efficiency over time,
   - compares baseline total_score vs silver_score for each skill.

4. **Policy comparison**

   If you later add alternative policies or parameter sets, you can
   use the silver stamp as a common metric to compare them: which
   policy tends to have a healthier balance of exploration vs
   efficiency at the same belief levels?

---

## 7. Sanity Checks and Validation

After applying the patch, validate the following:

- [ ] Episodes still run to completion with no errors.
- [ ] Behaviour (selected skills, number of steps) matches the
      pre-patch behaviour for the same random seeds / scenarios.
- [ ] `Step` nodes now have `skill_name`, and (optionally)
      `silver_stamp` and `silver_score` properties.
- [ ] The `silver_stamp` JSON parses correctly if you copy-paste it
      into a JSON viewer.
- [ ] Turning `scoring_silver` off (e.g. renaming the file) causes
      the system to quietly fall back to plain logging again.

If all of those are green, the silver gauge patch is successfully
integrated.
