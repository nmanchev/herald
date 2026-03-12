-- Example: fetch key metrics for stakeholder briefing
SELECT
    metric_name,
    current_value,
    previous_value,
    ROUND((current_value - previous_value) / previous_value * 100, 1) AS pct_change
FROM briefing_metrics
WHERE report_date = CURRENT_DATE()
ORDER BY metric_name
