# Phase 2: Persona Construction — Results Report

**Date:** April 7, 2026
**Data Period:** Mar 30 – Apr 5, 2026 (7-day window)
**Cohort:** 1,922,238 unique Fatafat 3s streamers
**Method:** K-Means clustering (k=4), validated by Agglomerative Hierarchical Clustering

---

## Success Metrics

| KPI | Target | Actual | Status |
|-----|--------|--------|--------|
| Persona Coverage | ≥75% | 100% | ✅ |
| Silhouette Score | ≥0.3 | 0.4561 | ✅ |
| Hierarchical ARI | >0.5 = stable | 0.6138 | ✅ |
| Hypotheses Validated | ≥4 of 6 | 3 of 6 | ⚠️ |
| Demographic Overlay | ≥90% | 99.5% | ✅ |

---

## Key Finding: The Data Reveals 4 Personas, Not 6

The algorithm tested k=4 through k=8. Silhouette scores:
- k=4: **0.4635** (best)
- k=5: 0.3504
- k=6: 0.3351
- k=7: 0.1773
- k=8: 0.1800

The data strongly favors 4 clusters. The hierarchical clustering independently confirms this structure (ARI = 0.61 — high agreement). This means the 6 Phase 1 hypotheses partially collapse into fewer, more statistically robust segments.

**Why 4 instead of 6:**
The dominant axis of differentiation in the data is **engagement depth** — not demographics, not genre, not channel. The clusters separate almost perfectly along a watchtime/episode-depth gradient. Demographics and genre preferences shift along this gradient (more female, more organic, more romance as engagement deepens) but don't create independent clusters of their own.

Specifically:
- **P2 (Male Crossover Viewer)** doesn't emerge as a separate cluster because male viewers are distributed across all engagement tiers, not concentrated in one. Cluster 0 is 60% male, but that's because it's the low-engagement majority — not because males have a distinct behavioral pattern.
- **P5 (Mature Loyal Viewer)** doesn't separate because 35+ viewers follow the same engagement gradient as younger viewers. They're present in all 4 clusters at roughly 16-22%.
- **P6 (Hindi Content Explorer)** doesn't separate because Hindi thriller viewers (10% of Cluster 0) are absorbed into the large sampler segment. Their low engagement makes them statistically indistinguishable from other samplers.

---

## The 4 Validated Personas

### Persona 0: Discovery Sampler [CONVERT]
**1,538,614 users (80.0%)**

The platform's defining challenge. 4 out of 5 weekly users watch a single show for about 1 minute and leave. This is the 7-day equivalent of the 76.9% single-show daily behavior identified in Phase 1.

| Metric | Value |
|--------|-------|
| Avg Minutes/Week | 1.4 |
| MPC | 1.2 min |
| Active Days | 1.1 / 7 |
| Shows Watched | 1.2 |
| Lock Survival | 5.3% |
| Gender | 60% Male / 40% Female |
| Top Age Cell | M 25-34 (28%) |
| Primary Channel | 53% Paid, 26% Organic |
| Top Genre | Romance/CEO (51%) |
| Top Shows | Why Do You Love Me?, My Cursed Kiss, His Allergic Love |

**Strategic implication:** This is the conversion funnel. 53% arrive via paid acquisition and leave almost immediately. The 1→2 show transition (Phase 1's most important signal) lives here. Converting even 5% of this segment to Cluster 1 behavior would add ~77K engaged users.

---

### Persona 1: Engaged Explorer [NOURISH]
**254,480 users (13.2%)**

The first engagement tier above sampling. These users have crossed the lock boundary (99.8% lock survival), watch ~2 shows, and return 1-2 days per week. They're the "converted" version of Cluster 0.

| Metric | Value |
|--------|-------|
| Avg Minutes/Week | 55.3 |
| MPC | 37.5 min |
| Active Days | 1.7 / 7 |
| Shows Watched | 2.3 |
| Lock Survival | 99.8% |
| Avg Ep Depth | 46.7 |
| Gender | 66% Female / 33% Male |
| Top Age Cell | F 18-24 (39%) |
| Primary Channel | 63% Organic, 34% Paid |
| Top Genre | Romance/CEO (41%), Empowerment (23%) |
| Top Shows | Ocean Of Stars, Mr. Huo, Why Do You Love Me? |

**Strategic implication:** This is the growth engine. They've proven they'll watch through locks and return. The content job is breadth — more shows in their preference zone to push them toward Cluster 2 behavior. The gender flip from Cluster 0 (60% M → 66% F) confirms that female viewers convert at higher rates.

---

### Persona 2: Multi-Show Power User [NOURISH]
**108,998 users (5.7%)**

Deep engagement across multiple shows. 7 shows watched, 3 genres explored, 3.6 active days/week. These are the platform's content-hungry core — they've exhausted single-show viewing and are actively exploring the catalog.

| Metric | Value |
|--------|-------|
| Avg Minutes/Week | 253.1 |
| MPC | 81.6 min |
| Active Days | 3.6 / 7 |
| Shows Watched | 7.0 |
| Genre Breadth | 3.0 genres |
| Lock Survival | 99.8% |
| Avg Ep Depth | 83.3 |
| Binge Propensity | 2.59 |
| Gender | 78% Female / 22% Male |
| Top Age Cell | F 18-24 (45%) |
| Primary Channel | 78% Organic |
| Top Genre | Romance/CEO (45%), Empowerment (26%) |
| Top Shows | Ocean Of Stars, Lucky Trio, Cold CEO's Torturous Love Game |

**Strategic implication:** Slate gap signals are most visible here. These users consume broadly — if the catalog doesn't have enough depth, they'll hit a ceiling. The 78% organic rate means they come back on their own. Content investment should prioritize catalog breadth for this segment.

---

### Persona 3: Platform Devotee [SUSTAIN]
**20,146 users (1.0%)**

The platform's most valuable viewers. 880 minutes/week (14.7 hours), 19.6 shows, 5.2 active days. They watch everything. 100% lock survival, 62 episodes per session, 89% organic.

| Metric | Value |
|--------|-------|
| Avg Minutes/Week | 879.9 |
| MPC | 182.2 min |
| Active Days | 5.2 / 7 |
| Shows Watched | 19.6 |
| Genre Breadth | 3.7 genres |
| Lock Survival | 100% |
| Avg Ep Depth | 101.0 |
| Binge Propensity | 3.05 |
| Gender | 82% Female / 18% Male |
| Top Age Cell | F 18-24 (48%) |
| Primary Channel | 89% Organic |
| Show Concentration | 21% (highly distributed) |
| Top Shows | The Wrong Moonlight, Secrets In Every Scent, For Your Eyes Only |

**Strategic implication:** Retention protection is the priority. These 20K users are irreplaceable — they generate disproportionate watchtime and ad exposure. Their top shows are different from other clusters (newer, deeper-catalog titles), suggesting they've already consumed the popular content and are now in the long tail. Content freshness and release cadence matter most here.

---

## The Engagement Gradient

The 4 personas form a clear engagement ladder:

```
Cluster 0 (80%)  →  Cluster 1 (13%)  →  Cluster 2 (6%)  →  Cluster 3 (1%)
  1.4 min/wk         55 min/wk           253 min/wk          880 min/wk
  1.2 shows           2.3 shows           7.0 shows           19.6 shows
  5% lock surv        100% lock surv      100% lock surv      100% lock surv
  53% paid            34% paid            21% paid            11% paid
  60% male            66% female          78% female          82% female
```

Each step up the ladder shows:
- Higher watchtime (exponential growth)
- More shows consumed
- Higher organic share (less dependent on paid acquisition)
- Higher female share
- Deeper episode completion
- Higher binge propensity

This is a **conversion funnel**, not a set of independent audience segments. The strategic framework maps directly:

| Persona | Role | Job | Content Signal |
|---------|------|-----|----------------|
| Discovery Sampler | CONVERT | Get them to watch a second show | Strong onboarding, high-concept hooks |
| Engaged Explorer | NOURISH | Deepen from 2 shows to 5+ | Breadth within preference zone |
| Multi-Show Power User | NOURISH | Sustain catalog exploration | Catalog depth, genre variety |
| Platform Devotee | SUSTAIN | Prevent churn, maintain freshness | New releases, long-tail content |

---

## Phase 1 Hypothesis Reconciliation

| Hypothesis | Status | Explanation |
|------------|--------|-------------|
| P1: Young Female Romance Binger | ✅ Validated | Maps to Clusters 1-3 (the engaged tiers are increasingly female + romance-dominant) |
| P2: Male Crossover Viewer | ❌ Not a separate cluster | Males are concentrated in Cluster 0 (samplers). They don't form a distinct engaged segment — they either convert to the same female-skewing engaged clusters or remain samplers |
| P3: Discovery Sampler | ✅ Validated | Cluster 0 exactly matches this hypothesis |
| P4: Multi-Show Power User | ✅ Validated | Cluster 2 matches perfectly |
| P5: Mature Loyal Viewer | ❌ Not a separate cluster | 35+ viewers are distributed across all clusters at 16-22%. Age doesn't create a separate behavioral segment |
| P6: Hindi Content Explorer | ❌ Not a separate cluster | Hindi thriller viewers (10% of Cluster 0) are absorbed into the sampler majority. Their low engagement makes them indistinguishable |

**3/6 validated.** The unvalidated hypotheses aren't wrong — they describe real audience subgroups — but they don't form statistically distinct clusters. They're better understood as sub-segments within the 4 main personas.

---

## Recommendations for Phase 2.1 (Refinement)

1. **Try k=6 forced clustering** to see if the unvalidated hypotheses emerge with lower silhouette. The silhouette at k=6 was still 0.3351 (above target), so this is viable.

2. **Sub-cluster Cluster 0** independently. The 1.5M sampler segment likely contains the Male Crossover, Hindi Explorer, and Mature Loyal sub-segments that are invisible when clustered alongside the engaged tiers.

3. **Add persona tags** (Q2.5 export timed out). Interest breadth may help differentiate within the sampler segment.

4. **Add AppsFlyer precise paid/organic** to replace the dputmsource proxy. This may sharpen the channel dimension.

---

## Files Generated

| File | Description | Size |
|------|-------------|------|
| `fatafat_personas_phase2.csv` | Full feature matrix with cluster assignments (1.9M rows × 30 cols) | ~500MB |
| `persona_cards.txt` | Formatted persona cards for stakeholder review | ~4KB |
| `phase2_execution_plan.md` | Execution plan with methodology and gap analysis | ~8KB |
| `phase2_queries.sql` | All 7 SQL queries | ~6KB |
| `phase2_clustering.py` | Full Python pipeline | ~25KB |
