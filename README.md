# Audience Simulation Engine — Synthetic Personas

## Overview

An audience intelligence system that constructs data-backed synthetic personas from streaming behavioral data, then uses those personas to inform content acquisition, commissioning, and advertising strategy. The engine merges viewing behavior with demographic profiles and consumer interest signals to produce a unified audience model.

The end goal: evaluate who a show is for before it's bought or commissioned — replacing post-launch reactive analysis with pre-launch predictive intelligence.

## Architecture

Three-layer system, built in phases:

```
Layer 1: Unified Audience Dataset
  Streaming behavioral signals + demographics + interest segments
  → UUID-level join across engagement, CMS, demographic, and persona tables

Layer 2: Synthesized Persona Set
  K-Means clustering across 5 behavioral dimensions
  → Statistically validated personas with content identity + commercial profile

Layer 3: AI Simulation Engine (planned)
  Pseudo-viewer models trained per persona on historical show performance
  → Pre-launch engagement prediction, narrative density fit, audience-fit scoring
```

## Methodology

### Feature Matrix Construction

User-level feature vectors built across 5 dimensions from streaming event data (7-day window):

| Dimension | Features | Source |
|-----------|----------|--------|
| Engagement Depth | Total minutes, MPC, streams, active days, sessions, episodes/session | Player engagement events |
| Content Preference | Shows watched, genre breadth, show concentration, content source, content origin | Engagement + CMS metadata |
| Retention Profile | Max episode depth, lock boundary survival (Ep5→6), binge propensity | Engagement + CMS episode numbers |
| Demographics | Age group, gender, age×gender interaction | Demographic lookup table |
| Channel & Interest | Primary channel (paid/organic/push), interest tag count, 8 interest category flags | UTM attribution + ML persona tags |

### Clustering Algorithm

- K-Means with k=4 through k=8 evaluated via silhouette score and elbow method
- One-hot encoding for categorical features, StandardScaler for numerics
- Validated by Agglomerative Hierarchical Clustering (Ward linkage) using Adjusted Rand Index
- Iterative refinement across 4 phases to optimize cluster quality vs hypothesis alignment

| Iteration | Change | Silhouette | ARI | Hypotheses Validated |
|-----------|--------|-----------|-----|---------------------|
| Phase 2.0 | k=4, basic features | 0.46 | 0.61 | 3/6 |
| Phase 2.1 | + ML persona tags, k=6 | 0.42 | 0.65 | 4/6 |
| Phase 2.2 | + content source/origin | 0.43 | 0.75 | 4/6 ← selected |
| Phase 2.3 | + secondary genre one-hot | 0.11 | 0.38 | 5/6 (rejected) |

Phase 2.3 tested secondary genre as a clustering input but degraded silhouette from 0.43 to 0.11 — most users watch 1-2 shows, making per-user genre distributions binary and noisy. Secondary genre is instead applied as post-clustering enrichment.

### Two-Level Content Identity

Content preference is captured at two levels, applied after clustering:

- **Level 1 (Theme):** Per-cluster distribution of secondary genre watchtime (Edgy, Forbidden Love, Melodrama, Revenge, Secret Lives, etc.)
- **Level 2 (Archetype):** Derived from top 10 shows per cluster — their names, genres, and narrative patterns produce a human-readable content archetype

### Slate Gap Analysis

Demand (watchtime share) vs supply (catalog share) computed per secondary genre to identify acquisition gaps and oversupply. Per-persona gap analysis surfaces which personas are underserved by which content themes.

### Commercial Value Index

Composite score (0-100, platform average = 50) estimating per-persona commercial value:

| Component | Weight |
|-----------|--------|
| Engagement depth (log watchtime) | 30% |
| Session frequency (active days / 7) | 25% |
| Interest breadth (tag count) | 15% |
| Organic share | 15% |
| Lock survival | 15% |

### Strategic Framework

Personas are assigned to Grow / Nourish / Sustain / Convert roles based on segment size × engagement depth, per the implementation plan's taxonomy.

## Project Structure

```
├── docs/                              # Project documents
│   ├── phase2_report.md               # Phase 2 final report
│   ├── phase2_execution_plan.md       # Full methodology + content enrichment rationale
│   ├── phase1_report.md               # Phase 1 data foundation
│   ├── implementation_plan.md         # 5-phase project plan
│   ├── strategy_paper.md              # Anticipatory content strategy paper
│   └── source/                        # Original source documents
├── dashboard/                         # Interactive HTML dashboard
│   └── index.html                     # Self-contained, no dependencies
├── src/                               # Python & SQL
│   ├── phase2_queries.sql             # Redshift queries (7 queries)
│   ├── export_csvs.py                 # Redshift → CSV export
│   ├── export_persona_tags.py         # Interest tag aggregation
│   ├── phase2_clustering.py           # Base clustering pipeline
│   ├── phase2_1_refinement.py         # + persona tags
│   ├── phase2_2_enriched.py           # + content source/origin (selected)
│   ├── phase2_3_content_enriched.py   # Secondary genre experiment (rejected)
│   ├── phase2_final_content_enrichment.py  # Two-level content identity
│   ├── phase2_commercial_profiles.py  # CVI + advertiser affinity
│   ├── slate_gap_analysis.py          # Demand vs supply analysis
│   ├── archive/                       # Original agent-generated code
│   └── exploration/                   # CMS field exploration scripts
├── output/                            # Generated outputs
│   ├── persona_cards_final.txt
│   ├── slate_gap_analysis.csv
│   └── archive/                       # Superseded versions
└── data/                              # CSVs (gitignored)
```

## Phases

| Phase | Status | Deliverable |
|-------|--------|-------------|
| 1. Data Foundation | ✅ Complete | Unified behavioral dataset, 8 analytical queries, 6 persona hypotheses |
| 2. Persona Construction | ✅ Complete | Validated persona set, two-level content identity, slate gap analysis, interactive dashboard |
| 3. AI Model Training | Planned | Pseudo-viewer models per persona, retention curve prediction (target: r ≥ 0.70) |
| 4. Integration Pilot | Planned | Prediction vs actuals on upcoming commission |
| 5. Live Deployment | Planned | Production system across commissioning, slate planning, ad targeting |

## Running the Pipeline

1. Set `REDSHIFT_USERNAME` and `REDSHIFT_PASSWORD` in `.env`
2. `python src/export_csvs.py` — exports 6 CSVs from Redshift
3. `python src/export_persona_tags.py` — exports aggregated interest tags
4. `python src/phase2_2_enriched.py` — runs clustering (Phase 2.2)
5. `python src/phase2_final_content_enrichment.py` — adds two-level content identity
6. `python src/slate_gap_analysis.py` — computes demand vs supply gaps

Requirements: `pandas`, `numpy`, `scikit-learn`, `scipy`, `psycopg2-binary`
