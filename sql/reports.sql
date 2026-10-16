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
FROM orders;
-- 180|165|15


-- c) LEFT JOIN with a genuine zero-match row —
SELECT c.customer_id,c.name
FROM customers c
LEFT JOIN orders o
  ON c.customer_id = o.customer_id
GROUP BY c.customer_id,c.name
HAVING COUNT(o.order_id) = 0;
-- C045|Vihaan

SELECT c.customer_id,c.name
FROM customers c
WHERE c.customer_id NOT IN (SELECT DISTINCT customer_id FROM orders);
-- C045|Vihaan


-- d) GROUP BY + HAVING —
SELECT
    c.city,
    COUNT(o.order_id) AS total_orders,
    SUM(CASE WHEN o.returned = 1 THEN 1 END) AS returned_orders,
    ROUND(100.0 * SUM(CASE WHEN o.returned = 1 THEN 1 END)
           / COUNT(o.order_id),1
           ) AS return_rate_pct
FROM orders o
JOIN customers c
    ON o.customer_id = c.customer_id
GROUP BY c.city
HAVING return_rate_pct > 20
ORDER BY return_rate_pct DESC;
--Jaipur|19|8|42.1
--Lucknow|49|15|30.6
--Bangalore|33|8|24.2

-- e) Ranking with ORDER BY + LIMIT/OFFSET — 
SELECT
    c.customer_id,
    c.name,
    SUM(
        o.quantity * p.price * (1 - COALESCE(o.discount_pct, 0) / 100.0)
    ) AS total_spend
FROM orders o
JOIN customers c
    ON o.customer_id = c.customer_id
JOIN products p
    ON o.product_id = p.product_id
GROUP BY c.customer_id, c.name
ORDER BY total_spend DESC, customer_id ASC 
LIMIT 5;
-- If two customers have the same total_spend, it sorts those tied rows by customer_id in ascending order.
--C043|Reyansh|12920.0
--C026|Isha|8371.6
--C008|Meera|4564.6
--C011|Arjun|4111.0
--C042|Sanya|3785.0

SELECT
    c.customer_id,
    c.name,
    SUM(
        o.quantity * p.price * (1 - COALESCE(o.discount_pct, 0) / 100.0)
    ) AS total_spend
FROM orders o
JOIN customers c
    ON o.customer_id = c.customer_id
JOIN products p
    ON o.product_id = p.product_id
GROUP BY c.customer_id, c.name
ORDER BY total_spend DESC, customer_id ASC 
LIMIT 3 OFFSET 2;
--C008|Meera|4564.6
--C011|Arjun|4111.0
--C042|Sanya|3785.0
