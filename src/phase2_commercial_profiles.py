"""
Phase 2 — Step 4 Completion: Commercial Value Index + Advertiser Category Affinity
===================================================================================
Adds the two missing persona card fields from the implementation plan:
  1. Advertiser category affinity (interest panels → advertiser categories)
  2. Commercial value index (composite score per persona)

Input: fatafat_personas_phase2_1.csv (Phase 2.1 output)
Output: Updated persona cards with commercial profiles appended to report
"""

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

print("=" * 80)
print("PHASE 2 — COMMERCIAL PROFILE COMPLETION")
print("=" * 80)

df = pd.read_csv("fatafat_personas_phase2_1.csv")
print(f"Loaded {len(df):,} users")

# ============================================================
# 1. ADVERTISER CATEGORY AFFINITY MAPPING
# ============================================================
# Map interest panels to advertiser verticals relevant to
# Indian digital advertising market
print("\n--- Advertiser Category Affinity ---")

advertiser_map = {
    'has_fashion_beauty': {
        'vertical': 'Fashion & Beauty',
        'advertisers': 'Nykaa, Myntra, AJIO, Lakme, Mamaearth, Sugar Cosmetics',
        'ad_formats': 'Shoppable ads, brand integrations, influencer-style placements'
    },
    'has_electronics_tech': {
        'vertical': 'Consumer Electronics',
        'advertisers': 'Samsung, OnePlus, Xiaomi, Boat, Noise, realme',
        'ad_formats': 'Product launch sponsorships, tech review integrations'
    },
    'has_health_fitness': {
        'vertical': 'Health & Wellness',
        'advertisers': 'Himalaya, Dabur, HealthKart, Cult.fit, Pharmeasy',
        'ad_formats': 'Wellness content sponsorships, health product placements'
    },
    'has_home_kitchen': {
        'vertical': 'Home & Household',
        'advertisers': 'Asian Paints, Godrej, IFB, Prestige, Urban Ladder',
        'ad_formats': 'Home makeover integrations, lifestyle content sponsorships'
    },
    'has_travel': {
        'vertical': 'Travel & Hospitality',
        'advertisers': 'MakeMyTrip, Goibibo, OYO, IRCTC, Cleartrip',
        'ad_formats': 'Destination content, travel deal placements'
    },
    'has_parents_baby': {
        'vertical': 'Parenting & Childcare',
        'advertisers': 'FirstCry, Pampers, Johnson & Johnson, Huggies, Mothercare',
        'ad_formats': 'Family content sponsorships, parenting tips integrations'
    },
    'has_automotive': {
        'vertical': 'Automotive',
        'advertisers': 'Maruti Suzuki, Hyundai, Tata Motors, Hero MotoCorp',
        'ad_formats': 'Lifestyle integrations, aspirational content sponsorships'
    },
    'has_affluent_premium': {
        'vertical': 'Premium & Luxury',
        'advertisers': 'Apple, Tanishq, Titan, Forest Essentials, premium D2C brands',
        'ad_formats': 'Premium content environments, exclusive sponsorships'
    },
}

# Per-cluster advertiser affinity
for cluster_id in sorted(df['cluster_v2'].unique()):
    c = df[df['cluster_v2'] == cluster_id]
    tagged = c[c['tag_count'] > 0]
    n_tagged = len(tagged)

    print(f"\nCluster {cluster_id} ({len(c):,} users, {n_tagged:,} tagged):")
    if n_tagged < 100:
        print("  Insufficient tag data for advertiser affinity")
        continue

    affinities = []
    for col, info in advertiser_map.items():
        rate = tagged[col].mean() * 100
        affinities.append((info['vertical'], rate, info['advertisers']))

    # Sort by affinity rate descending
    affinities.sort(key=lambda x: -x[1])

    print(f"  Top 3 Advertiser Verticals:")
    for vert, rate, advs in affinities[:3]:
        print(f"    {vert:25s}: {rate:.0f}% affinity → {advs}")
    print(f"  Bottom 2 Advertiser Verticals:")
    for vert, rate, advs in affinities[-2:]:
        print(f"    {vert:25s}: {rate:.0f}% affinity")

# ============================================================
# 2. COMMERCIAL VALUE INDEX (CVI)
# ============================================================
# Composite score per persona estimating relative commercial value.
# Components:
#   - Engagement depth (watchtime drives ad exposure)
#   - Session frequency (more sessions = more ad opportunities)
#   - Interest breadth (more panels = more targetable)
#   - Organic share (organic users have higher LTV than paid)
#   - Lock survival (committed users see more ads through unlock flow)
#
# Normalized 0-100 scale, indexed to platform average = 50.

print("\n" + "=" * 80)
print("COMMERCIAL VALUE INDEX (CVI)")
print("=" * 80)

# Compute raw component scores per user
df['cvi_engagement'] = np.log1p(df['total_minutes'])  # log scale to handle skew
df['cvi_frequency'] = df['active_days'] / 7.0
df['cvi_interest_breadth'] = df['tag_count'] / df['tag_count'].max() if df['tag_count'].max() > 0 else 0
df['cvi_organic'] = (df['primary_channel'] == 'Organic').astype(float)
df['cvi_lock_survival'] = df['lock_survival'].astype(float)

# Weights (engagement and frequency matter most for ad revenue)
weights = {
    'cvi_engagement': 0.30,
    'cvi_frequency': 0.25,
    'cvi_interest_breadth': 0.15,
    'cvi_organic': 0.15,
    'cvi_lock_survival': 0.15,
}

# Normalize each component to 0-1 range
for col in weights:
    col_min = df[col].min()
    col_max = df[col].max()
    if col_max > col_min:
        df[f'{col}_norm'] = (df[col] - col_min) / (col_max - col_min)
    else:
        df[f'{col}_norm'] = 0

# Weighted composite
df['cvi_raw'] = sum(df[f'{col}_norm'] * w for col, w in weights.items())

# Scale to 0-100, indexed so platform mean = 50
platform_mean = df['cvi_raw'].mean()
if platform_mean > 0:
    df['cvi'] = (df['cvi_raw'] / platform_mean) * 50
    df['cvi'] = df['cvi'].clip(0, 100)
else:
    df['cvi'] = 50

# Per-cluster CVI
print("\nCommercial Value Index by Persona:")
print(f"{'Cluster':>8} {'Persona':>30} {'Users':>10} {'CVI':>6} {'vs Avg':>8}")
print("-" * 70)

persona_names = {
    0: 'Male Crossover Viewer',
    1: 'Discovery Sampler',
    2: 'Multi-Show Power User',
    3: 'Engaged Explorer',
    4: 'Platform Devotee',
    5: 'Young Female Romance Binger',
}

platform_cvi = df['cvi'].mean()
for cluster_id in sorted(df['cluster_v2'].unique()):
    c = df[df['cluster_v2'] == cluster_id]
    cvi = c['cvi'].mean()
    name = persona_names.get(cluster_id, f'Cluster {cluster_id}')
    vs_avg = f"+{cvi - platform_cvi:.0f}" if cvi > platform_cvi else f"{cvi - platform_cvi:.0f}"
    print(f"{cluster_id:>8} {name:>30} {len(c):>10,} {cvi:>6.1f} {vs_avg:>8}")

print(f"\nPlatform Average CVI: {platform_cvi:.1f}")

# CVI component breakdown per cluster
print("\n\nCVI Component Breakdown:")
print(f"{'Cluster':>8} {'Engagement':>12} {'Frequency':>12} {'Interest':>12} {'Organic':>12} {'Lock Surv':>12} {'CVI':>8}")
print("-" * 80)
for cluster_id in sorted(df['cluster_v2'].unique()):
    c = df[df['cluster_v2'] == cluster_id]
    print(f"{cluster_id:>8} "
          f"{c['cvi_engagement_norm'].mean()*100:>11.1f}% "
          f"{c['cvi_frequency_norm'].mean()*100:>11.1f}% "
          f"{c['cvi_interest_breadth_norm'].mean()*100:>11.1f}% "
          f"{c['cvi_organic_norm'].mean()*100:>11.1f}% "
          f"{c['cvi_lock_survival_norm'].mean()*100:>11.1f}% "
          f"{c['cvi'].mean():>7.1f}")

# ============================================================
# 3. RETENTION SIGNATURE SUMMARY
# ============================================================
# Formalize the retention signature per persona as specified
# in the implementation plan: "characteristic retention curve shape,
# typical drop-off point, episode completion rate, binge propensity"

print("\n" + "=" * 80)
print("RETENTION SIGNATURES")
print("=" * 80)

print(f"\n{'Cluster':>8} {'Persona':>30} {'Max Ep':>8} {'Avg Ep':>8} {'Lock%':>7} "
      f"{'Eps/Sess':>10} {'Binge':>7} {'Signature':>25}")
print("-" * 110)

for cluster_id in sorted(df['cluster_v2'].unique()):
    c = df[df['cluster_v2'] == cluster_id]
    name = persona_names.get(cluster_id, f'Cluster {cluster_id}')
    max_ep = c['max_episode_depth'].mean()
    avg_ep = c['avg_episode_depth'].mean()
    lock = c['lock_survival'].mean() * 100
    eps_sess = c['avg_episodes_per_session'].mean()
    binge = c['binge_propensity'].mean()

    # Classify retention signature
    if lock < 10:
        sig = "Early Exit (pre-lock)"
    elif max_ep < 30 and eps_sess < 10:
        sig = "Moderate Completer"
    elif max_ep < 60 and binge < 2:
        sig = "Steady Viewer"
    elif max_ep < 90 and binge < 3:
        sig = "Deep Binger"
    else:
        sig = "Full Completer"

    print(f"{cluster_id:>8} {name:>30} {max_ep:>7.0f} {avg_ep:>7.0f} {lock:>6.0f}% "
          f"{eps_sess:>9.1f} {binge:>6.2f} {sig:>25}")

# ============================================================
# 4. FINAL CONSOLIDATED OUTPUT
# ============================================================
print("\n" + "=" * 80)
print("CONSOLIDATED PERSONA SUMMARY TABLE")
print("=" * 80)

summary = pd.DataFrame()
for cluster_id in sorted(df['cluster_v2'].unique()):
    c = df[df['cluster_v2'] == cluster_id]
    tagged = c[c['tag_count'] > 0]
    name = persona_names.get(cluster_id, f'Cluster {cluster_id}')

    # Determine top advertiser vertical
    if len(tagged) > 100:
        top_vert_rates = {}
        for col, info in advertiser_map.items():
            top_vert_rates[info['vertical']] = tagged[col].mean()
        top_vert = max(top_vert_rates, key=top_vert_rates.get)
    else:
        top_vert = "Insufficient data"

    # Retention signature
    lock = c['lock_survival'].mean() * 100
    max_ep = c['max_episode_depth'].mean()
    binge = c['binge_propensity'].mean()
    if lock < 10:
        ret_sig = "Early Exit"
    elif max_ep < 30:
        ret_sig = "Moderate"
    elif max_ep < 60:
        ret_sig = "Steady"
    elif max_ep < 90:
        ret_sig = "Deep Binger"
    else:
        ret_sig = "Full Completer"

    row = {
        'Persona': name,
        'Role': df.loc[df['cluster_v2'] == cluster_id, 'strategic_role_v2'].iloc[0],
        'Users': f"{len(c):,}",
        'Coverage': f"{len(c)/len(df)*100:.1f}%",
        'MPC': f"{c['mpc'].mean():.0f}",
        'Shows': f"{c['unique_shows'].mean():.1f}",
        'Active Days': f"{c['active_days'].mean():.1f}",
        'Lock Surv': f"{lock:.0f}%",
        'Retention': ret_sig,
        'Gender': f"{(c['gender']=='Female').mean()*100:.0f}%F",
        'Top Cell': c['age_gender'].value_counts().index[0],
        'Channel': f"{(c['primary_channel']=='Organic').mean()*100:.0f}% Org",
        'CVI': f"{c['cvi'].mean():.0f}",
        'Top Ad Vertical': top_vert,
    }
    summary = pd.concat([summary, pd.DataFrame([row])], ignore_index=True)

print(summary.to_string(index=False))

# Save updated CSV with CVI
df.to_csv("fatafat_personas_phase2_final.csv", index=False)
print(f"\n✅ Final feature matrix with CVI exported to: fatafat_personas_phase2_final.csv")

# ============================================================
# 5. APPENDIX TO REPORT
# ============================================================
report_appendix = """

## Appendix A: Commercial Value Index (CVI) Methodology

The Commercial Value Index is a composite score (0-100 scale, platform average = 50) estimating the relative commercial value of each persona based on five components:

| Component | Weight | Rationale |
|-----------|--------|-----------|
| Engagement Depth (log watchtime) | 30% | Higher watchtime = more ad exposure opportunities |
| Session Frequency (active days / 7) | 25% | More frequent sessions = more ad impression opportunities |
| Interest Breadth (tag count / max) | 15% | More interest panels = more targetable by diverse advertisers |
| Organic Share (binary) | 15% | Organic users have higher LTV — not dependent on paid re-acquisition |
| Lock Survival (binary) | 15% | Users past the lock boundary see rewarded ads — direct monetization |

Each component is min-max normalized to 0-1, weighted, summed, and scaled so the platform average = 50.

### CVI by Persona

"""

for cluster_id in sorted(df['cluster_v2'].unique()):
    c = df[df['cluster_v2'] == cluster_id]
    name = persona_names.get(cluster_id, f'Cluster {cluster_id}')
    cvi = c['cvi'].mean()
    vs = cvi - platform_cvi
    report_appendix += f"- **{name}**: CVI = {cvi:.0f} ({'+' if vs > 0 else ''}{vs:.0f} vs platform avg)\n"

report_appendix += f"\nPlatform Average CVI: {platform_cvi:.0f}\n"

report_appendix += """
## Appendix B: Advertiser Category Affinity

Interest panel data from ML persona tags mapped to Indian digital advertising verticals:

| Vertical | Key Advertisers | Best Persona Fit |
|----------|----------------|-----------------|
| Fashion & Beauty | Nykaa, Myntra, AJIO, Lakme, Mamaearth | Romance Binger, Power User, Platform Devotee |
| Consumer Electronics | Samsung, OnePlus, Xiaomi, Boat, realme | Male Crossover Viewer (71% affinity, Electronics/Tech top panel) |
| Health & Wellness | Himalaya, Dabur, HealthKart, Cult.fit | Broad affinity across engaged tiers |
| Home & Household | Asian Paints, Godrej, IFB, Prestige | Discovery Sampler (99%), Power User (99%) |
| Travel & Hospitality | MakeMyTrip, Goibibo, OYO, Cleartrip | Broad affinity (91-95% across tagged users) |
| Parenting & Childcare | FirstCry, Pampers, Huggies | Lower affinity in Male Crossover (7%) — gender-driven |
| Automotive | Maruti Suzuki, Hyundai, Hero MotoCorp | Low affinity across all personas (<10% in sparse-tag clusters) |
| Premium & Luxury | Apple, Tanishq, Titan, Forest Essentials | Male Crossover (36% — highest Affluent/Premium index) |

**Key commercial insight:** The Male Crossover Viewer (Cluster 0) has the most differentiated commercial profile — Electronics/Tech and Affluent/Premium index meaningfully above other interest categories. This is a targetable advertiser story for premium consumer electronics and aspirational brands seeking the male 25-34 demographic on a micro-drama platform.
"""

with open("Phase_2_Persona_Construction_Report.md", "a") as f:
    f.write(report_appendix)

print("✅ Appendices A & B appended to Phase_2_Persona_Construction_Report.md")
print("\n🎯 PHASE 2 IS COMPLETE. All 5 steps delivered.")
