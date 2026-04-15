# Persona Card Template & Field Definitions

A standardized schema for Fatafat synthetic persona cards. Each persona card contains 7 sections with defined fields, data sources, and computation logic.

---

## Card Header

| Field | Description | Source | Computation |
|-------|-------------|--------|-------------|
| Cluster ID | K-Means cluster number | `phase2_2_enriched.py` | K-Means assignment |
| Strategic Role | CONVERT / GROW / NOURISH / SUSTAIN | Rule-based | Segment size × engagement depth (see rules below) |
| Persona Name | Human-readable label | Manual / auto-suggested | Derived from dominant traits (demo + content + engagement) |
| User Count | Number of users in cluster | Feature matrix | COUNT of cluster members |
| Coverage % | % of total active Fatafat audience | Feature matrix | cluster_users / total_users × 100 |
| Content Archetype | Narrative-level content identity | `phase2_final_content_enrichment.py` | Derived from top 10 shows + secondary genres (Level 2) |
| Retention Signature | Behavioral commitment label | Computed | Early Exit / Moderate / Steady / Deep Binger / Full Completer |

### Strategic Role Rules (applied in priority order)

| Rule | Role | Criteria |
|------|------|----------|
| 1 | CONVERT | size > 30% AND avg_minutes < 10 |
| 2 | EXPLORE | size < 10% AND avg_minutes < 5 |
| 3 | GROW | size > 15% AND avg_minutes < platform_median |
| 4 | SUSTAIN | avg_minutes > 1.5× platform_median AND active_days > 4 |
| 5 | NOURISH | avg_minutes > platform_median AND lock_survival > 50% |
| 6 | NOURISH (fallback) | avg_minutes > platform_median |
| 7 | GROW (fallback) | everything else |

### Retention Signature Rules

| Label | Criteria |
|-------|----------|
| Early Exit | lock_survival < 10% |
| Moderate | max_episode_depth < 30 |
| Steady Viewer | max_episode_depth < 60 AND binge_propensity < 2 |
| Deep Binger | max_episode_depth < 90 |
| Full Completer | max_episode_depth ≥ 90 |

---

## Section 1: Engagement

| Field | Description | Source Table | Computation |
|-------|-------------|-------------|-------------|
| Minutes/Week | Total watchtime in 7-day window | `fatafat.mxp_fatafat_player_engagement` | SUM(playtime)/60000 per user, then cluster mean |
| MPC | Minutes per consumer per active day | Derived | total_minutes / active_days |
| Active Days | Days with ≥1 stream in 7-day window | Engagement table | COUNT(DISTINCT DATE(start_date)) |
| Shows Watched | Unique shows in window | Engagement + CMS | COUNT(DISTINCT channel_ids) after CMS join |

### Filters Applied
- `event = 'onlineStreamEnd'`
- `CAST(playtime AS FLOAT) >= 3000` (3-second per-stream threshold)
- `networkType IS NOT NULL AND internalNetworkStatus > 1`
- `pagetype = 'titlePage'` (show playbacks only)
- `DATE(start_date) BETWEEN '2026-03-30' AND '2026-04-05'`

---

## Section 2: Retention

| Field | Description | Source | Computation |
|-------|-------------|--------|-------------|
| Max Episode Depth | Highest episode_number reached on any show | CMS `episode_number` | MAX(CAST(episode_number AS INT)) per user per show, then cluster mean of max |
| Lock Survival % | % of users who watched episode ≥ 6 on any show | CMS episode_number | Binary: max_episode_depth ≥ 6. Cluster mean × 100 |
| Episodes/Session | Avg unique episodes per session | Engagement table | COUNT(DISTINCT videoid) per uuid+sid, then user mean, then cluster mean |

### Note on Lock Survival
Episode 5 is the last free episode. Episode 6 requires ad unlock (lock boundary). Lock survival = user committed past the paywall.

---

## Section 3: Content Identity (Two-Level)

### Level 1: Content Theme

| Field | Description | Source | Computation |
|-------|-------------|--------|-------------|
| Secondary Genre Distribution | % of cluster watchtime per secondary genre | CMS `secondary_genre_name` | Per-cluster: SUM(minutes) by secondary_genre / total cluster minutes |

Secondary genres: Edgy, Forbidden Love, Secret Lives, Revenge, Second Chances, Melodrama, Inheritance, Crime, Pulp, Inspiring, Hidden Identity, Time Travel, Horror, Mythical Action, Creature Romance

### Level 2: Content Archetype

| Field | Description | Source | Computation |
|-------|-------------|--------|-------------|
| Archetype | Narrative-level content label | Top 10 shows per cluster | Keyword scoring on show names + secondary genre weighting |

Archetype keywords:
- CEO/Billionaire Romance: ceo, billionaire, president, boss, rich, huo, lucky trio
- Forbidden Love Epic: ocean of stars, royal, closer, ancient, forbidden
- Female Empowerment: unbossed, strength, alone, chain, rising, divorce sisters
- Revenge & Power: funeral, murder, badla, revenge, betrayal
- Hindi Crime/Thriller: aashram, bhaukaal, dharavi, raktanchal, detective
- Mystery & Secrets: secret, mystery, moonlight, scent, hidden
- Marriage Drama: flash marriage, contract, married, wife, husband
- Hook-Driven Romance: cursed kiss, allergic love, love me, fell twice

### Content Source & Origin

| Field | Description | Source | Computation |
|-------|-------------|--------|-------------|
| Content Source | Production/acquisition source | CMS `tag_name` | Mapped: Mandarin/English/Korean → Intl Dubbed, Fatafat Original → Original, Reelies/Pratilipi/Reelsaga/Rusk → Partner, Repack → Repack |
| Content Origin | International vs Hindi | CMS `original_acquired` | Direct mapping |

---

## Section 4: Demographics

| Field | Description | Source Table | Computation |
|-------|-------------|-------------|-------------|
| Gender Split | % Female / % Male | `mxp_age_gender_details_table_v3` | Cluster-level value_counts(normalize=True) |
| Age Distribution | % per age group | Same | 18-24, 25-34, 35+ buckets |
| Top Age×Gender Cells | Top 3 age_gender combinations | Derived | gender[0] + '_' + age_group, value_counts top 3 |

---

## Section 5: Channel

| Field | Description | Source | Computation |
|-------|-------------|--------|-------------|
| Primary Channel | Highest-watchtime channel per user | Engagement `dputmsource` | CASE classification → aggregate by user → ROW_NUMBER by total_playtime |

Channel categories:
- Paid: perf_m, perf_g, fatafat_inmobi, branding_meta, etc. (full list in schema)
- Organic: NULL or empty dputmsource
- Push: mx_internal_notif
- OTT Notification: personal-ott-toast-v3/v4/v5, ott_nudges
- Internal Ad: paid_int-con-perf-dfp, house_int-con-perf-dfp

---

## Section 6: Commercial Profile (Tiered)

| Field | Description | Source Table | Computation |
|-------|-------------|-------------|-------------|
| Tag Source Split | % Amazon only / ML only / Both / None | `mxp_persona_details_table_v3` | Per-user: check if uuid has ml tags, amazon tags, both, or neither |
| Interest Category Rates | % of tagged users with each interest | Same | Per interest category, MAX(CASE WHEN persona_name ILIKE pattern THEN 1) |
| Primary Signal | Which source to trust | Derived | Amazon if ≥50% Amazon coverage, else ML with over-prediction caveat |

Interest categories and their ILIKE patterns:
| Category | Pattern |
|----------|---------|
| Fashion/Beauty | fashion, beauty, grooming, ethnic wear, jewelry, clothing |
| Electronics/Tech | electronics, computer, smartphone, mobile, tablet, tech |
| Health/Fitness | health, fitness, nutrition |
| Home/Kitchen | home, kitchen, appliance |
| Travel | travel |
| Parents/Baby | parent, baby |
| Automotive | automotive |
| Affluent/Premium | affluent, premium |

### ML Over-Prediction Note
ML tags assign 95-100% of users to nearly every category. Amazon tags (actual shopping behavior) show 20-44 points lower rates. Use Amazon rates as primary signal where available. Flag ML-only profiles as "predicted — lower confidence."

---

## Section 7: Cross-Platform (OTT Overlap)

| Field | Description | Source Table | Computation |
|-------|-------------|-------------|-------------|
| OTT Overlap % | % of persona users who also stream OTT | `content_stream_end_table_v2` | COUNT users appearing in both tables / cluster size |
| OTT Minutes/Week | Avg OTT watchtime for overlap users | OTT table | SUM(playtime)/60000 per overlap user, cluster mean |
| Fatafat/OTT Ratio | Relative platform engagement | Derived | avg_fatafat_minutes / avg_ott_minutes |
| Platform Type | Fatafat-native vs OTT-primary | Derived | Ratio > 2 = Fatafat-native, < 0.5 = OTT-primary |
| OTT Content Category | Top content type on OTT | CMS `content_category` | Per overlap user: top category by watchtime. Cluster distribution. |
| OTT Genre Preferences | Genre flags for overlap users | CMS `genre_name` | ILIKE pattern matching on genre_name for action, comedy, romance, etc. |
| Behavioral Split | OTT-overlap vs non-overlap Fatafat engagement | Derived | Compare avg_fatafat_minutes and lock_survival between overlap and non-overlap sub-groups |

### OTT Table Notes
- `content_stream_end_table_v2` contains OTT data only (no Fatafat)
- No networkType/internalNetworkStatus filters needed
- `isfatafat` column is always NULL — do not filter on it
- Join to Fatafat users on `uuid`

---

## Data Flow Summary

```
Redshift Tables:
  fatafat.mxp_fatafat_player_engagement  →  Engagement, Retention, Channel
  daily_cms_data_table                   →  Content Identity (genre, source, episodes)
  mxp_age_gender_details_table_v3        →  Demographics
  mxp_persona_details_table_v3           →  Commercial (ML + Amazon tags)
  content_stream_end_table_v2            →  Cross-Platform (OTT overlap)

Pipeline:
  SQL queries (phase2_queries.sql)  →  7 CSVs
  phase2_2_enriched.py              →  Clustering (k=6, silhouette 0.43)
  phase2_final_content_enrichment.py →  Two-level content identity
  amazon_tags_analysis.py           →  Tiered commercial profiles
  ott_overlap_analysis.py           →  Cross-platform profiles
  slate_gap_analysis.py             →  Demand vs supply gaps
```


---

## Section 8: Geographic Profile (Two-Level)

### Level 1: Regional Split

| Field | Description | Source | Computation |
|-------|-------------|--------|-------------|
| Hindi Belt % | % of persona from UP, Bihar, MP, Rajasthan, Jharkhand, Chhattisgarh, Haryana, Uttarakhand, HP, Delhi | `fatafat.mxp_fatafat_player_engagement.regionname` | Per user: primary state by highest watchtime. Per cluster: count users in Hindi Belt states / total |
| South % | % from Tamil Nadu, Karnataka, Telangana, Kerala, Andhra Pradesh | Same | Same method |
| West % | % from Maharashtra, Gujarat, Goa | Same | Same method |
| East % | % from West Bengal, Odisha, Assam | Same | Same method |

### Level 2: Top Cities

| Field | Description | Source | Computation |
|-------|-------------|--------|-------------|
| Top 5 Cities | Cities with highest user concentration | `fatafat.mxp_fatafat_player_engagement.city` | Per user: primary city by highest watchtime. Per cluster: value_counts top 5 |

### Regional Classification

| Region | States |
|--------|--------|
| Hindi Belt | Uttar Pradesh, Bihar, Madhya Pradesh, Rajasthan, Jharkhand, Chhattisgarh, Haryana, Uttarakhand, Himachal Pradesh, National Capital Territory of Delhi |
| South | Tamil Nadu, Karnataka, Telangana, Kerala, Andhra Pradesh |
| West | Maharashtra, Gujarat, Goa |
| East | West Bengal, Odisha, Assam |

### Key Geo Signal

South India (20-22% of low-engagement personas) drops to 11-13% in engaged personas — these users sample but don't convert. West India (Maharashtra, Gujarat) over-indexes in engaged tiers (25-27% vs 21% in samplers). Tamil Nadu is the biggest under-indexer in engaged personas (7.9% sampler → 3.3% devotee, 0.47x index).
