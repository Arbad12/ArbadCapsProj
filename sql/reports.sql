-- a) Order totals —
SELECT COUNT(*) FROM orders
-- total_orders = 180

SELECT SUM(
    o.quantity * p.price * (1 - COALESCE(o.discount_pct, 0) / 100.0)
) AS total_revenue
FROM orders o
JOIN products p
    ON o.product_id = p.product_id;
-- total_revenue = 99860.20

SELECT AVG(
    o.quantity * p.price * (1 - COALESCE(o.discount_pct, 0) / 100.0)
) AS avg_order_value
FROM orders o
JOIN products p
    ON o.product_id = p.product_id;
-- avg_order_value = 554.78


-- b) COUNT(*) vs COUNT(column) —
SELECT COUNT(*),
COUNT(rating),
COUNT(*) - COUNT(rating)
FROM orders
-- 180|165|15


