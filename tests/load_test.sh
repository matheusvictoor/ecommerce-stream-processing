#!/bin/bash
echo "🚀 Iniciando teste de carga automatizado..."

# Espera serviços estarem prontos
# sleep 30

echo "✅ Enviando requisições de teste..."
for i in {1..10}; do
    curl -X POST http://localhost:5000/transaction \
         -H "Content-Type: application/json" \
         -d '{
           "transaction_id": "test-'$i'",
           "product_id": 9999,
           "product_name": "Test Product",
           "product_category": "Test",
           "product_price": 99.99,
           "product_quantity": 1,
           "product_brand": "TestBrand",
           "total_amount": 99.99,
           "currency": "BRL",
           "customer_id": 88888,
           "transaction_date": "now",
           "payment_method": "Credit Card"
         }'
    sleep 0.5
done

echo "✅ Teste de carga concluído."