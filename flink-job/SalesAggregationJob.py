from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.connectors.kafka import KafkaSource, KafkaOffsetsInitializer
from pyflink.common.serialization import SimpleStringSchema
from pyflink.common.typeinfo import Types
from pyflink.datastream.window import TumblingProcessingTimeWindows
from pyflink.datastream.functions import MapFunction
from pyflink.common.watermark_strategy import WatermarkStrategy
from pyflink.datastream.connectors.jdbc import JdbcSink, JdbcConnectionOptions, JdbcExecutionOptions
from pyflink.common import Time
from pyflink.datastream.connectors.elasticsearch import Elasticsearch7SinkBuilder, ElasticsearchEmitter

import json
from datetime import datetime
import os

_conn = None
def get_pg_conn():
    global _conn
    if _conn is None:
        import psycopg2
        db = os.getenv('POSTGRES_DB', 'ecommerce')
        user = os.getenv('POSTGRES_USER', 'user')
        pwd = os.getenv('POSTGRES_PASSWORD', 'password')
        host = os.getenv('POSTGRES_HOST', 'postgres')
        port = int(os.getenv('POSTGRES_PORT', 5432))
        _conn = psycopg2.connect(dbname=db, user=user, password=pwd, host=host, port=port)
        _conn.autocommit = True
    return _conn

def write_to_postgres(record):
    try:
        conn = get_pg_conn()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO sales_summary
            (category, brand, payment_method, total_revenue, window_start, window_end)
            VALUES (%s, %s, %s, %s, NOW(), NOW())
            """,
            (record[0], record[1], record[2], record[3])
        )
        cur.close()
        print(f"[PG] inserted: {record[0]}, {record[3]}")
    except Exception as e:
        print(f"[PG] insert error: {e}")
    return record
class ParseTransaction(MapFunction):
    def map(self, value):
        obj = json.loads(value)
        return (
            obj.get('product_category', 'UNKNOWN'),
            obj.get('product_brand', 'UNKNOWN'),
            obj.get('payment_method', 'UNKNOWN'),
            float(obj.get('total_amount', 0.0)),
            obj.get('transaction_id', None)
        )

def create_es_element(element):
    return {
        "@timestamp": datetime.utcnow().isoformat() + "Z",
        "category": element[0],
        "brand": element[1],
        "payment_method": element[2],
        "total_revenue": element[3],
        "window_start": datetime.utcnow().isoformat() + "Z"
    }


def main():
    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_parallelism(1)

    source = KafkaSource.builder() \
        .set_bootstrap_servers('kafka:9092') \
        .set_topics('transactions') \
        .set_group_id('flink-consumer-group') \
        .set_starting_offsets(KafkaOffsetsInitializer.earliest()) \
        .set_value_only_deserializer(SimpleStringSchema()) \
        .build()

    ds = env.from_source(
        source,
        WatermarkStrategy.no_watermarks(),
        "Kafka Source"
    )

    parsed = ds.map(ParseTransaction(), output_type=Types.TUPLE([
        Types.STRING(), Types.STRING(), Types.STRING(), Types.DOUBLE(), Types.STRING()
    ]))

    windowed = parsed \
        .key_by(lambda x: x[0]) \
        .window(TumblingProcessingTimeWindows.of(Time.minutes(1))) \
        .reduce(lambda a, b: (a[0], a[1], a[2], a[3] + b[3], a[4]))

    type_info = Types.ROW_NAMED(
        ["category", "brand", "payment_method", "total_revenue"],
        [Types.STRING(), Types.STRING(), Types.STRING(), Types.DOUBLE()]
    )

    windowed.add_sink(
        JdbcSink.sink(
            "INSERT INTO sales_summary (category, brand, payment_method, total_revenue, window_start, window_end) VALUES (?, ?, ?, ?, NOW(), NOW())",
            type_info,
            JdbcConnectionOptions.JdbcConnectionOptionsBuilder()
                .with_url("jdbc:postgresql://postgres:5432/ecommerce")
                .with_driver_name("org.postgresql.Driver")
                .with_user_name("user")
                .with_password("password")
                .build(),
            JdbcExecutionOptions.builder()
                .with_batch_interval_ms(200)
                .with_batch_size(1000)
                .with_max_retries(5)
                .build()
        )
    ).name("PostgreSQL Sink")
    

    # Mapeia os dados para o formato esperado pelo Elasticsearch
    def tuple_to_es_dict(record):
        return {
            "@timestamp": datetime.utcnow().isoformat() + "Z",
            "category": record[0],
            "brand": record[1],
            "payment_method": record[2],
            "total_revenue": record[3],
            "window_start": datetime.utcnow().isoformat() + "Z"
        }

    es_stream = windowed.map(
        tuple_to_es_dict,
        output_type=Types.MAP(Types.STRING(), Types.STRING())
    )

    ELASTICSEARCH_SQL_CONNECTOR_PATH = 'file:///lib/flink-sql-connector-elasticsearch7-1.16.0.jar'
    env.add_jars(ELASTICSEARCH_SQL_CONNECTOR_PATH)

    es_sink = Elasticsearch7SinkBuilder() \
        .set_emitter(ElasticsearchEmitter.dynamic_index('category', 'window_start')) \
        .set_hosts(['http://elasticsearch:9200']) \
        .set_bulk_flush_max_actions(1) \
        .set_bulk_flush_max_size_mb(2) \
        .set_bulk_flush_interval(1000) \
        .build()
    
    es_stream.sink_to(es_sink).name('Elasticsearch 7 Sink')
    
    # Funciona mas usa dados estaticos ds de exemplo
    # def write_to_es7_dynamic_index(env):
    #     ELASTICSEARCH_SQL_CONNECTOR_PATH = 'file:///lib/flink-sql-connector-elasticsearch7-3.1.0-1.18.jar'
    #     env.add_jars(ELASTICSEARCH_SQL_CONNECTOR_PATH)

    #     ds = env.from_collection(
    #         [{'name': 'ada', 'id': '1'}, {'name': 'luna', 'id': '2'}],
    #         type_info=Types.MAP(Types.STRING(), Types.STRING()))

    #     es7_sink = Elasticsearch7SinkBuilder() \
    #         .set_emitter(ElasticsearchEmitter.dynamic_index('name', 'id')) \
    #         .set_hosts(['localhost:9200']) \
    #         .build()

    #     ds.sink_to(es7_sink).name('es7 dynamic index sink')

    #     env.execute()

    env.execute()

if __name__ == '__main__':
    main()