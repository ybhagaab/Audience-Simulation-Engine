-- ============================================================
-- PHASE 2: User-Level Feature Matrix — Full 5-Dimension Queries
-- ============================================================
-- Date window: 7 days (Mar 30 – Apr 5, 2026)
-- Cohort: All Fatafat 3s streamers in the window
-- Performance: Single-table aggregations first, CMS joins only
--   on small result sets. Each query runs independently.
--   Export each result as CSV, merge in Python.
-- ============================================================
-- Base filters (ALWAYS applied):
--   event = 'onlineStreamEnd'
--   CAST(playtime AS FLOAT) >= 3000   (per-stream 3s threshold)
--   networkType IS NOT NULL
--   internalNetworkStatus > 1
--   pagetype = 'titlePage'            (show playbacks only)
-- ============================================================


-- ============================================================
-- Q2.1 — ENGAGEMENT DEPTH (Dimension 1)
-- ============================================================
-- Output: q21_engagement.csv
-- Features: total_streams, total_minutes, unique_episodes,
--           active_days, total_sessions
-- Derived in Python: mpc, minutes_per_stream, streams_per_day,
--                    episodes_per_session, engagement_tier
-- Estimated runtime: ~25-35s
-- ============================================================

SELECT
    uuid,
    COUNT(*)                              AS total_streams,
    ROUND(SUM(CAST(playtime AS FLOAT)) / 60000, 2) AS total_minutes,
    COUNT(DISTINCT videoid)               AS unique_episodes,
    COUNT(DISTINCT DATE(start_date))      AS active_days,
    COUNT(DISTINCT sid)                   AS total_sessions
FROM fatafat.mxp_fatafat_player_engagement
WHERE DATE(start_date) BETWEEN '2026-03-30' AND '2026-04-05'
  AND event = 'onlineStreamEnd'
  AND CAST(playtime AS FLOAT) >= 3000
  AND networkType IS NOT NULL
  AND internalNetworkStatus > 1
  AND pagetype = 'titlePage'
GROUP BY uuid;


-- ============================================================
-- Q2.2a — CONTENT PREFERENCE: User × Video aggregation (Dim 2)
-- ============================================================
-- Output: q22a_user_video.csv
-- This is the raw user×video matrix. CMS join happens in Python
-- to derive show names, genres, episode depth.
-- Estimated runtime: ~25-35s
-- ============================================================

SELECT
    uuid,
    videoid,
    COUNT(*)                              AS streams,
    ROUND(SUM(CAST(playtime AS FLOAT)) / 60000, 2) AS minutes
FROM fatafat.mxp_fatafat_player_engagement
WHERE DATE(start_date) BETWEEN '2026-03-30' AND '2026-04-05'
  AND event = 'onlineStreamEnd'
  AND CAST(playtime AS FLOAT) >= 3000
  AND networkType IS NOT NULL
  AND internalNetworkStatus > 1
  AND pagetype = 'titlePage'
GROUP BY uuid, videoid;


-- ============================================================
-- Q2.2b — CMS LOOKUP for Fatafat videos (Dim 2 + Dim 3)
-- ============================================================
-- Output: q22b_cms_lookup.csv
-- Small result set (~5-10K rows). Includes genre fields,
-- episode_number, and language for content classification.
-- Estimated runtime: <5s
-- ============================================================

SELECT DISTINCT
    video_id,
    tv_show_name,
    channel_ids,
    genre_name,
    secondary_genre_name,
    language_name,
    content_category,
    episode_number
FROM daily_cms_data_table
WHERE is_fatafat_micro_show = '1'
  AND tv_show_name NOT IN ('[]', '[unknown]');


-- ============================================================
-- Q2.3 — RETENTION PROFILE: Session-level episodes (Dim 3)
-- ============================================================
-- Output: q23_session_episodes.csv
-- Per-session episode count for binge propensity calculation.
-- Estimated runtime: ~25-35s
-- ============================================================

SELECT
    uuid,
    sid,
    COUNT(DISTINCT videoid) AS episodes_in_session
FROM fatafat.mxp_fatafat_player_engagement
WHERE DATE(start_date) BETWEEN '2026-03-30' AND '2026-04-05'
  AND event = 'onlineStreamEnd'
  AND CAST(playtime AS FLOAT) >= 3000
  AND networkType IS NOT NULL
  AND internalNetworkStatus > 1
  AND pagetype = 'titlePage'
GROUP BY uuid, sid;


-- ============================================================
-- Q2.4a — DEMOGRAPHICS (Dimension 4)
-- ============================================================
-- Output: q24a_demographics.csv
-- Join streamer cohort to age/gender lookup table.
-- Estimated runtime: ~30-40s (cohort subquery + join)
-- ============================================================

WITH streamers AS (
    SELECT DISTINCT uuid
    FROM fatafat.mxp_fatafat_player_engagement
    WHERE DATE(start_date) BETWEEN '2026-03-30' AND '2026-04-05'
      AND event = 'onlineStreamEnd'
      AND CAST(playtime AS FLOAT) >= 3000
      AND networkType IS NOT NULL
      AND internalNetworkStatus > 1
      AND pagetype = 'titlePage'
)
SELECT
    s.uuid,
    COALESCE(d.age_group, 'Unknown') AS age_group,
    COALESCE(d.gender, 'Unknown')    AS gender
FROM streamers s
LEFT JOIN mxp_age_gender_details_table_v3 d ON s.uuid = d.uuid;


-- ============================================================
-- Q2.4b — PRIMARY CHANNEL per user (Dimension 5)
-- ============================================================
-- Output: q24b_channel.csv
-- Classifies each user's primary channel by highest total
-- watchtime across the 7-day window.
-- Fixed: Aggregates first, then ranks (no window function
-- over aggregate).
-- Estimated runtime: ~30-40s
-- ============================================================

WITH channel_watchtime AS (
    SELECT
        uuid,
        CASE
            WHEN dputmsource IN (
                'perf_m','perf_g','fatafat_inmobi','fatafat_aff_affle',
                'fatafat_aff_inmobi','fatafat_aff_xiaomi','perf_xiaomi',
                'fatafat_aff_affinity','aff_affle','perf_inmobi','perf_affle',
                'perf_aff','branding_meta','branding_META','branding_YT',
                'branding_publisher','google_web',
                'perf_u','perf_fb','perf_samsung','perf_oppo','perf_vivo',
                'perf_realme','perf_tiktok','perf_snap','perf_twitter',
                'perf_dv360','perf_moloco','perf_mintegral','perf_unity',
                'perf_applovin','perf_ironsource','perf_liftoff',
                'perf_digital_turbine','perf_aura','perf_adjoe',
                'perf_chartboost','perf_pangle','perf_bigo','perf_kwai',
                'perf_glance','perf_taboola'
            ) THEN 'Paid'
            WHEN dputmsource = 'mx_internal_notif' THEN 'Push'
            WHEN dputmsource IN (
                'personal-ott-toast-v3','personal-ott-toast-v4',
                'personal-ott-toast-v5','ott_nudges'
            ) THEN 'OTT Notification'
            WHEN dputmsource IN (
                'paid_int-con-perf-dfp_mx_internal-app',
                'house_int-con-perf-dfp_mx_internal-app'
            ) THEN 'Internal Ad'
            WHEN dputmsource IS NULL OR dputmsource = '' THEN 'Organic'
            ELSE 'Other'
        END AS channel_category,
        SUM(CAST(playtime AS FLOAT)) AS total_playtime
    FROM fatafat.mxp_fatafat_player_engagement
    WHERE DATE(start_date) BETWEEN '2026-03-30' AND '2026-04-05'
      AND event = 'onlineStreamEnd'
      AND CAST(playtime AS FLOAT) >= 3000
      AND networkType IS NOT NULL
      AND internalNetworkStatus > 1
      AND pagetype = 'titlePage'
    GROUP BY uuid, channel_category
),
ranked AS (
    SELECT
        uuid,
        channel_category AS primary_channel,
        ROW_NUMBER() OVER (PARTITION BY uuid ORDER BY total_playtime DESC) AS rn
    FROM channel_watchtime
)
SELECT uuid, primary_channel
FROM ranked
WHERE rn = 1;


-- ============================================================
-- Q2.5 — INTEREST TAGS (Dimension 5b - Optional)
-- ============================================================
-- Output: q25_persona_tags.csv
-- ML persona tags for the streamer cohort. Long format:
-- multiple rows per user. Pivoted in Python.
-- Estimated runtime: ~30-60s (cohort subquery + join on 181M table)
-- ============================================================

WITH streamers AS (
    SELECT DISTINCT uuid
    FROM fatafat.mxp_fatafat_player_engagement
    WHERE DATE(start_date) BETWEEN '2026-03-30' AND '2026-04-05'
      AND event = 'onlineStreamEnd'
      AND CAST(playtime AS FLOAT) >= 3000
      AND networkType IS NOT NULL
      AND internalNetworkStatus > 1
      AND pagetype = 'titlePage'
)
SELECT s.uuid, p.persona_name
FROM streamers s
JOIN mxp_persona_details_table_v3 p ON s.uuid = p.uuid
WHERE p.source = 'ml';
-- NOTE: Returns multiple rows per user (long format).
-- In Python: COUNT DISTINCT persona_name per uuid for tag breadth.
