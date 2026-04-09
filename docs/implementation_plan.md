Synthetic Personas
Audience Simulation Engine
Phased Implementation Plan
Amazon MX Player Fatafat  •  Internal Strategy Document

Project
Classification
Status
Version
Synthetic Personas / Audience Simulation Engine
Internal — Stakeholder Review
Active — Phase 1
v1.0

1. Executive Summary
Fatafat's growth at Amazon MX Player requires a fundamental shift from reactive content decisions to predictive audience intelligence. Today, content risks — poor onboarding, narrative pacing issues, low retention among key cohorts — are identified only after a show launches, when remediation is expensive or impossible. Audience understanding remains fragmented, with streaming behavioral data and consumer identity profiles living in disconnected systems. There is no live mechanism to detect slate gaps or identify underserved audience segments before they become competitive vulnerabilities.
The Audience Simulation Engine addresses these structural gaps by merging real-time Fatafat streaming behavioral data with the demographic and interest-based persona profiles already available in the Amazon MX Player Redshift data warehouse. The result is a set of synthesized audience personas — data-driven "pseudo-viewers" — that can be used to evaluate content pre-launch, align commissioning decisions to audience demand, and identify commercial value at the cohort level.
Problem Statement
	•	Late-stage risk identification: Content onboarding failure, pacing issues, and retention drop-off are caught post-launch when correction is costly
	•	Fragmented audience understanding: Streaming behavioral data and consumer identity/interest profiles exist in silos with no unified audience view
	•	Reactive slate gap detection: No live mechanism to surface underserved audience cohorts or identify content demand signals ahead of commissioning
Solution Overview
A three-layer architecture that progresses from raw data unification to synthesized personas to AI-powered simulation:
	•	Layer 1 — Unified Audience Dataset: Link Fatafat streaming behavioral signals with demographic profiles and interest-based persona segments
	•	Layer 2 — Synthesized Persona Set: Construct 5–6 content-first personas covering ~75% of active Fatafat audience, each carrying a behavioral fingerprint, strategic role, and commercial profile
	•	Layer 3 — AI Simulation Engine: Train pseudo-viewer models per persona to evaluate incoming content concepts for engagement prediction, narrative density alignment, and audience-fit scoring
Expected Outcomes
Outcome
Description
Pre-launch content scoring
Directional engagement predictions for new shows before production lock-in, reducing late-stage risk
Audience-aligned commissioning
Persona-mapped slate gaps surfaced in real time to inform commissioning decisions against live demand signals
Commercial profile matching
Interest and demographic persona overlays enabling precision ad targeting and sponsorship value identification
Retention intelligence
Episode-level retention signatures per persona, enabling proactive content intervention during production

2. Architecture Overview
The Audience Simulation Engine is designed as a layered architecture, where each layer builds on the outputs of the previous. The system is grounded in live Redshift data and designed to produce actionable, confidence-scored outputs for content and commercial teams.
□  □  □
Architecture Diagram — Three-Layer Data Flow: Unified Dataset → Synthesized Personas → AI Simulation Engine
[ Diagram to be inserted ]
Figure 1: High-level architecture showing data flow from raw behavioral signals through persona construction to AI-powered simulation outputs
2.1 Layer 1 — Unified Audience Dataset
The foundation of the system. Raw streaming behavioral signals from Fatafat are joined with demographic and interest-based persona profiles to create a single, anonymized audience dataset.
	•	Source 1: Fatafat streaming engagement data — retention curves, episode completion rates, session depth, genre affinity, drop-off patterns
	•	Source 2: Player interaction signals — seek behavior, playback speed preferences, replay patterns, buffering impact
	•	Source 3: Demographic profiles — age group and gender for ~228M users from ML prediction, Amazon identity, and declared MX sources
	•	Source 4: Interest/persona segmentation — ~181M users (ML-derived) and ~54M users (Amazon-sourced) tagged across 16 consumer interest categories
	•	Linkage methodology: UUID-based join across all tables, preserving anonymization and enabling cohort-level analysis without PII exposure
2.2 Layer 2 — Synthesized Persona Set
From the unified dataset, behavioral clustering yields 5–6 content-first personas that together account for approximately 75% of the active Fatafat audience. Each persona is a composite profile, not a demographic segment.
	•	Content identity: Primary genre preferences, narrative complexity tolerance, episode length affinity, series vs. film consumption patterns
	•	Strategic role: Classified as Grow (acquisition-focused, high potential), Nourish (engaged core, depth-oriented), or Sustain (habitual, volume-driven)
	•	Retention signature: Characteristic retention curve shape, typical drop-off point, episode completion rate, binge propensity
	•	Commercial profile: Dominant interest panel memberships, purchase intent signals, affinity with advertiser categories
2.3 Layer 3 — AI Simulation Engine
Pseudo-viewer models trained per persona evaluate incoming content concepts and scripts for predicted audience response. Outputs are directional and confidence-scored, designed for integration into commissioning and content development workflows.
	•	Engagement prediction: Estimated retention curve trajectory and completion likelihood per persona for a given content concept
	•	Narrative density alignment: Match between content complexity/pacing and persona tolerance profile
	•	Audience-fit scoring: Multi-dimensional compatibility score across retention, interest alignment, and demographic fit
	•	Slate gap detection: Real-time identification of content demand signals not currently served by the active Fatafat slate

□  □  □
Persona Architecture Diagram — Grow / Nourish / Sustain Strategic Role Classification
[ Diagram to be inserted ]
Figure 2: Persona strategic role taxonomy showing audience segments mapped to Grow, Nourish, and Sustain categories with behavioral signatures

3. Data Foundation — Available Assets
All data sources required for Phase 1 are available in the Amazon MX Player Redshift data warehouse (AMXP-BI-MCP-PROD). The tables below represent live, production-grade data that can be queried directly — the project is not dependent on CSV extracts or manual data pulls.
Table / Source
Data Domain
Refresh
Key Signals
fatafat.mxp_fatafat_player_engagement
Streaming Behavioral
Live / Daily
Retention curves, completion rates, session depth, show affinity, drop-off events, genre engagement patterns
fatafat.mxp_fatafat_player_interaction_v2
Player Interaction
Live / Daily
Seek behavior, playback speed selection, replay events, buffering impact on session continuity
mxp_age_gender_details_table_v3
User Demographics
Snapshot ~228M users
UUID, age_group (18-24 through 65+), gender (Male/Female), source: ML / Amazon / Declared MX
mxp_persona_details_table_v3
Interest Segments
181M ML + 54M Amazon
UUID, persona_name (16 interest categories incl. Fashion, Beauty, Electronics, Travel), source, process_date
daily_cms_data_table
Content Metadata
Daily
Show names, genres, episode metadata, launch dates, content classification
fatafat.mxp_fatafat_user_membership
Subscriber Behavior
Live / Daily
Membership tier, subscription tenure, renewal patterns, subscriber engagement depth
AppsFlyer Attribution Tables
UA / Attribution
Live / Daily
Paid vs. organic classification, campaign attribution, deep link vs. tab entry, For You vs. Home surface

Data Linkage Architecture
All tables are joined via the anonymized UUID field, which serves as the primary user identifier across the Redshift warehouse. The demographic and persona tables are snapshot-based (one row per UUID per persona tag for the persona table; one row per UUID for the demographics table), enabling clean aggregation at the user level before joining with streaming event data.
	•	UUID-level join: Streaming engagement → Demographics → Persona tags
	•	Persona table is long-format: a single user may carry 10+ persona tags from ML and Amazon sources, requiring aggregation before join
	•	Attribution tables enable paid/organic segmentation, critical for distinguishing organic retention signals from campaign-influenced behavior


Phase 1 — Current Phase
Data Foundation

Phase 1 establishes the empirical foundation for the entire Audience Simulation Engine. The objective is to extract, validate, and characterize all behavioral signals from live Fatafat data, and produce a unified audience dataset with demographic and interest overlays. This phase is executable immediately using live Redshift queries against tables confirmed available in AMXP-BI-MCP-PROD.
Step
Activity
Data Source(s)
Output
1.1
Baseline streaming snapshot: daily active streamers, total watchtime, median session depth, 3s start rate (last 7 days)
fatafat_player_engagement
KPI baseline table
1.2
Demographics breakdown: age/gender distribution of Fatafat 3s streamers; coverage rate by demographic source (ML vs. Amazon vs. Declared)
age_gender_details_table_v3
Demographics profile
1.3
Interest segmentation: top persona/interest segments among Fatafat streamers; cross-tab of interest segments vs. content genre preference
persona_details_table_v3
Interest affinity matrix
1.4
Retention curve analysis: episode-level completion rates across top 20 shows; identify characteristic drop-off points per genre; baseline retention signatures
fatafat_player_engagement
Retention curve library
1.5
User behavior clustering: session patterns, multi-show consumption chains, content preference mapping; identify natural behavioral cohorts prior to formal persona modeling
player_engagement + interaction_v2
Behavioral cluster map
1.6
Entry behavior analysis: organic vs. paid user classification; surface (For You / Home / Search / Deep Link) vs. retention quality; subscriber vs. non-subscriber behavioral split
AppsFlyer + membership tables
Entry-retention matrix

Phase 1 Deliverable
A unified behavioral dataset with demographic and interest overlays, documented in a Phase 1 Analysis Report containing: baseline KPI snapshot, demographics coverage analysis, interest affinity matrix, retention curve library (top 20 shows), behavioral cluster summary, and entry-to-retention quality matrix. This report serves as the direct input to Phase 2 persona construction.
Phase 1 Timeline
	•	Estimated duration: 2–3 weeks
	•	Week 1: Steps 1.1–1.3 — baseline snapshot, demographics, interest segmentation
	•	Week 2: Steps 1.4–1.5 — retention curve analysis, behavioral clustering
	•	Week 3: Step 1.6 + validation and documentation — entry behavior analysis, report assembly
Phase 1 Execution Checklist
	•	Verify access to all 7 data source tables listed in Section 3 via AMXP-BI-MCP-PROD Redshift connection
	•	Run baseline streaming query: total 3s streamers, total watchtime minutes, median session depth, by day for last 14 days
	•	Run demographics coverage query: count distinct UUIDs in age_gender table matched to Fatafat streamers; break out by source (ml / amazon / mxp)
	•	Run top-25 persona/interest query: rank interest segment tags by distinct Fatafat streamer count; cross-tab top 10 segments vs. top 10 shows
	•	Pull episode-level retention curves for top 20 Fatafat shows by total watchtime (last 30 days); calculate P25, P50, P75 completion deciles
	•	Run user behavioral clustering query: segment users by session depth quintile x genre breadth x binge rate; identify 8–12 natural behavioral cohorts
	•	Run entry behavior analysis: organic vs. paid cohort comparison on 7-day retention rate and avg sessions per user; For You vs. Home surface performance
	•	Assemble Phase 1 Analysis Report and circulate for stakeholder review before Phase 2 kickoff


Phase 2
Persona Construction

Using the unified behavioral dataset from Phase 1 as its input, Phase 2 builds the synthesized persona set that forms the audience model for the simulation engine. The goal is 5–6 content-first personas that together cover approximately 75% of the active Fatafat audience and carry actionable behavioral, strategic, and commercial profiles.
5.1 Clustering Methodology
Users will be clustered across five behavioral dimensions, derived from the Phase 1 analysis outputs:
Dimension
Signal Source
Segmentation Variables
Retention Profile
Episode completion rates, drop-off timing, binge propensity from fatafat_player_engagement
High / Mid / Low completer; early / mid / late drop-off; binge vs. casual
Content Preference
Genre affinity, multi-show consumption patterns, series vs. film ratio
Genre cluster (drama / comedy / reality / action); mono vs. multi-genre; format preference
Viewing Behavior
Session depth, frequency, time-of-day patterns, entry surface from interaction tables
Session depth quintile; daily vs. weekly; prime-time vs. off-peak; mobile vs. TV
Demographic Overlay
Age group, gender from mxp_age_gender_details_table_v3
Age band (18–24, 25–34, 35–44, 45+); gender; age-gender interaction
Interest Depth
Persona tag count, interest category breadth from mxp_persona_details_table_v3
Single-interest vs. multi-interest; ML source vs. Amazon source; interest-genre alignment

5.2 Strategic Role Assignment
Once behavioral clusters are formed, each cluster is assigned a strategic role within the Grow / Nourish / Sustain taxonomy. Role assignment is driven by the intersection of segment size and engagement depth:
	•	Grow: Large segments with moderate engagement and high growth potential — acquisition-priority, often driven by specific content triggers
	•	Nourish: Mid-sized segments with deep engagement and high retention — loyalty-priority, most receptive to original and franchise content
	•	Sustain: Large habitual-viewing segments — volume-priority, high commercial value due to session frequency and ad exposure
5.3 Persona Deliverable Format
Each of the 5–6 final personas will be documented in a standardized persona card covering:
	•	Persona name and archetype label
	•	Strategic role (Grow / Nourish / Sustain) with rationale
	•	Behavioral fingerprint: retention signature, content preference, session profile
	•	Demographic profile: age/gender distribution and skew
	•	Commercial profile: top 3 interest panels, advertiser category affinity, estimated commercial value index
	•	Coverage metric: % of active Fatafat audience represented by this persona
□  □  □
Persona Card Template — Example Layout for a Single Synthesized Persona
[ Diagram to be inserted ]
Figure 3: Example persona card format showing behavioral fingerprint, strategic role, and commercial profile fields
Phase 2 Timeline
	•	Estimated duration: 2–3 weeks (following Phase 1 completion)
	•	Week 1: Clustering runs and initial cohort validation
	•	Week 2: Strategic role assignment and persona card drafting
	•	Week 3: Coverage validation (confirm ~75% audience coverage) and stakeholder review


Phase 3
AI Model Training

Phase 3 trains the pseudo-viewer models that form the core of the simulation engine. Each persona from Phase 2 becomes the training target for a dedicated model, calibrated against historical Fatafat show performance data.
6.1 Training Data Construction
	•	Historical show performance: 12–24 months of Fatafat streaming data, segmented by persona cluster membership
	•	Show-level outcomes: Completion rates, retention curve shape, episode drop-off timing, binge rates per persona segment
	•	Content attributes: Genre, episode length, narrative complexity (proxy: pacing score from retention curve shape), cast profile, original vs. acquired
	•	Commercial outcomes: Session frequency, ad exposure per persona, interest-segment engagement patterns
6.2 Model Outputs
For each incoming content concept or script, the trained models produce:
Output Type
Description
Format
Engagement Prediction
Estimated retention curve trajectory and episode completion likelihood, per persona
Curve projection + completion % with confidence band
Narrative Density Fit
Match between content pacing/complexity and persona tolerance profile derived from historical preferences
Fit score 0–100 with flagged mismatches
Audience-Fit Score
Multi-dimensional compatibility score across retention alignment, interest-genre fit, and demographic skew
Composite score with dimension breakdown
Slate Gap Signal
Whether the content concept addresses an identified demand gap for one or more personas in the current Fatafat slate
Gap match flag + underserved persona list

6.3 Calibration and Validation
Models will be validated against a held-out set of historical Fatafat shows (not used in training) to establish baseline prediction accuracy before deployment:
	•	Hold-out validation set: Last 3 months of new Fatafat show launches
	•	Primary accuracy metric: Predicted vs. actual retention curve correlation (Pearson r) per persona
	•	Secondary metrics: Episode completion rate prediction error (MAE), audience-fit score vs. actual persona engagement split
	•	Minimum accuracy threshold for pilot deployment: r ≥ 0.70 on retention curve prediction across held-out set
Phase 3 Timeline
	•	Estimated duration: 4–6 weeks (following Phase 2 completion)
	•	Weeks 1–2: Training data construction and feature engineering
	•	Weeks 3–4: Model training per persona
	•	Weeks 5–6: Calibration, hold-out validation, accuracy documentation


Phase 4
Integration Pilot

Phase 4 moves from model development to real-world validation. The objective is to run the simulation engine against an active or upcoming Fatafat commission, establish output formats and confidence scoring protocols, and generate the first prediction-vs-actuals comparison.
7.1 Pilot Show Selection Criteria
	•	Show is in active development or pre-production (not yet launched) OR within 4–6 weeks of launch where pre-launch predictions can be compared against incoming actuals
	•	Show has reasonable historical comparables in the Fatafat catalog for model calibration
	•	Content and commissioning team has agreed to participate and share production/brief materials
	•	Show spans at least 2–3 target personas to enable multi-persona simulation output
7.2 Pilot Process
#
Step
Detail
1
Brief intake
Ingest show concept brief, episode structure, and available script or treatment into simulation engine input format
2
Persona simulation run
Run pseudo-viewer models for each relevant persona; generate engagement prediction, narrative fit score, and audience-fit score
3
Output review
Review outputs with content team; document confidence scores and flag any low-fit personas or narrative density mismatches
4
Post-launch tracking
Track actual show performance by persona segment in Redshift after launch; compare predicted vs. actual retention curves
5
Accuracy report
Produce pilot results report with prediction accuracy assessment and model recalibration recommendations

Phase 4 Timeline
	•	Estimated duration: 3–4 weeks
	•	Dependent on pilot show availability and content team engagement
	•	Post-launch accuracy reporting requires 4–6 weeks of show performance data post-launch


Phase 5
Live Deployment

Following successful pilot validation, Phase 5 deploys the Audience Simulation Engine as a production system integrated into content commissioning, slate planning, and advertising workflows at Amazon MX Player Fatafat.
8.1 Deployment Workstreams
	•	Content commissioning integration: Simulation engine outputs incorporated into the standard commissioning brief review process; persona-fit scores included in greenlight documentation
	•	Slate gap detection dashboard: Real-time dashboard surfacing underserved persona demand signals against the active Fatafat slate; updated weekly from live Redshift queries
	•	Commercial profile matching: Interest and demographic persona overlays made available to the advertising and partnerships team for precision targeting and sponsorship value identification
	•	Model maintenance: Quarterly recalibration of pseudo-viewer models using updated behavioral data; persona set reviewed biannually for cluster drift
8.2 Deployment Architecture
□  □  □
Deployment Architecture Diagram — Production Integration Points: Commissioning / Slate Planning / Ad Targeting
[ Diagram to be inserted ]
Figure 4: Production deployment architecture showing simulation engine integration with commissioning, slate planning, and advertising workflows
Phase 5 Timeline
	•	Estimated duration: 4–6 weeks (following Phase 4 pilot validation)
	•	Weeks 1–2: Production infrastructure setup and dashboard development
	•	Weeks 3–4: Integration testing with commissioning and commercial teams
	•	Weeks 5–6: Soft launch, monitoring setup, and full deployment

9. Roadmap Summary
Phase
Name
Key Deliverable
Duration
Status
1
Data Foundation
Unified behavioral dataset with demographic and interest overlays; Phase 1 Analysis Report
2–3 weeks
Active
2
Persona Construction
5–6 documented synthesized persona cards covering ~75% of active Fatafat audience
2–3 weeks
Planned
3
AI Training
Trained pseudo-viewer models per persona with validation accuracy metrics
4–6 weeks
Planned
4
Integration Pilot
Pilot results report with prediction vs. actual accuracy assessment for one Fatafat commission
3–4 weeks
Planned
5
Live Deployment
Production system deployed across commissioning, slate planning, and advertising workflows
4–6 weeks
Planned

Total estimated timeline from Phase 1 kickoff to live deployment: 15–22 weeks (approximately 4–5 months), assuming sequential phase execution with standard review and validation gates between phases.

10. Success Metrics & KPIs
The following KPIs will be tracked across phases to measure both the technical performance of the system and its business impact on content and commercial outcomes at Fatafat.
KPI
Definition
Phase
Target
Measurement Method
Persona Coverage
% of active Fatafat audience mapped to a synthesized persona
2
≥75% of 3s streamers
Cluster analysis on Phase 1 behavioral dataset
Demographic Overlay Rate
% of Fatafat streamers with a matched age/gender record
1
≥60% coverage
UUID join between engagement and demographics tables
Interest Segment Coverage
% of Fatafat streamers with at least one persona tag
1
≥50% tag coverage
UUID join between engagement and persona tables
Retention Prediction Accuracy
Pearson r: predicted vs. actual retention curve per persona
3
r ≥ 0.70 on hold-out set
Hold-out validation against unseen show launches
Audience-Fit Score Validity
Correlation between fit score and actual per-persona engagement split
4
r ≥ 0.65 on pilot show
Phase 4 pilot prediction vs. actuals comparison
Time-to-Insight
Days from content brief submission to simulation output
5
≤3 business days
Process timing tracked post-deployment
Slate Gap Detection Rate
% of identified slate gaps validated by post-commission content performance
5
≥70% at 6-month review
Slate gap flags vs. subsequent commissioning outcomes
Commercial Value Uplift
Ad targeting precision improvement (CTR delta) for persona-matched campaigns
5
+15% CTR vs. baseline
A/B comparison of persona-targeted vs. broad campaigns

11. Risks & Mitigations
Risk
Level
Description
Mitigation
Data Quality — Demographic Coverage
High
ML-predicted demographics may have significant error rates, particularly for age group prediction. Coverage gaps in under-represented demographics could bias persona construction.
Run demographic coverage and source distribution analysis in Phase 1 Step 1.2. Apply confidence weighting by source (Declared > Amazon > ML). Flag low-coverage personas in outputs.
Persona Tag Sparsity
Medium
A subset of Fatafat streamers may have no persona tags in mxp_persona_details_table_v3, particularly newer users or users acquired via certain channels.
Assess tag coverage rate in Phase 1 Step 1.3. Use genre affinity and viewing behavior as proxy signals for interest segmentation where tags are absent.
Model Drift
Medium
User behavioral patterns on Fatafat may shift significantly over time, causing pseudo-viewer models to produce increasingly inaccurate predictions.
Schedule quarterly model recalibration. Monitor prediction accuracy metrics post-deployment. Implement drift detection alerts when prediction error exceeds threshold.
Cold Start for New Genres
Low
The simulation engine relies on historical Fatafat performance data. For entirely new content genres with no Fatafat comparables, predictions will have wide confidence bands.
Use industry benchmarks (Cinelytic, Parrot Analytics demand data) as priors for new genres. Flag wide-confidence outputs explicitly in simulation reports.
Privacy & Compliance
Medium
Linking behavioral, demographic, and interest data at the user level requires careful handling to ensure compliance with applicable data privacy regulations and Amazon data governance policies.
All analysis conducted on anonymized UUID-based data. No PII exposure in outputs or persona cards. Compliance review required before Phase 3 AI training data construction.
Stakeholder Adoption
Medium
Content and commissioning teams may not trust or act on simulation engine outputs if the predictions are not intuitive or the confidence scoring is unclear.
Phase 4 pilot is designed to build credibility through documented prediction accuracy. Invest in clear output format design and stakeholder training alongside Phase 5 deployment.

12. Industry Benchmarks & External Validation
The Audience Simulation Engine approach is grounded in and validated by publicly documented industry implementations at leading streaming and entertainment platforms. These benchmarks establish the feasibility and expected value of the methodology.
Platform
System
Key Metric / Result
Relevance to Our Approach
Cinelytic
AI-powered content intelligence platform used by major studios
85% accuracy in pre-production revenue forecasting for film and TV projects
Demonstrates that AI-driven audience modeling can achieve high predictive accuracy before content launch — the core premise of our simulation engine
Disney Audience Graph
Disney's unified audience data layer across streaming, broadcast, and theme parks
Cross-platform audience identity resolution and content performance prediction at the persona segment level
Validates the Layer 1 unified audience dataset approach; shows that linking behavioral and identity data at scale creates durable audience intelligence
Netflix Ads Suite
Netflix's advertiser-facing audience targeting product
Uses content affinity and viewing behavior clustering to create targetable audience segments for brand advertisers
Directly parallels our commercial profile layer; confirms that behavioral clustering from streaming data produces commercially valuable audience segments
Parrot Analytics
Global content demand measurement and forecasting platform
Demand sensing: quantifies audience demand for content before acquisition or production decisions using social, search, and behavioral signals
Validates the slate gap detection use case; demonstrates that leading platforms use demand signals to inform commissioning ahead of content gaps widening

Our Differentiation
The Fatafat Audience Simulation Engine benefits from a data advantage that distinguishes it from third-party industry solutions:
	•	First-party behavioral data: Direct access to all Fatafat streaming events in real time, without API latency or data sampling limitations
	•	Amazon identity integration: Amazon-sourced demographic and interest persona data augments ML-derived profiles, creating a richer audience model than behavioral data alone
	•	16 consumer panel categories: The breadth of interest segmentation enables commercial persona overlays that third-party tools cannot replicate at this scale
	•	Platform-native deployment: Simulation outputs can be integrated directly into commissioning and ad targeting workflows without third-party intermediation

Appendix: Key Terms & Definitions
Term
Definition
Audience Simulation Engine
The three-layer system combining unified behavioral data, synthesized personas, and AI pseudo-viewer models to predict audience response to content pre-launch
Synthetic Persona / Pseudo-Viewer
A composite audience profile constructed from behavioral clusters and enriched with demographic and interest data, used as the input identity for AI simulation runs
Unified Audience Dataset
The Layer 1 output: a UUID-joined dataset linking Fatafat streaming behavioral signals, demographics, and interest persona tags for all active users
Grow / Nourish / Sustain
Strategic persona role taxonomy: Grow = acquisition-priority large segments; Nourish = engagement-priority deep loyalists; Sustain = volume-priority habitual viewers
Retention Signature
The characteristic retention curve shape for a given persona — defines where in an episode or series a persona typically drops off, replays, or completes
Slate Gap
A content demand signal from one or more personas that is not currently addressed by any show in the active Fatafat content slate
Engagement Prediction
A model output estimating the probable retention curve and completion rate for a new content concept, based on persona behavioral history
Narrative Density Fit
The alignment between a show's pacing and complexity and a persona's demonstrated tolerance for narrative complexity (derived from historical retention patterns)
Commercial Profile
The interest panel memberships and advertiser category affinities associated with a persona, used for ad targeting and sponsorship value identification
3s Streamer
A user who has streamed at least 3 seconds of content on Fatafat in a given period — the standard minimum engagement threshold for counting active users
UUID
Anonymized unique user identifier used to join behavioral, demographic, and persona data tables in Redshift without PII exposure
mxp_persona_details_table_v3
The Redshift table containing user-level interest/persona tags, sourced from ML prediction (~181M users) and Amazon identity data (~54M users)
mxp_age_gender_details_table_v3
The Redshift table containing ML-predicted and declared age group and gender for ~228M Amazon MX Player users

