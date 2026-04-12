# Synthetic Personas — Phase 2: Persona Construction Report (Final)

**Amazon MX Player | Fatafat Micro-Drama Vertical**
**Date:** April 8, 2026
**Data Period:** Mar 30 – Apr 5, 2026 (7-day window)
**Cohort:** 1,922,238 unique Fatafat 3s streamers
**Classification:** CONFIDENTIAL — INTERNAL USE ONLY

---

## Executive Summary

Phase 2 of the Synthetic Personas project — Persona Construction — is complete. Behavioral clustering across 5 dimensions on 1.9 million weekly active streamers has produced **5 statistically validated personas** (plus 1 outlier cluster of 7 users, discarded) that together cover 100% of the active Fatafat audience.

The clustering achieves a silhouette score of 0.43 (target: ≥0.3), confirmed by hierarchical clustering validation (ARI = 0.75), and validates 4 of 6 Phase 1 hypotheses (target: ≥4). Each persona carries a **two-level content identity**: Level 1 (secondary genre theme distribution) and Level 2 (content archetype derived from top shows).

The dominant structural finding is that Fatafat's audience organizes along an **engagement gradient** — a conversion ladder from single-episode samplers (64.5%) through progressively deeper engagement tiers to platform devotees (2.3%). A secondary finding is the **content maturation signal**: as engagement deepens, content preference shifts from "Edgy" hook-driven romance (28% of sampler watchtime) toward "Forbidden Love" (24%) and "Secret Lives" (13%) — deeper, more emotionally complex narratives.

| Metric | Target | Achieved |
|--------|--------|----------|
| Persona Coverage | ≥75% of 3s streamers | 100% |
| Cluster Separation | Silhouette ≥ 0.3 | 0.43 |
| Hypothesis Alignment | ≥4 of 6 validated | 4 of 6 |
| Demographic Overlay | ≥90% | 99.5% |
| Interest Tag Coverage | — | 83.4% |
| Hierarchical ARI | >0.5 = stable | 0.75 |

---

## Methodology

### Data Sources
| Table | Purpose | Records |
|-------|---------|---------|
| fatafat.mxp_fatafat_player_engagement | Streaming events, engagement, sessions | ~46M stream events (7 days) |
| daily_cms_data_table | Content metadata — shows, genres, secondary genres, source, origin, maturity | 21K Fatafat video records |
| mxp_age_gender_details_table_v3 | Demographics — age/gender | 228M users (99.5% match) |
| mxp_persona_details_table_v3 | Interest segments — ML-derived | 181M users (83.4% match) |

### Clustering Dimensions (5)
1. **Engagement Depth:** Total minutes, MPC, streams, active days, sessions, episodes per session
2. **Content Preference:** Shows watched, genre breadth, show concentration, genre cluster, content source (Intl Dubbed / Original / Partner / Repack), content origin (International / Hindi)
3. **Retention Profile:** Max episode depth (CMS episode_number), lock boundary survival (Ep5→6), binge propensity
4. **Demographics:** Age group, gender, age×gender interaction
5. **Channel & Interest:** Primary channel (Paid/Organic/Push), interest tag count, 8 interest category flags

### Algorithm
- **Primary:** K-Means (k=6), one-hot encoding for categoricals, StandardScaler for numerics
- **Validation:** Agglomerative Hierarchical Clustering (Ward linkage) — ARI = 0.75
- **Feature matrix:** 1,922,238 users × 45 features (23 numeric + 22 one-hot)

### Content Identity: Two-Level Enrichment (Post-Clustering)

Secondary genre (`secondary_genre_name` — 18 values: Edgy, Forbidden Love, Secret Lives, Revenge, Melodrama, etc.) was tested as a clustering input (Phase 2.3) but degraded cluster quality (silhouette dropped from 0.43 to 0.11) because most users watch only 1-2 shows, making their genre distribution binary and noisy.

Instead, secondary genre is applied as **post-clustering enrichment**:
- **Level 1 (Theme):** Per-cluster secondary genre distribution by watchtime — shows what content themes each persona gravitates toward
- **Level 2 (Archetype):** Derived from top 10 shows per cluster — their names, genres, and narrative patterns — to produce a human-readable content archetype

This approach preserves strong cluster statistics while adding rich content differentiation. See `phase2_execution_plan.md` for full methodology documentation.

### Iterative Refinement History

| Phase | Change | Silhouette | ARI | Hypotheses |
|-------|--------|-----------|-----|------------|
| 2.0 | k=4, basic features | 0.46 | 0.61 | 3/6 |
| 2.1 | + persona tags, k=6 | 0.42 | 0.65 | 4/6 |
| 2.2 | + content source/origin | 0.43 | 0.75 | 4/6 ← **selected** |
| 2.3 | + secondary genre one-hot | 0.11 | 0.38 | 5/6 (rejected — weak clusters) |
| Final | 2.2 clusters + two-level content enrichment | 0.43 | 0.75 | 4/6 |

---

## The Engagement Ladder

```
  CONVERT (64.5%)        GROW (18.3%)         NOURISH (17.9%)                    SUSTAIN (2.3%)
┌─────────────────┐  ┌─────────────────┐  ┌──────────────────────────────┐  ┌─────────────────┐
│ Discovery       │  │ Male Crossover  │  │ Romance    Engaged   Power  │  │ Platform        │
│ Sampler         │  │ Viewer          │  │ Binger     Explorer  User   │  │ Devotee         │
│ 1.2M users      │  │ 351K users      │  │ 226K       61K      44K    │  │ 44K users       │
│ 2 min/wk        │  │ 2 min/wk        │  │ 103 min    125 min  630 min│  │ 630 min/wk      │
│ 1.2 shows       │  │ 1.2 shows       │  │ 3.5        3.8      14.7   │  │ 14.7 shows      │
│ 8% lock         │  │ 9% lock         │  │ 100%       100%     100%   │  │ 100% lock       │
│ 53% paid        │  │ 51% paid        │  │ 30%        25%      14%    │  │ 14% paid        │
│ 58% male        │  │ 64% male        │  │ 72% F      64% F    82% F  │  │ 82% female      │
│                 │  │                 │  │                              │  │                 │
│ Edgy 28%        │  │ Edgy 27%        │  │ ForbLove   ForbLove ForbLove│  │ ForbLove 24%    │
│ ForbLove 23%    │  │ ForbLove 22%    │  │ 22%        23%      24%    │  │ SecretLives 13% │
│ Hook-Driven     │  │ Hook-Driven     │  │ Hook-Drv   Hook-Drv CEO/   │  │ CEO/Billionaire │
│ Romance         │  │ Romance         │  │ Romance    Romance  Billion│  │ Romance         │
└─────────────────┘  └─────────────────┘  └──────────────────────────────┘  └─────────────────┘
```

**Content maturation signal:** As engagement deepens, the dominant content theme shifts:
- Samplers: **Edgy** (28%) — provocative hooks, first-episode bait
- Engaged tiers: **Forbidden Love** overtakes Edgy (22-24%) — deeper emotional investment
- Devotees: **Secret Lives** rises to 13% (vs 6% in samplers) — complex narrative mystery
- **Melodrama** and **Revenge** remain steady (11-16%) across all tiers

---

## Strategic Role Assignment

| Role | Criteria | Content Signal |
|------|----------|----------------|
| **CONVERT** | Largest segment, minimal engagement, high churn | Strong onboarding, hook-driven first episodes |
| **GROW** | Large, low engagement, distinct demographic potential | Genre expansion, male-appeal content, Hindi originals |
| **NOURISH** | Mid-size, deep engagement, 100% lock survival | Catalog breadth, franchise content, recommendation quality |
| **SUSTAIN** | Small, highest engagement, commercially most valuable | Release cadence, long-tail freshness, churn prevention |

---

## The 5 Personas

### Persona 1: Discovery Sampler [CONVERT]

| | |
|---|---|
| **Cluster** | 0 |
| **Size** | 1,239,814 users (64.5%) |
| **Strategic Role** | CONVERT |
| **Content Archetype** | Hook-Driven Romance |
| **Retention Signature** | Early Exit (pre-lock) |

**Engagement:** 2 min/wk | 2 MPC | 1.1 active days | 1.2 shows
**Retention:** 3 max ep | 8% lock survival | 2.1 eps/session

**Content Identity:**
| Level | Detail |
|-------|--------|
| Theme (L1) | Edgy (28%), Forbidden Love (23%), Revenge (12%), Melodrama (11%), Crime (6%) |
| Archetype (L2) | Hook-Driven Romance — provocative first episodes, high-concept hooks |
| Source | Intl Dubbed (87%), Original (5%), Repack (5%) |
| Origin | International (87%), Hindi (13%) |
| Top Shows | Why Do You Love Me? (131K), My Cursed Kiss (103K), His Allergic Love (78K), I Won His Heart (74K), Ek Badnaam Aashram (68K) |

**Demographics:** 42% F / 58% M | 44% 18-24 | 34% 25-34 | 22% 35+
Top cells: M_25-34 (26%), F_18-24 (25%), M_18-24 (19%)

**Channel:** Paid 53% | Organic 26% | Push 13%

**Commercial:** Tags 100% | Fashion/Beauty (100%), Electronics/Tech (100%), Home/Kitchen (99%)

**Strategic Implication:** 3 out of 5 weekly users watch one episode and leave. "Edgy" content (provocative hooks) dominates — these users are attracted by the bait but don't commit. The 1→2 show transition is the highest-leverage conversion point. Converting 5% to the Romance Binger tier = +62K engaged users.

---

### Persona 2: Male Crossover Viewer [GROW]

| | |
|---|---|
| **Cluster** | 3 |
| **Size** | 351,187 users (18.3%) |
| **Strategic Role** | GROW |
| **Content Archetype** | Hook-Driven Romance |
| **Retention Signature** | Early Exit (pre-lock) |

**Engagement:** 2 min/wk | 2 MPC | 1.1 active days | 1.2 shows
**Retention:** 3 max ep | 9% lock survival | 2.1 eps/session

**Content Identity:**
| Level | Detail |
|-------|--------|
| Theme (L1) | Edgy (27%), Forbidden Love (22%), Revenge (13%), Melodrama (11%), Crime (6%) |
| Archetype (L2) | Hook-Driven Romance — but with Hindi crime content in top shows |
| Source | Intl Dubbed (85%), Original (5%), Repack (5%) |
| Origin | International (85%), Hindi (15%) — highest Hindi share of any persona |
| Top Shows | Why Do You Love Me? (49K), My Cursed Kiss (23K), **Ek Badnaam Aashram (22K)**, I Married A Mystery (19K), His Allergic Love (18K) |

**Demographics:** 34% F / **64% M** | 27% 18-24 | **50% 25-34** | 21% 35+
Top cells: **M_25-34 (35%)**, F_25-34 (15%), M_18-24 (14%)

**Channel:** Paid 51% | Organic 29% | Push 15%

**Commercial:** Tags 24% | **Electronics/Tech (71%)**, Fashion/Beauty (68%), **Affluent/Premium (36%)**

**Strategic Implication:** The male audience opportunity. M25-34 is the dominant cell (35%). Ek Badnaam Aashram (Hindi crime) in top 3 shows signals appetite for Hindi originals. Highest Hindi content share (15%) and highest Affluent/Premium affinity (36%) of any persona. Low tag coverage (24%) = newer/non-Amazon users. Content signal: male-appeal genres, Hindi originals, action/thriller.

---

### Persona 3: Romance Binger [NOURISH]

| | |
|---|---|
| **Cluster** | 1 |
| **Size** | 225,968 users (11.8%) |
| **Strategic Role** | NOURISH |
| **Content Archetype** | Hook-Driven Romance (transitioning to Forbidden Love) |
| **Retention Signature** | Deep Binger |

**Engagement:** 103 min/wk | 51 MPC | 2.2 active days | 3.5 shows
**Retention:** 61 max ep | 100% lock survival | 28.0 eps/session

**Content Identity:**
| Level | Detail |
|-------|--------|
| Theme (L1) | **Forbidden Love (22%)**, Edgy (19%), Melodrama (17%), Revenge (16%), Secret Lives (10%) |
| Archetype (L2) | Hook-Driven Romance transitioning to deeper emotional content |
| Source | Intl Dubbed (95%), Partner (3%), Original (2%) |
| Origin | International (95%), Hindi (5%) |
| Top Shows | Our Love Is The Ocean Of Stars (51K), Mr. Huo (37K), Why Do You Love Me? (36K), Back From My Funeral (32K), Lucky Trio: CEO Daddy (26K) |

**Demographics:** **72% F** / 28% M | **56% 18-24** | 28% 25-34 | 16% 35+
Top cells: **F_18-24 (46%)**, F_25-34 (17%), M_25-34 (11%)

**Channel:** Organic 67% | Paid 30% | Push 1%

**Commercial:** Tags 100% | Fashion/Beauty (100%), Electronics/Tech (100%), Home/Kitchen (99%)

**Strategic Implication:** The first engaged tier. 100% lock survival — they've committed past the paywall. Content theme shifts from Edgy to Forbidden Love + Melodrama — deeper emotional investment. 3.5 shows means they've discovered multiple titles. Content signal: breadth within romance/empowerment, "if you liked X try Y" recommendations, franchise content.

---

### Persona 4: Engaged Explorer [NOURISH]

| | |
|---|---|
| **Cluster** | 5 |
| **Size** | 61,215 users (3.2%) |
| **Strategic Role** | NOURISH |
| **Content Archetype** | Hook-Driven Romance (cross-age) |
| **Retention Signature** | Deep Binger |

**Engagement:** 125 min/wk | 58 MPC | 2.3 active days | 3.8 shows
**Retention:** 65 max ep | 100% lock survival | 32.0 eps/session

**Content Identity:**
| Level | Detail |
|-------|--------|
| Theme (L1) | Forbidden Love (23%), Edgy (19%), Melodrama (16%), Revenge (16%), Secret Lives (10%) |
| Archetype (L2) | Hook-Driven Romance — similar to Romance Binger but older demographic |
| Source | Intl Dubbed (95%), Partner (3%), Original (2%) |
| Origin | International (95%), Hindi (5%) |
| Top Shows | Our Love Is The Ocean Of Stars (15K), Mr. Huo (11K), Why Do You Love Me? (11K), Lucky Trio (8K), Back From My Funeral (8K) |

**Demographics:** 64% F / 34% M | 38% 18-24 | **42% 25-34** | 18% 35+
Top cells: **F_18-24 (26%), F_25-34 (26%)**, M_25-34 (16%)

**Channel:** Organic 73% | Paid 25% | Push 1%

**Commercial:** Tags 22% | Fashion/Beauty (61%), Electronics/Tech (56%), Home/Kitchen (25%)

**Strategic Implication:** The cross-age engaged viewer. Unlike the Romance Binger (F_18-24 dominant), this persona's top cells are split equally between F_18-24 and F_25-34. Similar content preferences but older. Low tag coverage (22%) suggests non-Amazon-identified users. Content signal: content that bridges age groups, empowerment themes.

---

### Persona 5: Platform Devotee [SUSTAIN]

| | |
|---|---|
| **Cluster** | 2 |
| **Size** | 44,047 users (2.3%) |
| **Strategic Role** | SUSTAIN |
| **Content Archetype** | CEO/Billionaire Romance |
| **Retention Signature** | Full Completer |

**Engagement:** 630 min/wk (10.5 hrs) | 143 MPC | 4.8 active days | 14.7 shows
**Retention:** 97 max ep | 100% lock survival | 52.6 eps/session | 2.97 binge propensity

**Content Identity:**
| Level | Detail |
|-------|--------|
| Theme (L1) | **Forbidden Love (24%)**, Edgy (17%), Melodrama (14%), **Revenge (13%), Secret Lives (13%)** |
| Archetype (L2) | **CEO/Billionaire Romance** — the only persona with a distinct archetype |
| Source | **Intl Dubbed (98%)** — almost exclusively dubbed content |
| Origin | International (98%), Hindi (2%) |
| Top Shows | Our Love Is The Ocean Of Stars (23K), **Lucky Trio: CEO Daddy (20K)**, **Flash Marriage: Mrs. Gu's (20K)**, Back From My Funeral (18K), **The Cold CEO's Torturous Love Game (18K)** |

**Demographics:** **82% F** / 18% M | 56% 18-24 | 28% 25-34 | 16% 35+
Top cells: **F_18-24 (49%)**, F_25-34 (21%), M_18-24 (8%)

**Channel:** **Organic 86%** | Paid 14%

**Commercial:** Tags 91% | Fashion/Beauty (99%), Electronics/Tech (99%), Home/Kitchen (97%)

**Strategic Implication:** The platform's most valuable viewers. 44K users watching 10.5 hours/week across 15 shows, nearly 5 days a week, 86% organic. The ONLY persona with a distinct content archetype — CEO/Billionaire Romance (Lucky Trio, Flash Marriage, Cold CEO). Their top shows are deeper-catalog titles. Secret Lives (13%) is 2x the sampler rate — they seek narrative complexity. Content freshness and release cadence are the priority. Losing 10% of this segment would be visible in platform metrics.

---

## Content Maturation Signal

The most actionable content insight from the two-level analysis is the **theme shift as engagement deepens**:

| Secondary Genre | Samplers (C0) | Male Cross. (C3) | Romance Binger (C1) | Explorer (C5) | Devotee (C2) | Trend |
|---|---|---|---|---|---|---|
| **Edgy** | **28%** | 27% | 19% | 19% | 17% | ↓ Declines with engagement |
| **Forbidden Love** | 23% | 22% | 22% | 23% | **24%** | → Stable, slight rise |
| **Melodrama** | 11% | 11% | **17%** | **16%** | 14% | ↑ Rises in engaged tiers |
| **Revenge** | 12% | 13% | **16%** | **16%** | 13% | ↑ Rises then stabilizes |
| **Secret Lives** | 6% | 5% | 10% | 10% | **13%** | ↑↑ Doubles from sampler to devotee |
| **Crime** | 6% | 6% | 2% | 2% | 1% | ↓ Drops sharply in engaged tiers |

**Interpretation:**
- "Edgy" content is the **acquisition hook** — it attracts first-time viewers but doesn't retain them
- "Forbidden Love" is the **universal backbone** — stable across all engagement levels
- "Melodrama" and "Revenge" are the **engagement deepeners** — they rise as users commit
- "Secret Lives" is the **loyalty signal** — it doubles from samplers to devotees, indicating appetite for narrative complexity
- "Crime" is the **sampler genre** — high in low-engagement tiers, drops sharply in engaged tiers (these users don't convert)

**Content strategy implication:** Commission more "Melodrama" and "Secret Lives" content to serve the engaged tiers. "Edgy" content drives acquisition but doesn't build loyalty. "Crime/Thriller" content attracts samplers who don't convert — ROI on this genre is lower than it appears from reach numbers.

---

## Coverage Validation

| Metric | Value | Assessment |
|--------|-------|------------|
| Persona Coverage | 100% (1,922,231 of 1,922,238) | 7 outlier users in discarded cluster |
| Silhouette Score | 0.43 | Well above 0.3 target |
| Hierarchical ARI | 0.75 | High cross-method stability |
| Hypotheses Validated | 4/6 | Meets target |
| Demographic Overlay | 99.5% | Excellent |
| Interest Tag Coverage | 83.4% | Good (16.6% untagged = newer users) |

### Hypothesis Validation

| # | Hypothesis | Status | Cluster | Notes |
|---|-----------|--------|---------|-------|
| P1 | Young Female Romance Binger | ✅ | C1, C5 | Romance Binger + Engaged Explorer |
| P2 | Male Crossover Viewer | ✅ | C3 | 64% male, M_25-34 dominant, Hindi content signal |
| P3 | Discovery Sampler | ✅ | C0 | 64.5% of audience, 2 min/wk |
| P4 | Multi-Show Power User | ✅ | C1, C2, C5 | Three engagement tiers above sampling |
| P5 | Mature Loyal Viewer | ❌ | — | 35+ viewers distributed 15-22% across all clusters |
| P6 | Hindi Content Explorer | ❌ | — | Sub-segment of Male Crossover (15% Hindi). Phase 2.3 found 330-user cluster at 95% Hindi but too small to be actionable |

**P5 explanation:** Age does not create a distinct behavioral segment on Fatafat. 35+ viewers follow the same engagement gradient as younger viewers. They should be addressed as a demographic overlay, not a separate persona.

**P6 explanation:** Hindi content viewers are absorbed into the Male Crossover persona (15% Hindi origin, Ek Badnaam Aashram in top 3). When forced to separate (Phase 2.3), only 330 users emerged — too small. Hindi originals are the content lever for the Male Crossover segment, not a standalone audience.

---

## Commercial Profiles

### CVI-Weighted Priority Matrix

| Persona | Role | CVI | Users | Top Advertiser Vertical |
|---------|------|-----|-------|------------------------|
| Platform Devotee | SUSTAIN | 100 | 44K | Fashion/Beauty (99%) |
| Romance Binger | NOURISH | ~95 | 226K | Fashion/Beauty (100%) |
| Engaged Explorer | NOURISH | ~94 | 61K | Fashion/Beauty (61%) |
| Discovery Sampler | CONVERT | ~36 | 1.2M | Broad — all categories 99%+ |
| Male Crossover | GROW | ~20 | 351K | **Electronics/Tech (71%), Affluent/Premium (36%)** |

**Key commercial insight:** The Male Crossover Viewer has the most differentiated commercial profile. Electronics/Tech and Affluent/Premium index meaningfully above Fashion/Beauty — unique among all personas. This is a targetable advertiser story for Samsung, OnePlus, Apple, Tanishq seeking the male 25-34 demographic.

### Advertiser Category Affinity

| Vertical | Key Advertisers | Best Persona Fit |
|----------|----------------|-----------------|
| Fashion & Beauty | Nykaa, Myntra, AJIO, Lakme, Mamaearth | Romance Binger, Devotee (99-100%) |
| Consumer Electronics | Samsung, OnePlus, Xiaomi, Boat | **Male Crossover (71%)** — unique differentiator |
| Premium & Luxury | Apple, Tanishq, Titan | **Male Crossover (36%)** — highest of any persona |
| Home & Household | Asian Paints, Godrej, Prestige | Sampler, Devotee (97-99%) |
| Travel & Hospitality | MakeMyTrip, Goibibo, OYO | Broad (91-95% in engaged tiers) |
| Parenting & Childcare | FirstCry, Pampers | Low in Male Crossover (7%) — gender gap |

---

## Implications for Content Strategy

### By Strategic Role

**CONVERT (Discovery Sampler — 64.5%)**
- The 1→2 show transition is the single highest-leverage metric
- "Edgy" content drives 28% of their watchtime — it attracts but doesn't retain
- Content investment: strong first-episode hooks + recommendation-driven second-show discovery
- Converting 5% to Romance Binger tier = +62K engaged users

**GROW (Male Crossover — 18.3%)**
- The untapped male audience. 64% male, 50% aged 25-34
- Hindi content (Ek Badnaam Aashram) in top 3 — signals appetite for Hindi originals
- Electronics/Tech + Affluent/Premium = premium advertiser opportunity
- Content investment: male-appeal genres, Hindi originals, action/thriller

**NOURISH (Romance Binger + Engaged Explorer — 15.0%)**
- Two tiers of engaged viewers, both 100% lock survival
- Content theme shifts to Forbidden Love + Melodrama — deeper emotional content
- Explorer skews older (F_25-34 co-dominant) — content that bridges age groups
- Content investment: catalog breadth, franchise content, "if you liked X" recommendations

**SUSTAIN (Platform Devotee — 2.3%)**
- 44K users, 10.5 hrs/week, 15 shows, 86% organic
- The ONLY persona with a distinct archetype: CEO/Billionaire Romance
- Secret Lives at 13% (2x sampler rate) — they seek narrative complexity
- Their top shows are leading indicators of what broader audience will discover next
- Content investment: release cadence, long-tail freshness, new show pipeline

---

## Phase 2 Deliverables

| Deliverable | File | Description |
|-------------|------|-------------|
| This report | Phase_2_Persona_Construction_Report_Final.md | Complete findings with two-level content identity |
| Final persona cards | persona_cards_final.txt | Machine-generated cards (quick reference) |
| Final feature matrix | fatafat_personas_final.csv | 1.9M users with cluster + archetype assignments |
| Execution plan | phase2_execution_plan.md | Full methodology incl. content enrichment rationale |
| Dashboard | dashboard/index.html | Interactive HTML visualization |
| SQL queries | phase2_queries.sql | All Redshift queries |
| Phase 2.2 clustering | phase2_2_enriched.py | Base clustering pipeline |
| Content enrichment | phase2_final_content_enrichment.py | Two-level content identity enrichment |
| Persona tags export | export_persona_tags.py | Interest tag aggregation |
| CMS enriched data | q22b_cms_enriched.csv | CMS with source, origin, maturity fields |

---

## Phase 3 Readiness

The 5 personas provide all inputs required for Phase 3 (AI Model Training):
- **Training targets:** Each persona becomes a pseudo-viewer model
- **Content identity:** Two-level content profiles define what each persona responds to
- **Retention signatures:** Episode depth + lock survival + binge propensity per persona = ground truth for calibration
- **Content maturation signal:** The Edgy → Forbidden Love → Secret Lives progression provides a testable prediction framework

**Recommended Phase 3 kickoff:** Following stakeholder review and sign-off on the persona set.

---

*Synthetic Personas — Phase 2: Persona Construction Report (Final)*
*Amazon MX Player | Fatafat Micro-Drama Vertical*
*Generated: April 8, 2026 | Data Source: AMXP-BI-MCP-PROD Redshift | CONFIDENTIAL*


---

## Slate Gap Analysis: Acquisition Recommendations

### Demand vs Supply by Secondary Genre

The following analysis compares watchtime share (demand) against catalog share (supply) per secondary genre to identify acquisition gaps and oversupply.

| Genre | Demand (Watchtime %) | Supply (Catalog %) | Gap Ratio | Signal |
|-------|---------------------|-------------------|-----------|--------|
| **Melodrama** | **15.2%** | 6.5% (25 shows) | **2.3x** | 🟢🟢 PRIORITY BUY |
| **Forbidden Love** | **23.1%** | 12.5% (48 shows) | **1.9x** | 🟢 BUY MORE |
| **Revenge** | **14.5%** | 8.8% (34 shows) | **1.6x** | 🟢 BUY MORE |
| Edgy | 18.3% | 14.3% (55 shows) | 1.3x | 🟡 Balanced |
| Secret Lives | 11.2% | 10.4% (40 shows) | 1.1x | 🟡 Balanced |
| Hidden Identity | 4.3% | 4.4% (17 shows) | 1.0x | 🟡 Balanced |
| Time Travel | 1.5% | 2.3% (9 shows) | 0.7x | 🔴 Oversupplied |
| Inheritance | 3.1% | 6.0% (23 shows) | 0.5x | 🔴 Oversupplied |
| Inspiring | 2.5% | 4.9% (19 shows) | 0.5x | 🔴 Oversupplied |
| Pulp | 2.0% | 4.9% (19 shows) | 0.4x | 🔴 Oversupplied |
| **Second Chances** | 3.4% | **8.3% (32 shows)** | **0.4x** | 🔴 STOP BUYING |
| **Crime** | 0.6% | **5.7% (22 shows)** | **0.1x** | 🔴 STOP BUYING |
| Horror | 0.1% | 1.3% (5 shows) | 0.1x | 🔴 Oversupplied |

### Per-Persona Gap Highlights

**Melodrama** is undersupplied for every persona:
- Romance Binger: 2.55x gap (16.6% demand vs 6.5% supply)
- Engaged Explorer: 2.49x gap
- Platform Devotee: 2.18x gap
- Discovery Sampler: 1.65x gap

**Crime** is the worst-performing genre in the catalog:
- 22 shows (5.7% of catalog) generating only 0.6% of watchtime
- Drops from 6% in samplers to 1% in devotees — these viewers don't convert
- Every Crime show acquired is a low-ROI investment

### Content Source Analysis

| Source | Catalog Share | Watchtime Share | Ratio | Assessment |
|--------|-------------|----------------|-------|------------|
| International Dubbed | 51.4% | **95.8%** | 1.86x | The platform's lifeline. Demand far exceeds catalog share. |
| Partner Studios | 22.9% | 2.2% | 0.10x | 23% of catalog, 2% of watchtime. Low ROI. |
| Fatafat Originals | 13.5% | 1.5% | 0.11x | Low watchtime but serves Male Crossover (5.3% of their demand) |
| Repack | 4.2% | 0.5% | 0.12x | Minimal demand |

**Key insight:** International Dubbed content (primarily Mandarin) is 51% of the catalog but drives 96% of watchtime. The dubbed content pipeline is the single most important acquisition lever. Partner studio content (Reelies, Pratilipi, Reelsaga) occupies 23% of catalog slots but generates only 2% of watchtime — a significant opportunity cost.

**Exception — Hindi Originals:** While only 1.5% of overall watchtime, Hindi content serves the Male Crossover persona specifically (5.3% of their watchtime, Ek Badnaam Aashram in top 3 shows). The ROI case for Hindi investment is audience diversification (unlocking the 351K male 25-34 segment), not watchtime volume.

### Acquisition Playbook

**Buy more:**
1. **Melodrama** (dubbed) — highest gap at 2.3x. Only 25 shows serving 15.2% of demand. Every persona benefits.
2. **Forbidden Love** (dubbed) — largest absolute demand at 23.1%. 48 shows isn't enough. Universal backbone genre.
3. **Revenge / Power Struggles** (dubbed) — 1.6x gap. Strong in engaged tiers (16% for Romance Binger + Explorer).

**Stop buying:**
1. **Crime** — 22 shows, 0.6% watchtime. 0.11x ratio. These viewers don't convert.
2. **Second Chances** — 32 shows, 3.4% watchtime. 0.41x ratio. Oversupplied.
3. **Pulp** — 19 shows, 2.0% watchtime. 0.41x ratio.

**Rebalance:**
1. Shift Partner Studio slots toward dubbed Melodrama/Forbidden Love content
2. Maintain Hindi Original pipeline for Male Crossover audience diversification
3. Edgy content is balanced (1.3x) — don't add more, but don't cut either. It's the acquisition hook.


---

## Appendix C: Tiered Commercial Profiles (Amazon vs ML Tags)

### Finding: ML Tags Over-Predict Interest Categories

The ML persona model assigns 95-100% of users to nearly every interest category, making the tags undifferentiated and commercially useless for precision targeting. Amazon-sourced tags (derived from actual shopping behavior on Amazon) show much more realistic and differentiated rates.

| Category | ML Rate (predicted) | Amazon Rate (actual) | ML Over-Prediction |
|----------|-------------------|---------------------|-------------------|
| Travel | 95% | 50-79% | +16 to +44 points |
| Parents/Baby | 92% | 54-80% | +12 to +38 points |
| Automotive | 97% | 63-84% | +10 to +34 points |
| Home/Kitchen | 99% | 69-88% | +11 to +30 points |
| Fashion/Beauty | 100% | 85-97% | +3 to +14 points |
| Electronics/Tech | 100% | 93-98% | +2 to +6 points |

### Tag Source Distribution by Persona

| Persona | Amazon Tags | ML Tags | Both | None |
|---------|------------|---------|------|------|
| Discovery Sampler | 3% | 100% | 3% | 0% |
| Romance Binger | 3% | 100% | 3% | 0% |
| Platform Devotee | 12% | 92% | 4% | 0% |
| Male Crossover | 83% | 24% | 9% | 3% |
| Engaged Explorer | 85% | 22% | 9% | 2% |

The Male Crossover and Engaged Explorer personas are primarily Amazon-identified users (75% Amazon-only). Their sparse ML coverage (22-24%) is because these users entered the platform through Amazon channels and were never profiled by the ML model. For these personas, Amazon tags are the only reliable commercial signal.

### Agreement Analysis (81K Users with Both Sources)

For the 81,130 users who have both Amazon and ML tags, agreement varies dramatically by category:

| Category | Agreement | Assessment |
|----------|-----------|------------|
| Electronics/Tech | 78% | Good — both sources agree |
| Fashion/Beauty | 73% | Good |
| Health/Fitness | 46% | Poor — ML over-predicts |
| Affluent/Premium | 44% | Poor |
| Home/Kitchen | 44% | Poor |
| Parents/Baby | 38% | Poor |
| Travel | 30% | Very poor |
| Automotive | 4% | Essentially random — ML is unreliable |

### Recommendation

Use Amazon-sourced rates as the primary commercial signal where available (83-85% of Male Crossover and Engaged Explorer). For Discovery Sampler and Romance Binger (97% ML-only), flag commercial profiles as "predicted — lower confidence" and apply a deflation factor based on the Amazon vs ML divergence observed in overlap users.

The most commercially actionable insight: the Male Crossover persona's Amazon profile shows genuine high interest in Automotive (83%), Affluent/Premium (86%), and Health/Fitness (88%) — categories that the ML model almost completely misses for this segment. This is a real advertiser targeting opportunity that was invisible in the ML-only analysis.


---

## Appendix D: OTT Cross-Platform Overlap Analysis

### Overall Overlap

54.6% of Fatafat's 1.9M weekly streamers also watch OTT content on the main MX Player platform in the same 7-day window. This cross-platform behavior varies dramatically by persona.

### Per-Persona OTT Profile

| Persona | OTT Overlap | OTT min/wk | FF min/wk | FF/OTT Ratio | Platform Type |
|---------|------------|------------|----------|-------------|---------------|
| Platform Devotee | 84.8% | 265 | 636 | 2.40x | **Fatafat-native** |
| Romance Binger | 75.0% | 266 | 107 | 0.40x | OTT-primary |
| Engaged Explorer | 72.8% | 272 | 131 | 0.48x | OTT-primary |
| Discovery Sampler | 51.1% | 155 | 2 | 0.01x | OTT-primary |
| Male Crossover | 46.9% | 159 | 2 | 0.01x | OTT-primary |

The Platform Devotee is the ONLY persona that watches more Fatafat than OTT (2.4x ratio). Every other persona is OTT-primary — they spend more time on the main platform than on Fatafat. The Samplers and Male Crossover barely engage with Fatafat (2 min/wk) but watch 155-159 min/wk on OTT — they're OTT users who sampled Fatafat and didn't stick.

### OTT Genre Preferences (% of overlap users)

| Genre | Sampler | Male Cross. | Romance | Explorer | Devotee |
|-------|---------|------------|---------|----------|---------|
| Drama | 78% | 75% | 80% | 80% | 86% |
| Romance | 67% | 62% | 85% | 84% | 91% |
| Comedy | 56% | 54% | 68% | 63% | 73% |
| Vdesi (Dubbed) | 56% | 53% | 83% | 83% | 90% |
| Action/Crime | 38% | 37% | 30% | 27% | 32% |
| Fantasy/Sci-Fi | 30% | 28% | 45% | 44% | 50% |
| Thriller/Horror | 20% | 19% | 17% | 15% | 16% |
| Anime | 7% | 7% | 7% | 7% | 6% |

### Content Gap Signals

**Comedy is the biggest cross-platform content gap.** 54-73% of every persona watches Comedy on OTT, but Fatafat has zero Comedy content in its catalog. This is a clear acquisition signal — Comedy micro-dramas could serve every persona.

**Vdesi (dubbed long-form)** is watched by 53-90% of overlap users on OTT. These are the same dubbed international content fans who watch Fatafat's micro-dramas, but they also consume long-form dubbed content. This validates the dubbed content pipeline as the platform's core.

**Action/Crime** is watched by 27-38% on OTT. Fatafat has Crime content (which doesn't convert per the slate gap analysis), but not Action. Action micro-dramas could serve the Male Crossover persona specifically.

**Fantasy/Sci-Fi** is watched by 28-50% on OTT, with the highest rates in the engaged tiers (Devotee 50%, Romance Binger 45%). Fatafat has only 16 Fantasy shows — there may be room for more.

### Implication for Content Strategy

The OTT overlap data confirms and extends the slate gap analysis:
1. **Comedy micro-dramas** should be the #1 new genre to acquire — universal demand across all personas
2. **Action micro-dramas** could unlock the Male Crossover segment (37% watch Action on OTT)
3. The Platform Devotee's Fatafat-native behavior (2.4x ratio) confirms they're the micro-drama core — protect this segment with content freshness
4. The Sampler and Male Crossover's OTT-primary behavior (0.01x ratio) means Fatafat is competing for their attention against the full OTT catalog — the hook content needs to be compelling enough to pull them from long-form
