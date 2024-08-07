from faker import Faker
import random
from sqlalchemy.orm import Session
from models import Item, Transaction, BillItem

def populate_dummy_data(db: Session):
    fake = Faker()
    categories = ['Burger', 'Pizza', 'Drink', 'Side']
    items = []

    for _ in range(20):
        item = Item(
            name=fake.word(),
            item_code=fake.unique.ean8(),
            price=round(random.uniform(5, 20), 2),
            category=random.choice(categories),
            starting_quantity=random.randint(100, 500)
        )
        items.append(item)
    db.add_all(items)
    db.commit()

    transactions = []

    for _ in range(50):
        transaction = Transaction()
        db.add(transaction)
        db.commit()

        for _ in range(random.randint(1, 5)):
            bill_item = BillItem(
                transaction_id=transaction.id,
                item_id=random.choice(items).id,
                unit_price=random.choice(items).price,
                quantity=random.randint(1, 5)
            )
            db.add(bill_item)
        transactions.append(transaction)
    db.commit()
