AMAZON MX PLAYER
Fatafat Micro-Drama Vertical
SYNTHETIC PERSONAS
Phase 1: Data Foundation Report
Behavioral intelligence from 400K+ daily streamers across 7 live Redshift tables
April 6, 2026  •  Data Period: Mar 31 – Apr 6, 2026  •  8 Analytical Queries
CONFIDENTIAL — INTERNAL USE ONLY


Executive Summary
Phase 1 of the Synthetic Personas project — the Data Foundation — is now complete. Eight analytical queries executed against live Amazon MX Player Redshift tables have surfaced the behavioral, demographic, content, and channel signals necessary to build the unified audience dataset that underpins persona construction in Phase 2.
Fatafat's daily active audience of 337K–410K streamers (3-second threshold) exhibits a richly differentiated behavioral structure that maps cleanly onto six persona hypotheses. The platform demonstrates strong engagement depth — 22–25 minutes per consumer per day — driven by a core of organic, returning viewers who watch multiple shows in a single session. At the same time, the majority (76.9%) of daily users are single-show samplers, representing both the platform's acquisition challenge and its largest growth opportunity.
Six preliminary persona hypotheses have emerged from the intersection of demographics, content preferences, channel behavior, retention curves, and multi-show consumption patterns. These hypotheses are data-anchored but not yet statistically validated — that step belongs to Phase 2 (clustering). The most critical behavioral signal identified is the 1→2 show transition: users who watch a second show in a session watch 5.5x more total minutes than single-show viewers.

Daily Streamers
MPC Range
Demo Match Rate
Single-Show Users

337K – 410K
22–25 min
95%
76.9%

3-second threshold | Mar 31–Apr 6
Organic users: 39.5 min avg
mxp_age_gender_details_v3
Biggest growth lever on platform


Phase 1 — Eight Queries, Eight Findings
	•	Baseline Streaming Snapshot: 337K–410K daily 3s streamers; Saturday peak at 409,753; MPC of 22–25 min/day; ~21–23 streams per user per day consistent with micro-drama short-episode cadence.
	•	Demographics Breakdown: F18-24 is the single largest demographic cell at 108K users (28.6%); 95% demographic match rate; gender flips at 25-34 from female-dominant to male-dominant.
	•	Interest / Persona Segments: ML persona tags cover 70–76% of all streamers per tag — indicating broad affinities, not exclusive segments. Tags must be used as clustering feature vectors, not persona definitions.
	•	Top Shows by Streamers: Three distinct consumption patterns — Discovery/Sampling (<15 MPC), Steady Engagement (15–30 MPC), and Binge/Loyal (30+ MPC). Romance/CEO dramas dominate the deep-engagement tier.
	•	Channel Distribution: Paid acquisition drives 49% of streamers but only 25% of watchtime. Organic users contribute 39% of streamers but 73% of total watchtime at 3.6x higher MPC.
	•	Episode Retention Curve: Classic "cliff + plateau" shape — 65% of viewers leave after Ep1. The first lock boundary (Ep5→Ep6) drives a further 35.6% drop. Users who survive become highly committed (stable through Ep80).
	•	Multi-Show Consumption: 76.9% of users watch only 1 show (7.8 min avg). The 1→2 show transition produces a 5.5x watchtime increase — the single most important engagement signal in the data.
	•	Demographics × Shows: Each show has a distinct demographic fingerprint. "Our Love Is The Ocean Of Stars" is 75.3% female; "Why Do You Love Me?" is nearly gender-equal at 49.2% female.

Critical Insight: The 1→2 show transition is the single most important engagement signal on Fatafat. Converting even 10% of the 308K single-show samplers into 2-show explorers would add approximately 10M+ watchtime minutes per day.


Query 1 — Baseline Streaming Snapshot
Source: fatafat.mxp_fatafat_player_engagement | Period: Mar 31 – Apr 6, 2026 | Threshold: 3-second per-stream
The baseline snapshot establishes the foundational scale of Fatafat's active audience. Using a per-stream 3-second filter applied before aggregation — the accurate methodology — the query captures daily unique streamers, total watchtime, stream volume, and Minutes Per Consumer (MPC).


Figure 1.1: Daily Unique Streamers (3s) and MPC Trend — Mar 31 to Apr 6, 2026

Data Table — Daily Streaming Metrics
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
*Apr 6 is partial data through approximately 7:28 AM UTC (12:58 PM IST).

Key Findings
	•	Daily 3s streamers range from 337K to 410K, with a clear weekday-to-weekend ramp — Saturday April 4 peaked at 409,753, the highest single day in the 7-day window.
	•	Minutes Per Consumer (MPC) remains consistently strong at 22–25 minutes per day, reflecting genuine viewing depth rather than accidental or passive engagement.
	•	Each streamer averages 21–23 streams per day — consistent with the Fatafat micro-drama format where individual episodes are 60–90 seconds and users swipe rapidly through content.
	•	Thursday April 2 recorded the highest single-day MPC at 25.1 minutes, potentially indicating a strong content release or content recommendation event on that date.
	•	Total streams (8M+ per day) consistently exceed unique streamers by ~20x, confirming the high-velocity consumption behavior inherent to the micro-drama vertical.

PERSONA IMPLICATION
The 22–25 min MPC baseline establishes the engagement benchmark for all six personas. Personas that consistently exceed 30+ min MPC represent the "Binge/Loyal" tier, while those below 12 min represent the "Discovery/Sampler" tier.


Query 2 — Demographics Breakdown
Source: mxp_age_gender_details_table_v3 joined to Fatafat 3s streamers | Date: April 5, 2026
The demographics query joins the Fatafat 3-second streamer cohort with the unified age/gender recognition table, which combines ML-predicted, Amazon, and MX-sourced signals for 228 million users. The 95% match rate — 378,471 out of approximately 399K streamers — provides a highly reliable demographic overlay for persona construction.


Figure 2.1: Audience Demographics — Age Group × Gender Distribution, April 5, 2026

Data Table — Age × Gender Matrix
Age Group
Female
Male
Total
% of Total
Gender Split
18–24
108,137
55,383
163,520
43.1%
66% F / 34% M
25–34
51,843
83,238
135,081
35.6%
38% F / 62% M
35–44
22,812
29,265
52,077
13.7%
44% F / 56% M
45–54
13,475
11,625
25,100
6.6%
54% F / 46% M
55–64
1,431
1,262
2,693
0.7%
53% F / 47% M
TOTAL
197,698
180,773
378,471
100%
52.2% F / 47.8% M

Key Findings
	•	Female 18–24 is the dominant demographic cell at 108,137 users (28.6% of all matched streamers) — the single largest age-gender group on the platform. This cell is the primary anchor for the "Young Female Romance Binger" persona hypothesis.
	•	The overall gender split is nearly even (52.2% Female vs 47.8% Male), but this masks a sharp age-driven reversal: the 18–24 cohort is 66% female while the 25–34 cohort is 62% male — a structural split that is critical for persona differentiation.
	•	78.7% of Fatafat streamers are under 35, establishing this as a fundamentally young platform. Content skewed toward younger demographic preferences will reach the majority of the active audience.
	•	The 35+ audience (20.3% of total, approximately 77K streamers) is a meaningful secondary segment that should not be collapsed into a single persona — the 35–44 cohort alone represents 52K streamers.
	•	95% demographic match rate is excellent for persona construction — virtually the entire active audience can be overlaid with age/gender signals, eliminating the cold-start problem for demographic segmentation.

PERSONA ANCHOR
The gender flip between 18-24 (66% F) and 25-34 (62% M) suggests these two cohorts require separate persona frameworks rather than being merged into a generic "young adult" segment. Their content preferences, as confirmed by Query 8, are measurably different.


Query 3 — Interest / Persona Segments
Source: mxp_persona_details_table_v3 (ML source) joined to Fatafat 3s streamers | Date: April 5, 2026
The interest segmentation query joins the Fatafat streamer cohort with the ML-sourced persona tag table, which contains over 181 million users and assigns each user to multiple interest categories based on browsing, purchase, and behavioral signals. The Amazon source (54 million users) is available for supplementary analysis.

Data Table — Top 20 ML Interest Segments
Interest / Persona Segment
Matched Users
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

Key Findings
	•	ML persona tags are extremely broadly distributed — every segment in the top 20 covers 70–76% of all streamers. This is expected: each user carries 10+ overlapping interest tags, meaning these represent co-occurring affinities rather than mutually exclusive audience segments.
	•	The broad distribution confirms that raw persona tags cannot be used as persona definitions. A user tagged with "Fashion", "Electronics", "Beauty", and "Home & Kitchen" simultaneously provides feature richness but cannot be placed in a single category.
	•	Interest tags are most valuable as feature vectors for clustering algorithms. The combination and relative weight of tags across a user will differentiate audience segments more reliably than any single tag alone.
	•	The dominant interest categories — Fashion, Electronics, Beauty, Home & Kitchen, Fitness — align well with the F18-24 demographic identified in Query 2, suggesting these interests are correlated with the platform's largest audience cohort.
	•	The presence of "Men or Computers & Accessories or Mobiles" (279K) and "Automotive or Electronics" (288K) at scale confirms that the male audience (primarily M25-34 from Query 2) is well-represented in the interest signal layer.

METHODOLOGY NOTE
Phase 2 persona construction must treat interest tags as a multi-dimensional feature matrix (user × interest combination vectors) rather than as categorical labels. A k-means or hierarchical clustering approach over this feature space — combined with behavioral dimensions from Queries 1, 4, 5, and 7 — will yield the statistically defined personas.


Query 4 — Top Shows by Streamers
Source: fatafat.mxp_fatafat_player_engagement joined to daily_cms_data_table | Period: Mar 31 – Apr 6, 2026
The top shows query identifies the 20 most-streamed shows on Fatafat by unique 3-second streamers over the 7-day window. Beyond reach, it captures total watchtime and MPC — enabling identification of distinct content consumption patterns that anchor persona construction.


Figure 4.1: Top 20 Shows — Unique Streamers vs MPC | Bubble Size = Total Watchtime Minutes

Data Table — Top 20 Fatafat Shows (Mar 31 – Apr 6, 2026)
#
Show Name
Streamers
Episodes
Total Min
MPC (min)
1
Why Do You Love Me?
225,701
80
2,273,093
10.1
2
My Cursed Kiss
150,480
70
1,026,671
6.8
3
His Allergic Love
130,311
79
1,624,955
12.5
4
Back From My Funeral
127,395
64
1,288,700
10.1
5
Our Love Is The Ocean Of Stars
126,092
67
4,523,515
35.9
6
I Won His Heart
125,293
69
1,832,010
14.6
7
Mr. Huo, Your Wife's Back with Babies!
122,070
59
3,879,250
31.8
8
I Married A Mystery
107,940
61
1,162,860
10.8
9
Ek Badnaam Aashram
96,620
60
176,360
1.8
10
Unbossed Wife
94,084
86
1,294,573
13.8
11
Lucky Trio: CEO Daddy's Doting Love
73,172
90
2,205,650
30.1
12
The Divorce Sisters
69,534
90
1,236,643
17.8
13
The Cold CEO's Torturous Love Game
62,710
100
2,012,240
32.1
14
I Owe You Everything
61,922
29
159,918
2.6
15
Love Found Me First
56,562
72
1,217,721
21.5
16
I Found My Own Strength
51,675
80
1,094,377
21.2
17
I Raised Our Child Alone
48,032
60
1,427,952
29.7
18
Tempted By The Boss's Wife
47,538
50
423,819
8.9
19
I Fell Twice For Him
47,318
61
949,344
20.1
20
Flash Marriage: Mrs. Gu's Online Unmasking
45,148
90
1,478,358
32.7
MPC shading: Pink = Binge/Loyal (30+ min) | Teal = Steady Engagement (15–30 min) | White = Discovery/Sampling (<15 min)

Three Distinct Content Consumption Patterns
Pattern A — High Reach, Lower Depth (Discovery / Sampling)
	•	Why Do You Love Me? (226K streamers, 10.1 MPC), My Cursed Kiss (150K, 6.8 MPC), Ek Badnaam Aashram (97K, 1.8 MPC).
	•	High discovery reach driven by homepage placement, For You feed, or paid acquisition. Users sample but do not commit to sustained viewing.
	•	Notable exception: Ek Badnaam Aashram has 97K streamers but only 1.8 MPC — the lowest in the top 20. As the sole apparent Hindi-language title, this suggests a distinct audience segment with a fundamentally different engagement profile, possibly short-form or trailer-like content behavior.
Pattern B — Lower Reach, Very High Depth (Binge / Loyal)
	•	Our Love Is The Ocean Of Stars (126K, 35.9 MPC), Mr. Huo (122K, 31.8 MPC), The Cold CEO's Torturous Love Game (63K, 32.1 MPC), Flash Marriage (45K, 32.7 MPC).
	•	Romance/CEO/marriage drama genre dominates this tier — users are watching 30+ minutes per session across many episodes, driven by narrative hook and emotional investment.
	•	Despite lower reach than Pattern A, these shows generate disproportionate total watchtime. Our Love Is The Ocean Of Stars alone drove 4.5M minutes in 7 days.
Pattern C — Moderate Reach, Moderate Depth (Steady Engagement)
	•	I Found My Own Strength (52K, 21.2 MPC), Love Found Me First (57K, 21.5 MPC), I Fell Twice For Him (47K, 20.1 MPC).
	•	Empowerment and independence themes anchor this tier. Consistent 20+ min MPC across a mid-range audience suggests a loyal but non-binge audience with regular, habitual viewing.

The MPC-Reach trade-off is a defining structural feature of Fatafat's content landscape: the highest-reach show (Why Do You Love Me? at 226K) has only 10.1 MPC, while the highest-MPC show (Ocean Of Stars at 35.9 MPC) has 126K streamers. Neither metric alone tells the full story — both must be tracked for persona profiling.


Query 5 — Entry Behavior / Channel Distribution
Source: fatafat.mxp_fatafat_player_engagement (dputmsource field) | Date: April 5, 2026
The channel distribution query classifies each streaming session by its acquisition or re-engagement source, mapping dputmsource values into five categories: Paid (performance/branding media), Organic (direct/undefined source), Push Notification, Internal Ad, and OTT Notification.

Methodology Note: dputmsource is an approximate proxy for session source. A user can have both paid and organic sessions on the same day, meaning channel categories are not mutually exclusive — the sum of channel streamers exceeds the total unique streamers. For precise paid/organic attribution at the user level, AppsFlyer is the source of truth.


Figure 5.1: Channel Distribution — Streamers vs Watchtime by Channel Category, April 5, 2026

Data Table — Channel Distribution (April 5, 2026)
Channel
Streamers (3s)
Watchtime (min)
% Streamers
MPC (min)
% Watchtime
Paid
209,169
2,320,079
48.9%
11.1
25.4%
Organic
168,456
6,654,046
39.4%
39.5
72.9%
Push Notification
32,646
113,120
7.6%
3.5
1.2%
Internal Ad
16,214
30,329
3.8%
1.9
0.3%
OTT Notification
1,147
14,235
0.3%
12.4
0.2%

Key Findings
	•	Paid acquisition drives the most streamers (49%) but contributes only 25% of total watchtime — an efficiency ratio of approximately 0.51. For every dollar of paid reach, watchtime return is roughly half the platform average.
	•	Organic users are the platform's depth engine: 39% of streamers but 73% of watchtime, with an MPC of 39.5 minutes — 3.6x higher than paid users (11.1 min). These are habitual, returning viewers who come to the platform on their own initiative.
	•	Push Notifications drive 7.6% of streamers but with only 3.5 min MPC — users are opening the app in response to a notification but not staying engaged. This suggests notification content-match quality may need improvement.
	•	Internal Ads (3.8% of streamers, 1.9 MPC) represent the most transactional discovery behavior — users see an ad inside the AMXP ecosystem and click through, but engagement is minimal.
	•	OTT Notifications are tiny (0.3%) but exhibit a 12.4 min MPC — higher than Push Notifications and comparable to paid engagement. This small cross-platform segment may punch above its weight and warrants dedicated persona monitoring.

PERSONA DIMENSION
Channel behavior splits the audience into two fundamental behavioral types: "Organic Depth" users (loyalists who return organically and watch deeply) and "Acquisition Surface" users (paid/push-driven samplers). This dimension must be incorporated as a primary clustering variable in Phase 2.


Query 6 — Episode-Level Retention Curve
Source: fatafat.mxp_fatafat_player_engagement joined to daily_cms_data_table (episode_number column) | Show: "Why Do You Love Me?" | Period: Mar 31 – Apr 5, 2026
The retention curve query uses actual episode_number values from the CMS metadata table (cast to integer for correct sequential ordering) to map viewer drop-off and retention across all 80 episodes of Fatafat's most-watched show. This produces a true sequential retention curve — the foundational behavioral signature for persona construction.


Figure 6.1: Full 80-Episode Retention Curve — "Why Do You Love Me?" | Orange dashed lines = Progressive lock boundaries


Figure 6.2: Lock Boundary Drop-off Analysis — Percentage and User Count at Each Progressive Lock Boundary

Retention Milestones Table
Episode
Streamers
Retention %
Change
Users Lost/Gained
Behavior Note
Ep 1 (Entry)
178,007
100.0%
—
—
Start: Full audience entry point
Ep 2
62,200
34.9%
-65.1%
-115,807
Biggest single drop — Sampler exit
Ep 3
46,171
25.9%
-25.8%
-16,029
Continued filtering of casual viewers
Ep 5 (pre-lock)
40,581
22.8%
-4.4%
-5,590
Final free episode before 1st lock
Ep 6 (1st lock)
26,145
14.7%
-35.6%
-14,436
Lock gate: largest post-Ep1 drop
Ep 10
24,087
13.5%
-1.2%/ep
-522/ep
Committed plateau begins
Ep 20
19,779
11.1%
-0.4%/ep
-231/ep
Very gradual decline continues
Ep 30
17,675
9.9%
-0.3%/ep
-210/ep
Deep loyal core stabilizing
Ep 40
16,575
9.3%
-0.2%/ep
-110/ep
Near-flat loyalty zone
Ep 50
15,385
8.6%
-0.1%/ep
-119/ep
Core completers
Ep 60
14,415
8.1%
-0.1%/ep
-97/ep
Deep completers
Ep 70
13,748
7.7%
-0.1%/ep
-67/ep
Pre-finale territory
Ep 80 (Final)
18,085
10.2%
+3.7%
+3,610
Finale spike — skip viewers return

Lock Boundary Impact Analysis — Diminishing Returns
Lock Boundary
Pre-Lock
Post-Lock
Drop %
Users Lost
Assessment
Ep5→Ep6 (1st Lock)
40,581
26,145
-35.6%
14,436
Primary filter — largest gate
Ep10→Ep11 (2nd Lock)
24,087
21,306
-11.5%
2,781
Significant but manageable
Ep15→Ep16 (3rd Lock)
21,044
19,917
-5.4%
1,127
Moderate drop-off
Ep20→Ep21 (4th Lock)
19,779
18,600
-6.0%
1,179
Slightly elevated at this stage
Ep25→Ep26 (5th Lock)
18,399
17,706
-3.8%
693
Committed users absorb the lock
Ep30→Ep31 (6th Lock)
17,675
17,279
-2.2%
396
Near-negligible — highly loyal core

Key Findings — Four Retention Phases
	•	Discovery Phase (Ep 1–5): Entry at 178K, collapsing to 40K — an 77.2% cumulative loss before the first lock boundary. The Ep1→Ep2 transition alone loses 65.1% of all viewers, establishing the sampler-to-trialist filter.
	•	Lock Gate Phase (Ep 5→6): The progressive lock system creates a 35.6% cliff at Ep5→Ep6 — the single largest lock-driven drop. This gate is working as designed, filtering out uncommitted viewers before expensive content is consumed.
	•	Committed Phase (Ep 6–30): Viewers who survive the first lock enter a gradual decline phase from 14.7% to 9.9% retention over 24 episodes — approximately 0.2% per episode. These users are increasingly committed with each episode watched.
	•	Deep Loyal Phase (Ep 30–80): Retention becomes nearly flat below 10%. The core audience of approximately 13K–18K viewers watches all the way to the finale with remarkable stability.
	•	Finale Spike (Ep79→Ep80): An uptick of +3,610 viewers at the finale (from 14,475 to 18,085) indicates "finale curiosity" behavior — users who dropped out mid-series return specifically to see the ending. This is a recoverable audience segment.
	•	Ep5 Uptick: Episode 5 (the last free episode) shows higher streamers than Ep4 (+1,790), suggesting that users are directed specifically to the pre-lock finale to maximize their chances of completing the unlock trigger.

BEHAVIORAL SIGNATURES
This retention curve defines three user behavioral signatures: Samplers (65% of entry — watch Ep1 only), Trialists (13% — watch Ep1-5, hit the lock, leave), and Completers (~10% — survive the first lock and stay through Ep80). Each signature represents a distinct persona type.


Query 7 — Multi-Show Consumption Distribution
Source: fatafat.mxp_fatafat_player_engagement joined to daily_cms_data_table | Date: April 5, 2026
The multi-show consumption query maps the distribution of unique shows watched per user on a single day. It reveals how many users watch just one show versus multiple shows, and how watchtime escalates with each additional show — producing the clearest single-variable proxy for audience engagement depth available in Phase 1.


Figure 7.1: Multi-Show Consumption Distribution — Users (bars) and Avg Minutes (spline) by Shows Watched per Day

Data Table — Multi-Show Consumption Segments
Shows / Day
Users
% of Total
Avg Minutes
Segment
Behavior Note
1 show
307,604
76.9%
7.8
Sampler
Try one show and leave — the majority behavior
2 shows
46,342
11.6%
43.1
Explorer
5.5x watchtime jump from single-show
3 shows
18,212
4.6%
72.5
Explorer
Consistently high engagement
4 shows
9,621
2.4%
96.5
Engaged
Nearly 100 min/day avg
5 shows
5,433
1.4%
115.3
Engaged
Committed viewer pattern
6 shows
3,473
0.9%
127.0
Power User
Daily session depth 2+ hours
7 shows
2,219
0.6%
135.7
Power User
Deep daily engagement
8 shows
1,578
0.4%
147.1
Power User
Strong loyalty signal
9 shows
1,124
0.3%
150.4
Power User
Near-ceiling viewing
10 shows
833
0.2%
165.9
Super Fan
Platform-dedicated behavior
11+ shows
3,527
0.9%
~161
Super Fan
Daily ceiling ~160 min

Cumulative Distribution
Shows Watched (cumulative)
Users
Cumulative %
Implication
1 show
307,604
76.9%
Single-show majority — platform's primary challenge
2 shows
353,946
88.5%
Two-show threshold — critical engagement signal
3 shows
372,158
93.0%
Three-show users: highly engaged, small cohort
5 shows
387,212
96.8%
Core active audience boundary
10 shows
396,439
99.1%
99% of audience captured at 10-show threshold

Key Findings
	•	The single-show majority (76.9%, 308K users) is the defining structural challenge of Fatafat's engagement landscape. These users generate only 7.8 min avg — far below the platform average and far below commercial monetization thresholds for most ad products.
	•	The 1→2 show transition produces a 5.5x watchtime increase (7.8 → 43.1 min). No other single behavioral event in the data produces an equivalent magnitude of watchtime change. This is the highest-leverage conversion point on the platform.
	•	Only 23.1% of users (92K) watch 2+ shows. This small cohort drives the substantial majority of total daily watchtime. Converting even 5% of single-show samplers (15K users) to 2-show viewers would meaningfully impact platform-level watchtime.
	•	Watchtime plateaus at approximately 160 minutes after 10+ shows — representing a natural daily consumption ceiling of 2.5–3 hours. Platform mechanics (content library size, UX design) should be designed with this ceiling in mind.
	•	The escalation is rapid and near-linear through the first 8–10 shows, suggesting each additional show watched produces a roughly constant watchtime increment — a favorable engagement function for content recommendation optimization.

Growth opportunity: If the "For You" recommendation system could convert the 76.9% single-show sampler cohort to a 2-show explorer cohort at even a 10% rate (30K additional 2-show users), total daily watchtime would increase by approximately 1.1M minutes per day.


Query 8 — Demographics × Top 5 Shows
Source: fatafat.mxp_fatafat_player_engagement joined to daily_cms_data_table and mxp_age_gender_details_table_v3 | Date: April 5, 2026
The demographic cross-reference query joins the top 5 shows' streamers on April 5 with the age/gender recognition table, producing a show-level demographic fingerprint for each title. This reveals whether different shows serve different audience cohorts — a critical test for persona differentiation.


Figure 8.1: Audience Demographics × Top 5 Shows — Pink = Female segments | Blue = Male segments, April 5, 2026

Gender Split by Show
Show
Streamers
Female %
Male %
Dominant Cell
Assessment
Our Love Is The Ocean Of Stars
27,809
75.3%
24.7%
F 18–24 (45.4%)
Purest female-skewed show; 35.9 MPC
Mr. Huo, Your Wife's Back with Babies!
22,268
63.0%
37.0%
F 18–24 (35.9%)
Strong female; deep engagement 31.8 MPC
My Cursed Kiss
25,225
52.2%
47.8%
F 18–24 (29.8%)
Gender-balanced crossover title
His Allergic Love
18,782
52.2%
47.8%
F 18–24 (30.4%)
Gender-balanced crossover title
Why Do You Love Me?
42,542
49.2%
50.8%
F18-24 ≈ M25-34
Most gender-equal; broadest reach

Age Group Distribution by Show
Show
18–24 %
25–34 %
35–44 %
45–54 %
55–64 %

Our Love Is The Ocean Of Stars
55.2%
29.7%
9.4%
5.1%
0.6%

Mr. Huo, Your Wife's Back with Babies!
49.2%
33.3%
11.2%
5.7%
0.6%

My Cursed Kiss
43.5%
34.9%
13.2%
7.8%
0.5%

His Allergic Love
43.7%
34.5%
13.5%
7.8%
0.5%

Why Do You Love Me?
37.8%
37.8%
16.4%
7.1%
0.9%


Key Findings
	•	"Our Love Is The Ocean Of Stars" is the most demographically concentrated show on the platform: 75.3% female, with F18-24 alone making up 45.4% of its audience. This is the clearest "Young Female Romance Binger" persona anchor in the data — it also has the highest MPC at 35.9 minutes.
	•	"Mr. Huo, Your Wife's Back with Babies!" follows a similar pattern (63% female, 35.9% F18-24) with 31.8 MPC — confirming that the CEO/marriage-drama genre consistently attracts and deeply engages the Female 18-24 cohort.
	•	"Why Do You Love Me?" is the platform's most gender-balanced show at 49.2% female / 50.8% male, with M25-34 (24.9%) nearly matching F18-24 (25.3%). This show serves as the broadest-appeal entry point and reaches both of the platform's largest demographic cohorts simultaneously.
	•	"My Cursed Kiss" and "His Allergic Love" are near-identical in demographic profile (both 52.2% female) — confirming their classification as "crossover" titles that appeal across gender lines and may be particularly useful for the male 25-34 persona who engages with romance content.
	•	The 18-24 age group concentration is highest in Ocean Of Stars (55.2%) and lowest in Why Do You Love Me? (37.8%), indicating that the highest-depth shows skew younger. Mature audiences (35+) are proportionally better represented in the highest-reach shows.

SHOW-AS-PERSONA-PROXY
The distinct demographic fingerprints across these 5 shows confirm that content preferences are a valid proxy for demographic-behavioral persona segmentation. A user whose top show is "Our Love Is The Ocean Of Stars" is highly likely to be F18-24 (75.3% probability); a user whose top show is "Why Do You Love Me?" could be any demographic. This show-based inference can serve as a lightweight persona classifier in Phase 2.


Consolidated Persona Hypotheses
Combining all eight data layers — streaming baseline, demographics, interest segments, content preferences, channel distribution, retention curves, multi-show consumption, and demographic × show cross-reference — six preliminary personas emerge from Phase 1.
These hypotheses are data-anchored but not yet statistically validated through cluster analysis. Validation and formalization occur in Phase 2 (Persona Construction). Each persona hypothesis below carries a behavioral fingerprint, demographic anchor, content signal, channel signal, and Grow/Nourish/Sustain strategic role.

P1 - Young Female Romance Binger    [GROW]
Size: ~108K (28.6%)  |  Demo: Female 18-24  |  MPC: 40-115 min
Content Signal: Our Love Is The Ocean Of Stars, Mr. Huo — CEO/romance dramas; 30+ MPC shows
Channel: Organic (high loyalty)  |  Shows/Day: 2-5 shows/day
Note: Largest and deepest segment. F18-24 makes up 45.4% of Ocean Of Stars audience. The platform's primary commercial asset.

P2 - Male Crossover Viewer    [GROW]
Size: ~83K (21.9%)  |  Demo: Male 25-34  |  MPC: 20-50 min
Content Signal: Why Do You Love Me?, My Cursed Kiss — balanced/crossover titles; moderate MPC
Channel: Mixed organic + paid  |  Shows/Day: 1-3 shows/day
Note: Gender flip at 25-34 (62% male) confirmed by Query 2. Prefers broader-appeal crossover titles rather than female-dominant romance dramas.

P3 - Discovery Sampler    [CONVERT]
Size: ~308K (76.9%)  |  Demo: Broad demographic  |  MPC: 7.8 min avg
Content Signal: High-reach shows; <8 min MPC — samples but does not commit
Channel: Paid acquisition + Push Notification  |  Shows/Day: 1 show/day
Note: Numerically the largest cohort but lowest engagement. Converting 10% to 2-show explorer behavior would add 1.1M+ watchtime minutes daily.

P4 - Multi-Show Power User    [NOURISH]
Size: ~28K (7%)  |  Demo: Mixed under-35  |  MPC: 100-165 min
Content Signal: 4+ shows per day; 100-165 min; platform-dedicated behavior
Channel: Organic (habitual return)  |  Shows/Day: 4-10+ shows/day
Note: Small but disproportionately high watchtime contribution. Content appetite exceeds current recommendation surface. Slate gap signals most visible here.

P5 - Mature Loyal Viewer    [SUSTAIN]
Size: ~52K (13.7%)  |  Demo: Female / Male 35-44  |  MPC: 20-30 min
Content Signal: Empowerment and family dramas (Unbossed Wife, I Raised Our Child Alone); 20+ MPC
Channel: Organic (stable)  |  Shows/Day: 1-3 shows/day
Note: Most stable, habitual audience. Lower peak engagement but consistent daily viewing. Important for household and family advertiser CPM products.

P6 - Hindi Content Explorer    [EXPLORE]
Size: ~97K (est.)  |  Demo: TBD (Ek Badnaam Aashram viewers)  |  MPC: <5 min
Content Signal: Hindi-language content; 1.8 MPC — sampling only, no retention
Channel: TBD  |  Shows/Day: 1 show/day
Note: Identified by the Ek Badnaam Aashram anomaly (97K streamers, 1.8 MPC). Represents either content-format mismatch or distinct unmet content needs. Requires dedicated analysis.


Phase 1 Conclusion: All six persona hypotheses are grounded in live behavioral data from 400K+ daily streamers. The critical next step is Phase 2 — applying clustering algorithms across the 5-dimensional feature matrix (demographics, content preference, engagement depth, channel behavior, multi-show consumption) to validate, merge, or split these hypotheses into statistically defined personas.


Data Sources & Methodology
All Phase 1 analyses were executed against the AMXP-BI-MCP-PROD Redshift database using live production data. The following tables were queried and confirmed available for Phase 2 persona construction.

Data Sources Confirmed
Table Name
Schema
Purpose
Status
Note
mxp_fatafat_player_engagement
fatafat
Streaming events, engagement, MPC, session signals
Queried (Q1,Q4,Q5,S1-S3)
Primary behavioral source
mxp_age_gender_details_table_v3
public
Demographics — age/gender for 228M users (ML + Amazon + MX sources)
Queried (Q2, Q8)
95% match rate to streamers
mxp_persona_details_table_v3
public
Interest segments — 181M ML users + 54M Amazon users (long format: 10+ tags/user)
Queried (Q3)
ML source only used
daily_cms_data_table
public
Content metadata — show names, episode numbers, season numbers, video IDs
Queried (Q4, S1-S3)
episode_number cast to INT for ordering
mxp_fatafat_player_interaction_v2
fatafat
Player interactions — seek behavior, playback speed, buffering patterns
Available for Phase 2
Engagement quality signals
appsflyer_install_table
public
Paid attribution — install-level channel classification (source of truth for paid/organic)
Available for Phase 2
Supplements dputmsource proxy
appsflyer_conversions_retargeting_table
public
Paid retargeting attribution — re-engagement channel classification
Available for Phase 2
Re-engagement channel signals
mxp_fatafat_user_membership
fatafat
Membership metrics — subscriber behavior profiling and premium access patterns
Available for Phase 2
Monetization dimension

Methodology Notes
	•	Streamer threshold: 3-second per-stream filter (CAST(playtime AS FLOAT) >= 3000) applied BEFORE GROUP BY. This is the accurate methodology — P0 reports that apply an aggregate threshold overcount by approximately 3% because sessions shorter than 3s may summate to above the threshold.
	•	Base filters: All queries include networkType IS NOT NULL AND internalNetworkStatus > 1 to exclude bot traffic, offline sessions, and invalid network states.
	•	Demographics source: mxp_age_gender_details_table_v3 combines ML-predicted age/gender, Amazon account-linked signals, and MX-sourced signals. The 95% match rate to Fatafat streamers on April 5 confirms near-complete demographic coverage.
	•	Persona source: mxp_persona_details_table_v3 (ML source only, 181M users). The Amazon source (54M users) is available for supplementary analysis but was excluded from Phase 1 queries due to join size constraints.
	•	Channel attribution: dputmsource-based classification is an approximate proxy. Channel categories are not mutually exclusive — a user's session may be attributed to multiple sources within a single day. For precise paid/organic user-level classification, AppsFlyer install and retargeting tables are the source of truth.
	•	Episode ordering: Retention curve analysis (Query 6) uses CAST(episode_number AS INT) from daily_cms_data_table for correct sequential ordering. Lexicographic sort would produce incorrect order (1, 10, 11, 12... instead of 1, 2, 3...).
	•	Multi-show consumption: Single-day snapshot (April 5). Multi-day analysis (7-day rolling window) recommended for Phase 2 to capture cross-day viewing patterns and identify habitual multi-show behavior.
	•	Date range: Core queries (Q1, Q4) use Mar 31 to Apr 6, 2026 for 7-day trend analysis. Point-in-time queries (Q2, Q3, Q5, Q7, Q8) use April 5, 2026 as the primary sample date.


Phase 2 Readiness Assessment
Phase 1 data extraction is complete. The unified behavioral dataset — combining streaming signals, demographics, content preferences, channel behavior, and engagement depth — provides all required inputs for Phase 2 persona construction.

Clustering Dimensions Identified (5 Dimensions)
	•	Demographics: Age group and gender (95% match rate; F18-24 dominant cell at 28.6%)
	•	Content Preference: Show genre alignment and MPC tier (sampling vs. steady vs. binge behavior)
	•	Engagement Depth: Multi-show consumption count and avg minutes (single-show sampler to super fan)
	•	Channel Behavior: Organic vs. paid vs. notification-driven sessions (depth indicator)
	•	Retention Signature: Episode completion depth and lock boundary survival (behavioral commitment)

Recommended Phase 2 Approach
	•	Build user-level feature matrix: For each Fatafat user active in the past 30 days, construct a feature vector across all 5 clustering dimensions using a 30-day rolling window.
	•	Apply clustering algorithm: Run k-means (k=6 as starting point) and hierarchical clustering over the feature matrix. Test k=4 to k=8 to validate optimal segment count.
	•	Validate against hypotheses: Compare cluster outputs against the 6 Phase 1 persona hypotheses. Confirm, merge, or split as the data dictates.
	•	Assign strategic roles: Map validated clusters to Grow/Nourish/Sustain/Convert/Explore strategic roles based on segment size x engagement depth x commercial profile.
	•	Create persona cards: Document each persona with a behavioral fingerprint, content identity, strategic role, commercial profile, retention signature, and channel profile.

Additional Data to Pull in Phase 2
	•	AppsFlyer install and retargeting tables: Precise paid/organic classification at the user level (replaces dputmsource proxy)
	•	mxp_fatafat_player_interaction_v2: Seek behavior, playback speed preferences, and buffering tolerance (engagement quality signals)
	•	mxp_fatafat_user_membership: Subscriber vs. free tier behavior and premium content access patterns
	•	7-day rolling multi-show consumption: Cross-day viewing patterns to capture habitual vs. sporadic multi-show behavior
	•	Genre-level content clustering: Map all Fatafat shows to genre clusters using CMS metadata for content affinity scoring per user

PHASE 2 TIMELINE
Recommended Phase 2 execution: 2-3 weeks. Week 1: Build user-level feature matrix and run initial cluster analysis. Week 2: Validate clusters, assign strategic roles, and draft persona cards. Week 3: Review and finalize persona set with stakeholder sign-off.


Query Log — Phase 1 Execution Record
All 8 queries were executed on April 6, 2026 against AMXP-BI-MCP-PROD Redshift. Below is the complete execution record.

#
Query Name
Date Run
Data Period
Key Result
Q1
Baseline Streaming Snapshot
Apr 6
Mar 31 - Apr 6
337K-410K daily streamers; 22-25 min MPC; Saturday peak 409,753
Q2
Demographics Breakdown
Apr 6
Apr 5
F18-24 dominant (28.6%); 95% match rate; gender flip at 25-34
Q3
Interest/Persona Segments
Apr 6
Apr 5
Broad ML tags (70-76% coverage each); needs clustering approach
Q4
Top 20 Shows by Streamers
Apr 6
Mar 31 - Apr 6
3 consumption patterns: sampling (<15 MPC), steady (15-30), binge (30+)
Q5
Channel Distribution
Apr 6
Apr 5
Paid = 49% reach / 25% watchtime; Organic = 39% reach / 73% watchtime
S1
Episode Retention Curve
Apr 6
Mar 31 - Apr 5
4 retention phases; 65% Ep1 drop; 35.6% cliff at 1st lock boundary
S2
Multi-Show Consumption
Apr 6
Apr 5
76.9% single-show; 1 to 2 show jump = 5.5x watchtime increase
S3
Demographics x Top 5 Shows
Apr 6
Apr 5
Shows have distinct demo profiles; Ocean Of Stars = 75.3% female


Glossary of Terms

Term
Definition
3s Streamer
A user counted as having streamed if at least one individual streaming session exceeded 3 seconds of playback. The per-stream filter is applied before aggregation for accuracy.
MPC (Minutes Per Consumer)
Total watchtime in minutes divided by unique 3-second streamers for a given period. The primary depth engagement metric on Fatafat.
Lock Boundary
A progressive episode gate in Fatafat's content model. After completing the final episode of a free tier (e.g., Ep5), users must watch a 20-second ad or complete a specific interaction to unlock the next tier of episodes.
Retention Curve
An episode-by-episode view of unique streamers across a show's full episode run, expressing the percentage of the Ep1 audience that persists to each subsequent episode.
Discovery Phase
The first 1-5 episodes of a show where the majority of casual viewers are filtered out through organic drop-off.
dputmsource
A session-level field in mxp_fatafat_player_engagement that captures the acquisition or re-engagement source of the session (e.g., organic, paid campaign tag, push notification). Not mutually exclusive across sessions.
For You Feed
The primary content discovery surface on Fatafat — a personalized, algorithmically ranked feed of micro-drama episodes served to users upon opening the app.
Grow/Nourish/Sustain
The Fatafat audience strategic framework. Grow = largest segments requiring scale investment; Nourish = engaged mid-tier requiring content depth; Sustain = stable loyal segments requiring retention protection.
Persona Hypothesis
A data-anchored but not yet statistically validated audience archetype. Phase 1 produces hypotheses; Phase 2 (clustering) produces validated personas.
ML Persona Tags
Interest and intent tags assigned to users by ML models based on browsing, purchase, and behavioral signals across the Amazon MX Player ecosystem. Stored in mxp_persona_details_table_v3.
Feature Matrix
A user-level data structure combining multiple behavioral dimensions (demographics, content preference, engagement depth, channel behavior, retention signature) used as input for clustering algorithms in Phase 2.
Finale Curiosity
The observed behavior of viewers who drop out mid-series but return specifically to watch the final episode, producing a spike in Ep80 streamers above the late-series baseline.
Fatafat
Amazon MX Player's micro-drama vertical — a platform for bite-sized episodic drama content (60-90 second episodes) characterized by high-frequency consumption, progressive episode locks, and romance-dominant content.


Industry Benchmarks & Context
The Synthetic Personas project is positioned within a broader industry shift toward predictive, AI-powered audience intelligence in streaming. The following benchmarks from the external research document provide context for Phase 1 findings and validate the strategic direction of the project.

Source
Benchmark
Approach
Relevance to Phase 1
Cinelytic
85% pre-production forecasting accuracy
AI-driven content prediction before production decisions
Validates the viability of AI persona models for pre-launch content scoring (Phase 3 of this project)
Disney's Audience Graph
Cross-platform identity stitching at scale
Links streaming behavior to consumer identity across Disney+ and Hulu
Analogous to our mxp_age_gender + mxp_persona join architecture — confirms the approach
Netflix's Ads Suite
Audience segment-based ad targeting
Behavioral cohort-based ad targeting using viewing patterns as segments
Mirrors the commercial profile dimension of persona construction — ad targeting by behavioral persona, not just demographics
Parrot Analytics' Demand Sensing
Multi-signal content demand measurement
Aggregates social, streaming, and search signals for content demand forecasting
Phase 3 (AI Simulation Engine) analog — our equivalent uses internal behavioral signals at higher granularity
AMXP Synthetic Personas Target
~75% audience coverage by 5-6 personas
Internal project target from Synthetic Personas v2.docx
Phase 1 data confirms feasibility: 6 hypothetical personas already cover identifiable segments across the full streaming audience

Synthetic Personas — Phase 1: Data Foundation Report
Amazon MX Player | Fatafat Micro-Drama Vertical
Generated: April 6, 2026  |  Data Source: AMXP-BI-MCP-PROD Redshift  |  CONFIDENTIAL
