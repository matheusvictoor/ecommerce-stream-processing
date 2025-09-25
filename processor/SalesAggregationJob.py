from datetime import datetime
from quixstreams import Application
from quixstreams.sinks.community.postgresql import PostgreSQLSink


# função genérica para adicionar janelas
def format_with_window(window_result, extra_fields=None):
    start_ts = datetime.utcfromtimestamp(window_result["start"] / 1000.0)
    end_ts = datetime.utcfromtimestamp(window_result["end"] / 1000.0)
    value = window_result["value"]

    base = {
        "total_revenue": value.get("total_revenue", 0.0),
        "window_start": start_ts,
        "window_end": end_ts,
    }

    if extra_fields:
        base.update(extra_fields(window_result))

    return base

# função genérica para pipeline de agregação
def build_windowed_agg(sdf, group_by_key, extra_fields_fn, table_name, agg_name):
    sink = PostgreSQLSink(
        host="postgres",
        port=5432,
        dbname="ecommerce",
        user="user",
        password="password",
        table_name=table_name
    )

    return (
        sdf.group_by(lambda row: row[group_by_key], name=agg_name)
        .tumbling_window(duration_ms=5000)
        .reduce(
            initializer=lambda row: {
                group_by_key: row.get(group_by_key, "unknown"),
                "total_revenue": row.get("total_amount", 0.0),
            },
            reducer=lambda agg, row: {
                group_by_key: agg.get(group_by_key, "unknown"),
                "total_revenue": agg.get("total_revenue", 0.0) + row.get("total_amount", 0.0),
            },
        )
        .final()
        .apply(lambda w: format_with_window(w, extra_fields_fn))
        .apply(lambda row: print(f"-> Resultado {table_name}: {row}") or row)
        .sink(sink)
    )

app = Application(broker_address="kafka:9092", auto_offset_reset="latest")
topic = app.topic("transactions")
sdf = app.dataframe(topic=topic)


# agregacao categoria + pagamento
def extra_fields_category_payment(value):
    return {
        "product_category": value.get("product_category", "unknown"),
        "payment_method": value.get("payment_method", "unknown"),
    }


build_windowed_agg(
    sdf,
    group_by_key="product_category",
    extra_fields_fn=extra_fields_category_payment,
    table_name="category_payment_summary",
    agg_name="agg_category_payment",
)


# agregacao marca
def extra_fields_brand(value):
    return {"product_brand": value.get("product_brand", "unknown")}


build_windowed_agg(
    sdf,
    group_by_key="product_brand",
    extra_fields_fn=extra_fields_brand,
    table_name="brand_summary",
    agg_name="agg_brand",
)

# agregacao categoria + hora
def extra_fields_category_hour(window_result):
    start_dt = datetime.utcfromtimestamp(window_result["start"] / 1000.0)
    hour_bucket = start_dt.replace(minute=0, second=0, microsecond=0)
    return {
        "product_category": window_result["value"].get("product_category", "unknown"),
        "hour_bucket": hour_bucket,
    }


build_windowed_agg(
    sdf,
    group_by_key="product_category",
    extra_fields_fn=extra_fields_category_hour,
    table_name="category_hour_summary",
    agg_name="agg_category_hour",
)

if __name__ == "__main__":
    app.run()
