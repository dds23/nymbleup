from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Transaction(Base):
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_day_date = Column(Date, nullable=False, default=datetime.now().date(), index=True)
    transaction_timestamp = Column(DateTime, nullable=False, default=datetime.now, index=True)

    bill_items = relationship('BillItem', back_populates='transaction')


class BillItem(Base):
    __tablename__ = 'bill_items'

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(Integer, ForeignKey('transactions.id'))
    item_id = Column(Integer, ForeignKey('items.id'))
    unit_price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)

    transaction = relationship('Transaction', back_populates='bill_items')
    item = relationship('Item')

    @property
    def total_price(self):
        return self.unit_price * self.quantity


class Item(Base):
    __tablename__ = 'items'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    item_code = Column(String, unique=True, nullable=False, index = False)
    price = Column(Float, nullable=False)
    category = Column(String, nullable=False)
    starting_quantity = Column(Integer, nullable=False)

    @property
    def remaining_quantity(self):
        total_sold = sum(bill_item.quantity for bill_item in self.bill_items)
        return self.starting_quantity - total_sold
