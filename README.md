# Fatafat Synthetic Personas — Audience Simulation Engine

**Amazon MX Player | Fatafat Micro-Drama Vertical**

## What This Is

The core of an Audience Simulation Engine for Fatafat. While the end goal is to predict who a show is for before we buy or commission it, the current state delivers the foundation: 5 validated audience personas with content preferences, commercial profiles, and a slate gap analysis — all derived from how 1.9 million viewers actually behave.

## Live Dashboard

**[View Dashboard →](https://d3eijncil08ojn.cloudfront.net/reports/synthetic-personas-phase2/index.html)**

## Project Structure

```
synthetic-personas/
├── docs/                              # Project documents
│   ├── phase2_report.md               # Phase 2 final report (main deliverable)
│   ├── phase2_execution_plan.md       # Methodology & content enrichment rationale
│   ├── phase1_report.md               # Phase 1 data foundation findings
│   ├── implementation_plan.md         # Full 5-phase project plan
│   ├── strategy_paper.md              # Anticipatory content strategy paper
│   └── source/                        # Original docx source documents
├── dashboard/                         # Interactive HTML dashboard
│   └── index.html                     # Self-contained, no dependencies
├── src/                               # Python & SQL code
│   ├── phase2_queries.sql             # All Redshift queries
│   ├── export_csvs.py                 # Redshift → CSV export
│   ├── export_persona_tags.py         # Interest tag aggregation export
│   ├── phase2_clustering.py           # Phase 2.0: base K-Means clustering
│   ├── phase2_1_refinement.py         # Phase 2.1: + persona tags, k=6
│   ├── phase2_2_enriched.py           # Phase 2.2: + content source/origin (selected)
│   ├── phase2_3_content_enriched.py   # Phase 2.3: secondary genre experiment (rejected)
│   ├── phase2_final_content_enrichment.py  # Two-level content identity enrichment
│   ├── phase2_commercial_profiles.py  # CVI + advertiser affinity
│   ├── slate_gap_analysis.py          # Demand vs supply gap analysis
│   ├── archive/                       # Original agent-generated code
│   └── exploration/                   # One-off CMS exploration scripts
├── output/                            # Generated outputs
│   ├── persona_cards_final.txt        # Final persona cards
│   ├── slate_gap_analysis.csv         # Gap analysis data
│   └── archive/                       # Superseded versions
└── data/                              # CSVs (gitignored — too large)
```

## Key Findings

- **5 personas** on an engagement ladder: Discovery Sampler (64.5%) → Male Crossover (18.3%) → Romance Binger (11.8%) → Engaged Explorer (3.2%) → Platform Devotee (2.3%)
- **Content maturation signal**: as engagement deepens, preference shifts from "Edgy" (28%) → "Forbidden Love" (24%) → "Secret Lives" (13%)
- **Slate gaps**: Melodrama is 2.3x undersupplied, Crime is 10x oversupplied
- **Male opportunity**: 351K male 25-34 viewers with highest Electronics/Tech + Affluent/Premium affinity

## Phases

| Phase | Status | Description |
|-------|--------|-------------|
| 1. Data Foundation | ✅ Complete | 8 queries, 6 hypotheses, behavioral baseline |
| 2. Persona Construction | ✅ Complete | 5 personas, two-level content identity, slate gaps |
| 3. AI Model Training | Planned | Pseudo-viewer models per persona |
| 4. Integration Pilot | Planned | Test on upcoming commission |
| 5. Live Deployment | Planned | Production system |

## Data

CSV data files are gitignored (too large). To regenerate:
1. Set `REDSHIFT_USERNAME` and `REDSHIFT_PASSWORD` in `.env`
2. Run `python src/export_csvs.py` (exports 6 CSVs from Redshift)
3. Run `python src/export_persona_tags.py` (exports interest tags)
4. Run `python src/phase2_2_enriched.py` (clustering)
5. Run `python src/phase2_final_content_enrichment.py` (content enrichment)
6. Run `python src/slate_gap_analysis.py` (gap analysis)
