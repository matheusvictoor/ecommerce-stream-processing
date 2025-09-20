CREATE TABLE IF NOT EXISTS sales_summary (
    id SERIAL PRIMARY KEY,
    category VARCHAR(100),
    brand VARCHAR(100),
    payment_method VARCHAR(50),
    total_revenue NUMERIC(10,2),
    window_start TIMESTAMP,
    window_end TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_category ON sales_summary(category);
CREATE INDEX IF NOT EXISTS idx_payment ON sales_summary(payment_method);
CREATE INDEX IF NOT EXISTS idx_window ON sales_summary(window_start);