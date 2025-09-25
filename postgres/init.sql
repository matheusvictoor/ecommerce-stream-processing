-- Resumo por Categoria + Método de Pagamento
CREATE TABLE category_payment_summary (
    id SERIAL PRIMARY KEY,
    product_category VARCHAR(100) NOT NULL,
    payment_method VARCHAR(100) NOT NULL,
    total_revenue NUMERIC(15,2) NOT NULL,
    window_start TIMESTAMP DEFAULT NOW(),
    window_end TIMESTAMP DEFAULT NOW(),
    timestamp TIMESTAMP
);

-- Resumo por Marca
CREATE TABLE brand_summary (
    id SERIAL PRIMARY KEY,
    product_brand VARCHAR(100) NOT NULL,
    total_revenue NUMERIC(15,2) NOT NULL,
    window_start TIMESTAMP DEFAULT NOW(),
    window_end TIMESTAMP DEFAULT NOW(),
    timestamp TIMESTAMP
);

-- Resumo por Categoria + Hora
CREATE TABLE category_hour_summary (
    id SERIAL PRIMARY KEY,
    product_category VARCHAR(100) NOT NULL,
    hour_bucket VARCHAR(50) NOT NULL,
    total_revenue NUMERIC(15,2) NOT NULL,
    window_start TIMESTAMP DEFAULT NOW(),
    window_end TIMESTAMP DEFAULT NOW(),
    timestamp TIMESTAMP
);
