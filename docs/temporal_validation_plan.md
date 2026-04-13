# Temporal Validation & Content Impact Analysis — Plan

## Objective

Validate whether the persona model (trained on Mar 30 - Apr 5, 2026) generalizes across time periods, and measure how catalog changes between periods affect demand distribution and persona composition.

## Three-Period Design

| Period | Dates | Role |
|--------|-------|------|
| P1 | Feb 3-9, 2026 | Historical baseline |
| P2 | Mar 3-9, 2026 | Mid-point |
| P3 | Mar 30 - Apr 5, 2026 | Current (model trained here) |

## Analysis Structure

### Part A: Model Generalization (Predict → Compare)

**Method:** Use the K-Means model trained on P3 to predict cluster assignments for P1 and P2 users. This tests whether the model's feature space and cluster centroids generalize to different time periods.

**Steps:**
1. For P1 and P2, run the same SQL queries (Q2.1 through Q2.4b) with updated date ranges
2. Build the same feature matrix (engagement, content, retention, demographics, channel)
3. Apply the same StandardScaler (fitted on P3) and one-hot encoding
4. Use `kmeans.predict()` from the P3 model to assign clusters
5. Compare predicted persona distributions vs P3 actuals

**What to measure:**
- Persona size distribution: Do the same 5 clusters emerge? What % shifts?
- Per-persona engagement metrics: MPC, lock survival, shows watched
- Per-persona demographics: Does the gender/age composition hold?
- Per-persona content theme: Does the secondary genre distribution hold?

**Expected outcomes:**
- Persona sizes WILL differ (platform growth, paid mix changes)
- Engagement metrics SHOULD be similar within each persona (the model captures behavioral types, not absolute levels)
- If a persona disappears or a new one dominates, that tells us something about catalog/audience evolution

### Part B: True Validation (Re-cluster → Compare)

**Method:** Run the full clustering pipeline independently on P1 and P2 data. This produces "ground truth" clusters for each period.

**Steps:**
1. Full feature matrix for P1 and P2
2. Independent K-Means (k=4 through k=8, silhouette selection)
3. Compare the independently-found clusters to the P3 model's predictions

**What to measure:**
- Optimal k for each period (is it still 5-6?)
- Silhouette scores (are clusters equally well-separated?)
- Cluster profile similarity: Can we map P1/P2 clusters to P3 clusters by behavioral profile?
- Adjusted Rand Index between predicted (from P3 model) and actual (from independent clustering) — this is the true generalization metric

**This data feeds Phase 3:** The prediction errors (where the P3 model misclassifies P1/P2 users) become training signal for the AI pseudo-viewer models. They show which behavioral patterns are temporally stable vs which are period-specific.

### Part C: Catalog Evolution & Content Impact

**Method:** Track what shows entered the catalog between periods and whether they affected demand.

**Steps:**
1. Query CMS for shows with `golive_date` between P1 and P2, and between P2 and P3
2. Classify new shows by secondary genre, content source, origin
3. Compare demand distribution (watchtime % by secondary genre) across P1 → P2 → P3
4. Compute slate gap ratios for each period
5. Check: Did new Melodrama shows reduce the Melodrama gap? Did new Crime shows increase oversupply?

**What to measure:**
- New shows added per period (count, by genre, by source)
- Demand shift: secondary genre watchtime % change P1→P2→P3
- Gap ratio change: Did undersupplied genres get addressed?
- Persona impact: Did any persona grow/shrink due to catalog changes?

## Execution Plan

### Phase 1: Data Export (3 periods × 6 queries = 18 query runs)

For each period (P1, P2), export:
- Q2.1: Engagement (uuid, streams, minutes, episodes, days, sessions)
- Q2.2a: User×video (uuid, videoid, streams, minutes)
- Q2.3: Session episodes (uuid, sid, episodes_in_session)
- Q2.4a: Demographics (uuid, age_group, gender)
- Q2.4b: Channel (uuid, primary_channel)

CMS lookup (Q2.2b) is period-independent — same table. But we need to check `golive_date` for catalog evolution.

**Note:** Q2.2a (user×video) is the largest export (~46M rows per period). Total data: ~140M rows across 3 periods. Estimated export time: ~20 min per period.

### Phase 2: Model Prediction

1. Load P3 model (kmeans object, scaler, encoder)
2. Build P1/P2 feature matrices using same pipeline
3. Predict cluster assignments
4. Generate per-period persona profiles

### Phase 3: Independent Clustering

1. Run full clustering on P1 and P2 independently
2. Find optimal k, compute silhouette
3. Map clusters to P3 personas by profile similarity
4. Compute ARI between predicted and actual

### Phase 4: Catalog Evolution

1. Query CMS golive_date for new shows between periods
2. Classify by secondary genre
3. Compute demand shift and gap ratio changes
4. Identify content impact signals

## Output

- `temporal_validation_results.md` — full findings
- `period_comparison.csv` — per-period persona metrics
- `catalog_evolution.csv` — new shows by period and genre
- `gap_ratio_trends.csv` — slate gap changes over time
- Dashboard update: new "Temporal Validation" section (if findings are significant)

## Constraints

- Each period's Q2.2a export is ~3.7GB / 46M rows — need ~15GB disk for all 3 periods
- Redshift query performance: 7-day windows are fast (~25-35s per query)
- Feb data may have different user volumes (platform was smaller)
- CMS `golive_date` is stored as bigint (epoch?) — need to verify format
