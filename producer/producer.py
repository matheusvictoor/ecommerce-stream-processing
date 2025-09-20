from flask import Flask, request, jsonify
from kafka import KafkaProducer
import json
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

producer = KafkaProducer(
    bootstrap_servers='kafka:9092',
    value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8')
)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "OK"}), 200

@app.route('/transaction', methods=['POST'])
def receive_transaction():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON received"}), 400

        data['transaction_date'] = datetime.utcnow().isoformat() + "Z"

        producer.send('transactions', value=data)
        producer.flush()

        logger.info(f"Transaction sent to Kafka: {data['transaction_id']}")
        return jsonify({"status": "sent to kafka", "transaction_id": data["transaction_id"]}), 200

    except Exception as e:
        logger.error(f"Error processing transaction: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)