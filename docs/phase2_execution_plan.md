# Phase 2: Persona Construction — Execution Plan (Revised)

**Project:** Fatafat Synthetic Personas / Audience Simulation Engine
**Phase:** 2 — Persona Construction
**Status:** Ready for execution
**Date:** April 7, 2026
**Input:** Phase 1 Data Foundation Report (8 queries, 6 persona hypotheses)

---

## Objective

Build 5–6 statistically validated, content-first personas from a user-level feature matrix spanning 5 behavioral dimensions. Target: ≥75% audience coverage, silhouette score ≥0.3, ≥4 of 6 Phase 1 hypotheses validated.

## Execution Architecture

**Approach:** SQL queries extract per-dimension features from Redshift → export as CSV → Python merges, engineers derived features, runs clustering, assigns strategic roles, and generates persona cards.

**Date window:** 7 days (Mar 30 – Apr 5, 2026)
**Cohort:** All Fatafat 3s streamers in the window (~400K users)
**Performance strategy:** All SQL queries are single-table aggregations first, CMS joins only on small result sets (per schema performance rules).

---

## Step 1: User-Level Feature Matrix — 5 Dimensions

### Dimension 1: Engagement Depth
**Source:** `fatafat.mxp_fatafat_player_engagement`
**Query:** Q2.1
**Features extracted from SQL:**
- `total_streams` — COUNT of 3s streams
- `total_minutes` — SUM playtime in minutes
- `unique_episodes` — COUNT DISTINCT videoid
- `active_days` — COUNT DISTINCT dates (out of 7)
- `total_sessions` — COUNT DISTINCT sid

**Features derived in Python:**
- `mpc` — total_minutes / active_days (minutes per consumer per day)
- `minutes_per_stream` — total_minutes / total_streams
- `streams_per_day` — total_streams / active_days
- `episodes_per_session` — unique_episodes / total_sessions
- `engagement_tier` — quintile bucketing (Sampler / Light / Moderate / Heavy / Binge)

**Gap fixed vs previous version:** Added MPC as explicit derived feature. Per-show episode depth moved to Dimension 3 where it belongs (uses CMS episode_number).

### Dimension 2: Content Preference
**Source:** `fatafat.mxp_fatafat_player_engagement` + `daily_cms_data_table`
**Queries:** Q2.2a (user×video aggregation), Q2.2b (CMS lookup)
**CMS fields used:**
- `tv_show_name` — show name
- `channel_ids` — show identifier (groups episodes into shows)
- `genre_name` — primary genre (e.g., [Romance], [Drama], [Thriller])
- `secondary_genre_name` — secondary genre (e.g., [Forbidden Love], [Melodrama], [Secret Lives])
- `language_name` — language (for Hindi content detection)
- `episode_number` — episode number (varchar, CAST to INT)

**Features derived in Python (after CMS join):**
- `unique_shows` — COUNT DISTINCT channel_ids per user
- `genre_breadth` — COUNT DISTINCT genre_name per user (mono vs multi-genre)
- `top_show` — show with highest watchtime per user
- `top_genre` — primary genre of top show
- `top_secondary_genre` — secondary genre of top show
- `show_concentration` — top_show_minutes / total_minutes (loyalty vs exploration)
- `is_romance_ceo` — flag: top genre is Romance AND secondary genre in (Forbidden Love, Edgy)
- `is_empowerment` — flag: top genre is Drama AND secondary genre in (Melodrama, Secret Lives)
- `is_hindi_original` — flag: language_name = [Hindi] AND genre in (Power Struggles, Thriller)
- `genre_cluster` — categorical: Romance/CEO, Empowerment, Hindi Thriller, Fantasy, Other

**Gap fixed vs previous version:** Added secondary_genre_name and language_name from CMS. Added explicit genre cluster classification aligned with Phase 1 content patterns (romance/CEO vs empowerment vs Hindi).

### Dimension 3: Retention Profile
**Source:** Q2.2a user×video data + CMS episode_number + Q2.3 session data
**Queries:** Q2.3 (session-level episode counts)

**Features derived in Python:**
- `max_episode_depth` — MAX(episode_number) per user across all shows (from CMS, not videoid count)
- `avg_episode_depth` — AVG max episode_number per show per user
- `lock_survival` — binary: did user watch episode_number ≥ 6 on any show? (Ep5→6 is first lock boundary)
- `avg_episodes_per_session` — from Q2.3 session data
- `max_episodes_per_session` — peak binge signal
- `binge_propensity` — max_episodes_per_session / avg_episodes_per_session (spikiness)

**Gap fixed vs previous version:** Lock survival now uses CMS `episode_number` (CAST to INT) instead of counting unique video IDs. This correctly identifies the Ep5→6 lock boundary.

### Dimension 4: Demographics
**Source:** `mxp_age_gender_details_table_v3`
**Query:** Q2.4a

**Features:**
- `age_group` — from lookup table (18-24, 25-34, 35-44, 45-54, 55-64, 65+)
- `gender` — Male / Female
- `age_gender` — interaction feature: concatenation of age_group + gender (e.g., "F_18-24", "M_25-34")

**Gap fixed vs previous version:** Added age×gender interaction feature as explicitly called for in the implementation plan.

### Dimension 5: Channel / Entry Behavior
**Source:** `fatafat.mxp_fatafat_player_engagement` (dputmsource)
**Query:** Q2.4b

**Features:**
- `primary_channel` — highest-watchtime channel per user: Paid / Organic / Push / OTT Notification / Internal Ad / Other

**Note on entry surface:** The plan calls for "For You vs Home vs Search vs Deep Link" entry surface classification. This would require `tabid` analysis from the engagement table. However, `tabid` on streaming events may not match the entry surface (per schema docs). For Phase 2 v1, we use channel classification only. Entry surface analysis can be added as a refinement in Phase 2.1 if needed.

**Note on AppsFlyer:** The schema docs note that dputmsource is an approximate proxy and AppsFlyer is the source of truth for paid/organic. For Phase 2 v1, we use dputmsource for speed. AppsFlyer-based reclassification can be layered in as a refinement.

### Dimension 5b: Interest Tags (Optional)
**Source:** `mxp_persona_details_table_v3` (ML source)
**Query:** Q2.5

**Features derived in Python:**
- `persona_tag_count` — number of distinct ML persona tags per user
- Used as a numeric feature in clustering (interest breadth signal)

---

## Step 2: Clustering Algorithm

### Encoding
- **Numeric features (14-16):** StandardScaler normalization
- **Categorical features:** One-hot encoding for `gender`, `age_group`, `primary_channel`, `genre_cluster` (NOT LabelEncoder — plan explicitly requires one-hot to avoid false ordinal relationships)

### Primary: K-Means
- Test k = 4, 5, 6, 7, 8
- Evaluate: silhouette score (target ≥0.3) + within-cluster sum of squares (elbow method)
- Sample 50K users for k-selection, then run final clustering on full dataset
- Starting point: k=6 to match Phase 1 hypothesis count

### Validation: Agglomerative (Hierarchical) Clustering
- Run on same 50K sample with k = best_k from K-Means
- Compare cluster assignments using Adjusted Rand Index (ARI)
- If ARI > 0.5, clusters are stable across methods → high confidence
- Produces dendrogram for visual validation of natural cluster count

### Cross-validation against Phase 1 Hypotheses
- Automated scoring: for each cluster, compute match score against each of the 6 Phase 1 hypotheses based on demographic skew, engagement depth, content preference, and channel behavior
- Target: ≥4 of 6 hypotheses should map to a distinct cluster

---

## Step 3: Strategic Role Assignment

Automated assignment based on segment size × engagement depth:

| Rule | Role | Criteria |
|------|------|----------|
| 1 | **GROW** | Cluster size > 20% of total AND avg_minutes < platform median |
| 2 | **NOURISH** | Cluster size 5-20% AND avg_minutes > platform median AND lock_survival > 50% |
| 3 | **SUSTAIN** | Cluster size < 15% AND avg_minutes > 1.5× platform median AND active_days > 4 |
| 4 | **CONVERT** | Cluster size > 30% AND avg_minutes < 10 (single-show samplers) |
| 5 | **EXPLORE** | Cluster size < 10% AND avg_minutes < 5 AND genre_cluster = Hindi Thriller or Other |

Rules are applied in priority order. Ties broken by engagement depth (higher depth → more advanced role).

---

## Step 4: Persona Card Generation

Each cluster produces a standardized persona card containing:

1. **Persona name** — auto-suggested based on dominant traits, human-reviewable
2. **Archetype label** — one-line behavioral summary
3. **Strategic role** — Grow / Nourish / Sustain / Convert / Explore with rationale
4. **Behavioral fingerprint:**
   - Engagement: avg minutes, streams/day, active days
   - Retention: max episode depth, lock survival rate, binge propensity
   - Content: top 3 shows, top genre, genre breadth, show concentration
5. **Demographic profile:** age/gender distribution, dominant cell, gender skew
6. **Channel profile:** organic vs paid split, primary channel
7. **Commercial profile:** avg persona tag count (interest breadth proxy)
8. **Coverage metric:** % of total active Fatafat audience

Output format: printed to console + exported as `persona_cards.txt`

---

## Step 5: Coverage Validation

- K-means assigns every user → coverage is 100% by definition
- Real validation: silhouette score ≥ 0.3 (clusters are meaningful)
- Secondary: no cluster should be < 2% of total (too small to be actionable)
- Tertiary: ≥4 of 6 Phase 1 hypotheses validated

---

## Data Flow Summary

```
Redshift Queries (7 exports):
  Q2.1  → q21_engagement.csv        (uuid-level engagement, ~400K rows)
  Q2.2a → q22a_user_video.csv       (uuid×videoid aggregation, ~2-5M rows)
  Q2.2b → q22b_cms_lookup.csv       (CMS metadata for fatafat videos, ~5-10K rows)
  Q2.3  → q23_session_episodes.csv  (uuid×session episode counts, ~1-3M rows)
  Q2.4a → q24a_demographics.csv     (uuid demographics, ~400K rows)
  Q2.4b → q24b_channel.csv          (uuid primary channel, ~400K rows)
  Q2.5  → q25_persona_tags.csv      (uuid×persona_name, ~4M rows) [OPTIONAL]

Python Pipeline:
  Load CSVs → Build 5 dimension feature sets → Merge on uuid
  → One-hot encode categoricals → StandardScaler on numerics
  → K-Means (k=4-8) + Hierarchical validation
  → Strategic role assignment → Persona card generation
  → Export: fatafat_personas_phase2.csv + persona_cards.txt
```

---

## Excluded from Phase 2 v1

- `mxp_fatafat_user_membership` — noise per user direction, excluded entirely
- `mxp_fatafat_player_interaction_v2` — seek/buffering signals (engagement quality). Valuable but adds query complexity. Can layer in as Phase 2.1 refinement
- AppsFlyer precise paid/organic — dputmsource proxy used for v1. AppsFlyer reclassification available as refinement
- Entry surface (For You / Home / Search / Deep Link) — requires tabid analysis with caveats. Deferred to Phase 2.1


---

## Phase 2.2 Refinement: Enriched Content Dimension Methodology

### Problem Statement

Initial clustering (Phase 2.0 and 2.1) used a collapsed `genre_cluster` feature that mapped 18 secondary genres into 6-7 broad buckets (Romance/CEO, Empowerment, Hindi Thriller, etc.). This produced persona cards where every persona showed the same top genres — Romance/CEO and Empowerment dominated across all clusters because Fatafat's catalog is 63% Romance + Drama.

The content dimension was not differentiating personas. The clustering was driven almost entirely by engagement depth, not content preference.

### Root Cause Analysis

CMS data exploration revealed:
- `genre_name` (primary genre): Only 6 meaningful values. Romance (148 shows) and Drama (91 shows) = 63% of catalog. Too broad to differentiate.
- `content_category`: "Fatafat" for all rows. No signal.
- `tag_name`: Content source/studio (Mandarin, Reelies, Fatafat Original, etc.). Useful for source classification but not content theme.
- `original_acquired`: International vs Hindi. Useful but binary.
- `title`: Just "Episode N". No descriptions.
- `secondary_genre_name`: **18 distinct values** — Edgy, Forbidden Love, Secret Lives, Revenge, Inheritance, Second Chances, Melodrama, Crime, Pulp, Inspiring, Hidden Identity, Time Travel, Horror, Mythical Action, Creature Romance, Fiction, Sacrifice. **This is the richest content descriptor available.**

### Approach Tested: Secondary Genre as Clustering Feature (Phase 2.3)

We tested using `secondary_genre_name` as direct one-hot clustering features — computing per-user watchtime fractions across all 18 secondary genres and feeding them into K-Means alongside the existing behavioral features.

**Result:** Silhouette dropped from 0.43 to 0.11. ARI dropped from 0.75 to 0.38. The clusters became statistically weaker.

**Why it failed:** Most Fatafat users watch only 1-2 shows in a 7-day window (median shows = 1). This means their secondary genre distribution is binary — 100% one genre, 0% everything else. When K-Means tries to cluster on these sparse binary vectors, it finds noise rather than signal. The secondary genre differentiation only emerges in aggregate across a cluster (e.g., "30% of this cluster's users watch Edgy content vs 20% in that cluster"), not at the individual user level.

**Key learning:** Content preference features work for clustering only when users have enough consumption breadth to create a meaningful distribution. On Fatafat, where 77% of daily users watch a single show, content preference is better captured as a post-clustering enrichment than as a clustering input.

### Solution: Two-Level Content Identity (Post-Clustering Enrichment)

Use the Phase 2.2 clustering (silhouette 0.43, ARI 0.75) as the base — this is statistically the strongest model, driven by engagement depth + demographics + channel + interest tags + content source/origin. Then overlay content identity as a two-level enrichment computed after clustering:

**Level 1: Content Theme (post-clustering profile)**
For each cluster, compute the distribution of `secondary_genre_name` across all users in the cluster. This shows what content themes the persona gravitates toward — Edgy vs Forbidden Love vs Revenge vs Secret Lives etc. — even though individual users may only watch one genre.

**Level 2: Content Archetype (derived from top shows)**
For each cluster, analyze the top 10 shows by user count. Extract common narrative patterns from show names + their genre/secondary genre combinations to derive a human-readable content archetype (e.g., "CEO/Billionaire Romance", "Female Empowerment", "Hindi Crime/Thriller").

### Why Post-Clustering Enrichment, Not Clustering Input

| Approach | Silhouette | ARI | Hypotheses | Assessment |
|----------|-----------|-----|------------|------------|
| Phase 2.1: Engagement + demo + channel + tags | 0.42 | 0.65 | 4/6 | Strong clusters, weak content identity |
| Phase 2.2: + content source/origin | 0.43 | 0.75 | 4/6 | Strongest clusters, source adds stability |
| Phase 2.3: + secondary genre one-hot | 0.11 | 0.38 | 5/6 | Weak clusters, better hypothesis match but unreliable |

Phase 2.2 clusters are the most statistically robust. Adding secondary genre as enrichment (not clustering input) gives us the content differentiation without sacrificing cluster quality. The 5th hypothesis (Hindi Content Explorer) validated in Phase 2.3 can be captured as a sub-segment annotation on the Male Crossover persona.

### Persona Card Content Section (Final Format)

Each persona card's content identity has two levels plus source:

```
CONTENT IDENTITY:
  Theme (L1):     Edgy (30%), Forbidden Love (22%), Revenge (12%), Melodrama (11%)
  Archetype (L2): CEO/Billionaire Romance — hook-driven, provocative first episodes
  Source:         International Dubbed (85%), Fatafat Original (4%)
  Origin:         International (85%), Hindi (15%)
  Top Shows:      Why Do You Love Me? (113K), My Cursed Kiss (87K), His Allergic Love (67K)
```

### Why This Matters

The two-level approach serves different stakeholders:
- **Content team** uses Level 2 (archetypes) to understand what narrative territory each persona occupies and what to commission
- **Data/analytics team** uses Level 1 (secondary genre distribution) for quantitative segmentation and tracking
- **Advertising team** uses the combination to match advertiser briefs to persona content environments

### Data Flow

```
Phase 2.2 Clusters (k=6, silhouette 0.43, ARI 0.75)
  ↓
For each cluster:
  → Join user×video to CMS secondary_genre_name
  → Compute secondary genre distribution (Level 1)
  → Analyze top 10 shows + genres → derive archetype (Level 2)
  → Add content source + origin profile
  → Persona card: all levels presented
```
