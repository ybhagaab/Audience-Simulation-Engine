# Persona Maintenance Strategy: Centroid Matching, Drift Detection & Hybrid Approach

## Context

The persona model produces cluster assignments using K-Means. Every time K-Means is retrained on new data, cluster IDs are arbitrary — Cluster 0 in April might be the Discovery Sampler, but Cluster 0 in May might be the Platform Devotee. This is the **cluster correspondence problem**. Additionally, as the platform grows (new users, new content, new features), the persona structure itself may evolve — existing personas may drift, split, merge, or entirely new ones may emerge.

This document defines the mechanisms for handling these challenges in production.

---

## Three Strategies Compared

### 1. Centroid-Based Prediction

**How it works:** Train K-Means once. For new users or new time periods, use `kmeans.predict()` to assign them to the nearest existing centroid.

**Strengths:**
- Simple to implement
- Fast inference (just a distance calculation)
- No manual rules to maintain

**Failures:**
- Centroids are anchored to the training period's data distribution. If the distribution shifts (more paid users, new features added, different content mix), centroids become misaligned.
- Cannot detect new personas — new user types get forced into the nearest existing cluster even if they don't belong.
- Adding new features (e.g., new commercial tags, OTT overlap data) changes the feature space dimensionality. Old centroids are meaningless in the new space — full retrain required.
- We observed this directly: the P3 model predicted 79% of Feb users as "Platform Devotee" when they were actually samplers. The centroids didn't transfer.

**When it fails with growth:**
- Paid acquisition surge from a new channel → shifts channel distribution → centroids misalign
- Library expansion with new genres → content features change → centroids misalign
- New feature columns added → dimensionality change → centroids invalid

### 2. Profile Matching (Rule-Based)

**How it works:** Each persona is defined as a set of behavioral rules derived from the original clustering. Example: Discovery Sampler = total_minutes < 10 AND lock_survival < 15% AND shows < 2. New users are assigned to whichever profile they match.

**Strengths:**
- Deterministic and stable — same user always gets same persona
- Robust to data distribution shifts (rules are absolute, not relative)
- New features can be added incrementally as new rules without breaking existing ones
- Stakeholders see consistent persona names over time

**Failures:**
- Cannot discover new personas. If 200K users arrive who don't match any profile, they get forced into the closest one.
- Thresholds become stale. If the platform's engagement baseline shifts (e.g., average MPC doubles due to better content), the threshold "total_minutes < 10" may no longer capture the right users.
- Manual maintenance required — someone must review and update rules periodically.

**When it fails with growth:**
- New user types from new acquisition channels → no matching profile → misclassified
- Engagement baseline shift → thresholds become too loose or too tight
- New content genres → content rules don't account for them

### 3. Hybrid Approach (Recommended)

**How it works:** Profiles are the stable production assignment system. K-Means retraining runs monthly as a background discovery process. The two are compared to detect drift, validate profiles, and discover new personas.

**Strengths:**
- Stability of profiles for day-to-day operations
- Discovery power of clustering for detecting structural changes
- Graceful handling of new features, new users, and catalog evolution
- The cluster correspondence problem is solved because profiles are the identity layer — cluster IDs are an intermediate artifact that gets translated

**The flow:**
```
Monthly:
  1. Retrain K-Means on latest data (fresh features, fresh scaler)
  2. Match new centroids to existing profiles (centroid matching)
  3. Measure drift between new centroids and profile definitions
  4. Check for unmatched centroids (new persona candidates)
  5. Check for unmatched profiles (disappearing personas)
  6. Update profiles if drift exceeds threshold
  7. Report findings to stakeholders
```

---

## Mechanism 1: Centroid Matching (Cluster Correspondence)

### Problem

After monthly retraining, new cluster IDs are arbitrary. We need to map each new cluster to an existing persona profile.

### Method

For each existing persona profile, compute a **profile vector** — the expected centroid position based on the profile's behavioral characteristics:

```
Discovery Sampler profile vector:
  total_minutes: 2.0
  mpc: 2.0
  lock_survival: 0.08
  unique_shows: 1.2
  pct_female: 0.42
  pct_organic: 0.26
  ...
```

For each new centroid from the retraining, compute the same feature averages. Then compute **cosine similarity** between each new centroid and each profile vector.

```
Matching matrix (cosine similarity):

                    New C0    New C1    New C2    New C3    New C4
Sampler profile     0.95      0.12      0.08      0.31      0.15
Male Cross profile  0.30      0.04      0.11      0.92      0.18
Romance profile     0.11      0.88      0.22      0.09      0.35
Explorer profile    0.14      0.35      0.87      0.12      0.28
Devotee profile     0.08      0.21      0.30      0.10      0.91
```

Assignment: each profile gets matched to its highest-similarity centroid. In this example: Sampler → C0, Male Crossover → C3, Romance → C1, Explorer → C2, Devotee → C4.

### Thresholds

| Similarity | Interpretation | Action |
|-----------|----------------|--------|
| > 0.8 | Strong match | Auto-assign, no review needed |
| 0.5 - 0.8 | Moderate match | Flag for review — persona may be drifting |
| < 0.5 | Weak match | Profile may no longer exist in current data, or has evolved significantly |

### Unmatched Centroids

If a new centroid has similarity < 0.5 to ALL existing profiles, it's a **new persona candidate**. Examine its feature averages, demographic composition, and content preferences. If it represents a meaningful, actionable audience segment (not noise or outliers), create a new profile.

### Unmatched Profiles

If an existing profile has similarity < 0.5 to ALL new centroids, that persona may have **disappeared** — the audience segment no longer exists in the data. Investigate: did those users churn? Did they merge into another persona? Is it a data issue?

---

## Mechanism 2: Drift Detection

### Problem

Even when centroids match existing profiles, the behavioral characteristics may be shifting gradually. A persona that was 42% female in April might be 55% female by August. The profile still matches, but the persona is evolving.

### Method

For each matched persona, compute the **drift vector** — the difference between the new centroid's feature averages and the profile's reference values.

```
Discovery Sampler drift (April → June):
  total_minutes:  2.0 → 3.5  (+1.5, +75%)
  lock_survival:  0.08 → 0.12 (+0.04, +50%)
  pct_female:     0.42 → 0.48 (+0.06, +14%)
  pct_organic:    0.26 → 0.31 (+0.05, +19%)
```

### Drift Severity Classification

| Metric | Low Drift | Medium Drift | High Drift |
|--------|-----------|-------------|------------|
| Engagement (minutes, MPC) | < 20% change | 20-50% change | > 50% change |
| Behavioral (lock survival, shows) | < 10 pts | 10-25 pts | > 25 pts |
| Demographic (gender, age) | < 5 pts | 5-15 pts | > 15 pts |
| Channel (organic, paid) | < 10 pts | 10-20 pts | > 20 pts |

### Actions by Drift Level

| Level | Action |
|-------|--------|
| Low drift (all metrics) | No action. Log for trend tracking. |
| Medium drift (any metric) | Flag for review. Check if profile thresholds need adjustment. |
| High drift (any metric) | Mandatory review. Update profile rules. Investigate cause (catalog change? acquisition shift? seasonal?). |
| High drift (multiple metrics) | Persona may be fundamentally changing. Consider splitting or redefining. |

### Drift Tracking Over Time

Maintain a drift log:

```
| Month | Persona | Metric | Reference | Current | Drift % | Action |
|-------|---------|--------|-----------|---------|---------|--------|
| May   | Sampler | minutes | 2.0 | 2.3 | +15% | None |
| Jun   | Sampler | minutes | 2.0 | 3.5 | +75% | Review |
| Jun   | Male XO | pct_female | 0.34 | 0.41 | +21% | Flag |
```

This log becomes invaluable for Phase 3 — it shows which persona characteristics are stable (good for model training) vs which are volatile (need temporal features in the model).

---

## Mechanism 3: New Persona Discovery

### Triggers

A new persona should be investigated when:

1. **Unmatched centroid:** Monthly retraining produces a centroid with < 0.5 similarity to all existing profiles
2. **Optimal k increases:** Silhouette score improves at k+1 compared to previous month's optimal k
3. **Profile residual growth:** The % of users who match their assigned profile poorly (high distance from profile center) exceeds 15%
4. **External signal:** A major acquisition campaign, new content genre launch, or platform feature change that could create a new audience segment

### Validation Process

Before creating a new profile:

1. **Size check:** Does the candidate cluster have > 2% of total users? Smaller segments may be noise.
2. **Stability check:** Does the same cluster appear when you re-run with different random seeds? (Run K-Means 5 times with different seeds — if the cluster appears in 4/5 runs, it's stable.)
3. **Behavioral distinctiveness:** Is the cluster's profile meaningfully different from existing personas? (Not just a slight variation of an existing one.)
4. **Actionability:** Can the content team or ad team do something different for this segment? If not, it's analytically interesting but not operationally useful.

### Creation Process

1. Extract the new centroid's feature averages
2. Translate to profile rules (same process as original persona creation)
3. Name the persona based on dominant traits
4. Assign a strategic role (Grow/Nourish/Sustain/Convert)
5. Add to the profile registry
6. Update the dashboard and persona cards
7. Notify stakeholders

---

## Mechanism 4: Persona Splitting & Merging

### Splitting

A persona should be split when:
- Monthly retraining consistently finds 2 sub-clusters within what was 1 profile
- The sub-clusters have different content preferences or demographic compositions
- The content team needs to treat them differently

Example: Romance Binger splits into "CEO Romance Binger" (watches CEO/billionaire content) and "Empowerment Drama Binger" (watches female empowerment content). Same engagement level, different content identity.

Process: Create 2 new profiles from the sub-cluster centroids. Retire the parent profile. Map historical data to the new profiles for continuity.

### Merging

A persona should be merged when:
- Two profiles become behaviorally indistinguishable over time
- The content team doesn't need to treat them differently
- Maintaining separate profiles adds complexity without value

Process: Combine the two profiles into one. Use the larger cluster's centroid as the new reference. Update rules to be the union of both profiles' criteria.

---

## Implementation: Monthly Maintenance Cycle

```
Week 1: Data Export
  - Export latest 7-day feature matrix from Redshift
  - Run full clustering pipeline (same code as Phase 2.2)

Week 2: Centroid Matching + Drift Detection
  - Match new centroids to existing profiles (cosine similarity)
  - Compute drift vectors for all matched personas
  - Flag any unmatched centroids or profiles
  - Generate drift report

Week 3: Review + Action
  - Review flagged items with stakeholders
  - Decide: update thresholds? create new persona? split/merge?
  - Update profile rules if needed

Week 4: Update + Deploy
  - Update profile registry
  - Refresh dashboard with latest period's data
  - Update persona cards if profiles changed
  - Log all changes in drift tracking table
```

---

## Relationship to Phase 3

The drift log and centroid matching data feed directly into Phase 3 (AI Model Training):

- **Stable features** (low drift across months) → reliable training features for pseudo-viewer models
- **Volatile features** (high drift) → need temporal encoding or should be excluded from base model
- **New persona emergence patterns** → the model should be able to predict when a new segment is forming
- **Prediction errors** (where centroid prediction misclassifies users) → training signal for the model to learn what the simple K-Means misses
