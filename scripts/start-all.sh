#!/bin/bash
echo "🚀 Subindo toda a stack..."
docker compose up -d

echo "⏳ Aguardando inicialização (30s)..."
sleep 30

echo "📥 Criando tópico Kafka 'transactions'..."
docker exec -it kafka kafka-topics --create --topic transactions --partitions 3 --replication-factor 1 --bootstrap-server kafka:9092
sleep 2

echo "📤 Submetendo job Flink..."
docker exec -i jobmanager flink run -py /opt/flink/usrlib/SalesAggregationJob.py

echo "✅ Stack pronta! Acesse:"
echo "   Kafka-ui: http://localhost:8080"
echo "   Locust: http://localhost:8089"
echo "   Flink: http://localhost:8081"
echo "   Kibana: http://localhost:5601"