from locust import HttpUser, task, between
import random
import uuid

CATEGORIES = ["Electronics", "Books", "Clothing", "Home", "Toys"]
BRANDS = ["Samsung", "Apple", "Nike", "Sony", "Adidas"]
PAYMENT_METHODS = ["Credit Card", "Debit Card", "PayPal", "Pix"]

class EcommerceUser(HttpUser):
    wait_time = between(1, 3)

    @task(5)
    def create_transaction(self):
        product_price = round(random.uniform(10.0, 500.0), 2)
        quantity = random.randint(1, 5)
        transaction = {
            "transaction_id": str(uuid.uuid4()),
            "product_id": random.randint(1000, 9999),
            "product_name": f"Product_{random.randint(1, 100)}",
            "product_category": random.choice(CATEGORIES),
            "product_price": product_price,
            "product_quantity": quantity,
            "product_brand": random.choice(BRANDS),
            "total_amount": product_price * quantity,
            "currency": "BRL",
            "customer_id": random.randint(10000, 99999),
            "transaction_date": "now",
            "payment_method": random.choice(PAYMENT_METHODS)
        }

        self.client.post("/transaction", json=transaction)

    @task(1)
    def health_check(self):
        self.client.get("/health")