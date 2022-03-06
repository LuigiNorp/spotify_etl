SELECT orders
FROM lunchorders
WHERE orders ->> 'order_date' = '2020-12-11';
