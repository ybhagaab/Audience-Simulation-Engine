Synthetic Personas — Phase 1: Data Foundation
Working Document | Updated: April 6, 2026

Objective
Extract and validate all behavioral signals from live Fatafat data to build the unified audience dataset required for persona construction (Phase 2).

1. Baseline Streaming Snapshot (Mar 31 – Apr 6, 2026)
Source: fatafat.mxp_fatafat_player_engagement | Threshold: 3-second per-stream
Date
Streamers (3s)
Watchtime (min)
Total Streams
MPC (min)
Mar 31 (Tue)
337,229
7,828,022
7,221,753
23.2
Apr 01 (Wed)
378,202
8,350,860
7,650,382
22.1
Apr 02 (Thu)
385,227
9,687,712
8,882,475
25.1
Apr 03 (Fri)
386,815
9,464,027
8,709,740
24.5
Apr 04 (Sat)
409,753
9,618,626
8,840,353
23.5
Apr 05 (Sun)
398,926
9,128,317
8,417,920
22.9
Apr 06 (Mon)*
84,836
1,408,114
1,270,282
16.6
Apr 6 is partial data (through ~7:28 AM UTC / ~12:58 PM IST).
Key Findings:
	•	Daily 3s streamers range from 337K–410K, with a clear weekday-to-weekend ramp (Saturday peaked at ~410K)
	•	MPC is strong at 22–25 minutes/day — deep engagement per user
	•	Average ~21–23 streams per user per day — consistent with micro-drama short-episode format
	•	Thursday Apr 2 had the highest MPC (25.1 min) — possible strong content release

2. Demographics Breakdown (April 5, 2026)
Source: mxp_age_gender_details_table_v3 joined to Fatafat 3s streamers
Match Rate: 378,471 / ~399K streamers = 95% demographic coverage ✅
Age Group
Female
Male
Total
% of Total
18-24
108,137
55,383
163,520
43.1%
25-34
51,843
83,238
135,081
35.6%
35-44
22,812
29,265
52,077
13.7%
45-54
13,475
11,625
25,100
6.6%
55-64
1,431
1,262
2,693
0.7%
Total
197,698
180,773
378,471
100%
Key Findings:
	•	Female 18-24 is the dominant segment — 108K users (28.6%), the single largest demographic cell
	•	Gender split is nearly even overall (52.2% F vs 47.8% M), but varies sharply by age:
	•	18-24: 66% Female / 34% Male
	•	25-34: 38% Female / 62% Male (flips to male-dominant)
	•	35-44: 44% Female / 56% Male
	•	45-54: 54% Female / 46% Male
	•	78.7% of streamers are under 35 — young audience
	•	35+ audience (20.3%) is a meaningful secondary segment

3. Interest / Persona Segments (April 5, 2026)
Source: mxp_persona_details_table_v3 (ML source only) joined to Fatafat 3s streamers
Persona / Interest Segment
Users
% of Streamers
Demo - Amazon Reach
302,293
75.8%
Fashion or Computers or Electronics
294,634
73.8%
IM - Home Proud - Appliances Electronics & Hardware
293,426
73.5%
IM - Fashion
293,311
73.5%
Jewelry or Wedding Clothing or Fashion
292,623
73.3%
IM - Electronics
290,527
72.8%
IM - Home & Kitchen
289,561
72.6%
Watches or Computers or Electronics
289,160
72.5%
IM - Fitness Nutrition and Health Care
287,845
72.1%
Automotive or Electronics
287,613
72.1%
IM - Beauty Enthusiasts
287,359
72.0%
LS - Womens Grooming
286,301
71.8%
IM - Clothing & Accessories
286,064
71.7%
LS - Premium Electronics and Tech Enthusiasts
284,527
71.3%
IM - Beauty Products
284,243
71.2%
IM - Smartphones & Basic Mobiles
282,840
70.9%
IM - Health & Personal Care
280,429
70.3%
Men or Computers & Accessories or Mobiles
279,980
70.2%
Ethnic Wear or Ethnic Wear or Beauty
278,409
69.8%
Health or Fragrance
277,732
69.6%
Key Findings:
	•	ML persona tags are very broadly assigned — nearly every segment covers 70-76% of all streamers
	•	Each user carries 10+ overlapping persona labels — these are interest affinities, not exclusive segments
	•	Raw tags cannot be used as persona definitions — too overlapping
	•	Tags are valuable as feature inputs for clustering algorithms that find differentiating combinations of interests
Implication for Phase 2: Persona construction must use interest tags as clustering features (interest vectors), not as standalone persona definitions. The real differentiation will come from combining demographics + interest vectors + content behavior + entry behavior.

4. Emerging Persona Hypotheses
Based on demographics + interest signals, initial persona candidates:
Potential Persona
Demographic Anchor
Likely Interest Signals
Strategic Role
Young Female Drama Lover
F 18-24 (108K)
Fashion, Beauty, Ethnic Wear, Jewelry
Grow (largest segment)
Young Male Tech-Savvy Viewer
M 25-34 (83K)
Electronics, Automotive, Smartphones
Grow
Fashion-Forward Young Adult
F/M 18-34
Fashion, Clothing, Grooming
Nourish
Mature Family Viewer
F/M 35-44 (52K)
Home & Kitchen, Health, Appliances
Sustain
Health & Wellness Conscious
F 45+ (15K)
Health, Fitness, Beauty Products
Sustain
These are hypotheses only — will be validated/refined with content behavior and retention data in remaining Phase 1 queries.

5. Remaining Phase 1 Queries
#
Query
Status
Purpose
Q1
Baseline Streaming Snapshot
✅ Complete
Daily streamers, watchtime, MPC
Q2
Demographics Breakdown
✅ Complete
Age/gender distribution
Q3
Interest/Persona Segments
✅ Complete
Top interest tags
Q4
Top Shows by Streamers
⬜ Pending
Content preference mapping
Q5
Entry Behavior / Channel Distribution
⬜ Pending
Organic vs paid, discovery patterns
Q6
Retention Curve Analysis
⬜ Pending
Episode-level completion rates
Q7
Multi-Show Consumption
⬜ Pending
Session depth, content breadth

Data Sources Confirmed
Table
Schema
Purpose
Status
mxp_fatafat_player_engagement
fatafat
Streaming events, engagement
✅ Queried
mxp_fatafat_player_interaction_v2
fatafat
Player interactions, seek, buffering
⬜ Pending
mxp_age_gender_details_table_v3
public
Demographics (228M users)
✅ Queried (95% match)
mxp_persona_details_table_v3
public
Interest segments (181M ML + 54M Amazon)
✅ Queried
daily_cms_data_table
public
Content metadata, show names
⬜ Pending (Q4)
appsflyer_install_table
public
Paid attribution (installs)
⬜ Pending
appsflyer_conversions_retargeting_table
public
Paid attribution (retargeting)
⬜ Pending
mxp_fatafat_user_membership
fatafat
Membership metrics
⬜ Pending

Methodology Notes
	•	Streamer threshold: 3-second per-stream filter (CAST(playtime AS FLOAT) >= 3000) applied BEFORE GROUP BY — this is the accurate method (P0 reports use aggregate threshold which overcounts by ~3%)
	•	Base filters: All queries include networkType IS NOT NULL AND internalNetworkStatus > 1 to exclude bot/invalid traffic
	•	Demographics source: ML-predicted + Amazon + MX sources combined
	•	Persona source: ML source only (181M users) — Amazon source (54M) available for supplementary analysis
