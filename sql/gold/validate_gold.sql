-- Each query returns zero rows when the documented grain and data contract hold.

SELECT observation_id
FROM part4_ops.gold.fact_batch_quality
GROUP BY observation_id
HAVING count(*) > 1;

SELECT excursion_id
FROM part4_ops.gold.fact_cold_chain_excursion
GROUP BY excursion_id
HAVING count(*) > 1;

SELECT batch_id, effective_start_utc
FROM part4_ops.gold.dim_batch_history
GROUP BY batch_id, effective_start_utc
HAVING count(*) > 1;

SELECT site_id
FROM part4_ops.gold.dim_site
GROUP BY site_id
HAVING count(*) > 1;

SELECT product_id
FROM part4_ops.gold.dim_product
GROUP BY product_id
HAVING count(*) > 1;

SELECT site_id, product_id, reporting_date
FROM part4_ops.gold.kpi_quality_summary
GROUP BY site_id, product_id, reporting_date
HAVING count(*) > 1;
