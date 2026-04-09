SELECT
    eng.uuid,
    eng.total_streams,
    eng.total_minutes,
    eng.unique_episodes,
    COALESCE(dem.age_group, 'Unknown') as age_group,
    COALESCE(dem.gender, 'Unknown') as gender,
    COALESCE(ch.primary_channel, 'Unknown') as primary_channel
FROM (
    SELECT uuid,
           COUNT(*) as total_streams,
           ROUND(SUM(CAST(playtime AS FLOAT))/60000, 2) as total_minutes,
           COUNT(DISTINCT videoid) as unique_episodes
    FROM fatafat.mxp_fatafat_player_engagement
    WHERE DATE(start_date) = '2026-04-05'
      AND event = 'onlineStreamEnd'
      AND CAST(playtime AS FLOAT) >= 3000
      AND networkType IS NOT NULL
      AND internalNetworkStatus > 1
      AND pagetype = 'titlePage'
    GROUP BY uuid
) eng
LEFT JOIN (
    SELECT uuid,
           CASE
               WHEN age BETWEEN 18 AND 24 THEN '18-24'
               WHEN age BETWEEN 25 AND 34 THEN '25-34'
               WHEN age BETWEEN 35 AND 44 THEN '35-44'
               WHEN age BETWEEN 45 AND 54 THEN '45-54'
               WHEN age >= 55 THEN '55+'
               ELSE 'Unknown'
           END as age_group,
           CASE WHEN gender = 'm' THEN 'Male' WHEN gender = 'f' THEN 'Female' ELSE 'Unknown' END as gender
    FROM fatafat.mxp_fatafat_demographics_table
) dem ON eng.uuid = dem.uuid
LEFT JOIN (
    SELECT uuid, primary_channel FROM (
        SELECT uuid,
               CASE
                   WHEN dputmsource IN ('perf_m','perf_g','fatafat_inmobi','perf_u','perf_fb','perf_inmobi','perf_samsung','perf_oppo','perf_vivo','perf_xiaomi','perf_realme','perf_tiktok','perf_snap','perf_twitter','perf_dv360','perf_moloco','perf_mintegral','perf_unity','perf_applovin','perf_ironsource','perf_liftoff','perf_digital_turbine','perf_aura','perf_adjoe','perf_chartboost','perf_pangle','perf_bigo','perf_kwai','perf_glance','perf_taboola') THEN 'Paid'
                   WHEN dputmsource = 'mx_internal_notif' THEN 'Push'
                   WHEN dputmsource IS NULL OR dputmsource = '' THEN 'Organic'
                   ELSE 'Other'
               END as primary_channel,
               ROW_NUMBER() OVER (PARTITION BY uuid ORDER BY CAST(playtime AS FLOAT) DESC) as rn
        FROM fatafat.mxp_fatafat_player_engagement
        WHERE DATE(start_date) = '2026-04-05'
          AND event = 'onlineStreamEnd'
          AND CAST(playtime AS FLOAT) >= 3000
          AND networkType IS NOT NULL
          AND internalNetworkStatus > 1
    ) WHERE rn = 1
) ch ON eng.uuid = ch.uuid;
