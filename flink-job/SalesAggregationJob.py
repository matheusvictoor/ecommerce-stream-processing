from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.connectors.kafka import KafkaSource, KafkaOffsetsInitializer
from pyflink.common.serialization import SimpleStringSchema
from pyflink.common.typeinfo import Types
from pyflink.datastream.window import TumblingProcessingTimeWindows
from pyflink.datastream.functions import MapFunction
import json
from datetime import datetime

class ParseTransaction(MapFunction):
    def map(self, value):
        obj = json.loads(value)
        return (
            obj['product_category'],
            obj['product_brand'],
            obj['payment_method'],
            float(obj['total_amount']),
            obj['transaction_id']
        )

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

    ds = env.from_source(source, Types.STRING(), "Kafka Source")

    parsed = ds.map(ParseTransaction(), output_type=Types.TUPLE([
        Types.STRING(), Types.STRING(), Types.STRING(), Types.DOUBLE(), Types.STRING()
    ]))

    windowed = parsed \
        .key_by(lambda x: x[0]) \
        .window(TumblingProcessingTimeWindows.of(Time.minutes(1))) \
        .reduce(lambda a, b: (a[0], a[1], a[2], a[3] + b[3], a[4]))
    env.execute("E-commerce Real-Time Sales Aggregation")

if _name_ == '_main_':
    main()
