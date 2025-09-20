from flask import Flask, request, jsonify
from kafka import KafkaProducer
import json
from datetime import datetime

app = Flask(__name__)

producer = KafkaProducer(
    bootstrap_servers='kafka:9092',
    value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8')
)

@app.route('/transaction', methods=['POST'])
def receive_transaction():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON received"}), 400

        data['transaction_date'] = datetime.utcnow().isoformat() + "Z"

        producer.send('transactions', value=data)
        producer.flush()


    except Exception as e:
        return jsonify({"error": str(e)}), 500
