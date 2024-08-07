from fastapi.responses import StreamingResponse
import csv
from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from sqlalchemy import func
from datetime import datetime, date
from models import Item, Transaction, BillItem
from schemas import BillItemCreate, SalesResponse
from database import get_db, Base, engine
from fastapi.openapi.utils import get_openapi
import io
from cache import get_redis
import json
from aioredis import Redis
from populate_dummy_data import populate_dummy_data


app = FastAPI()

Base.metadata.create_all(bind=engine)


@app.post("/add-items")
async def add_items(db: Session = Depends(get_db), redis: Redis = Depends(get_redis)):
    """
    Populate the database with dummy data for testing purposes.
    """
    populate_dummy_data(db)
    keys = await redis.keys('*')
    for key in keys:
        redis.delete(key)

    return {"message": "Dummy data populated successfully"}


@app.get("/items")
async def fetch_item_details(db: Session = Depends(get_db), redis: Redis = Depends(get_redis)):
    """
    Fetch details of all items available in the store.
    """
    cache_key = "items"
    cached_items = await redis.get(cache_key)
    if cached_items:
        print('got cached res')
        return json.loads(cached_items)

    items = db.query(Item).all()
    items_data = [item.__dict__ for item in items]
    for item in items_data:
        item.pop('_sa_instance_state', None)

    # Cache for 1 hour
    await redis.set(cache_key, json.dumps(items_data), ex=3600)
    return items_data


@app.post("/sales", response_model=SalesResponse)
async def add_sales(sales: List[BillItemCreate], db: Session = Depends(get_db), redis: Redis = Depends(get_redis)):
    """
    Add sales records with corresponding item codes, prices, and quantities.
    System-generated fields like date and timestamp are automated.
    """
    transaction = Transaction()
    db.add(transaction)
    db.commit()

    for sale in sales:
        item = db.query(Item).filter(Item.item_code == sale.item_code).first()
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        bill_item = BillItem(
            transaction_id=transaction.id,
            item_id=item.id,
            unit_price=item.price,
            quantity=sale.quantity
        )
        db.add(bill_item)
    db.commit()

    # Invalidate the cache for items since quantities have changed
    await redis.delete("items")

    return {"message": "Sales added successfully"}


@app.get("/sales-summary")
async def fetch_sales_summary(date: datetime = Query(..., example='2024-07-31'), db: Session = Depends(get_db), redis: Redis = Depends(get_redis)):
    """
    Fetch consolidated sales figures for the business day, including total quantity
    sold for each item, each item category, and the total sales amount.
    """
    cache_key = f"sales_summary_{date}"
    cached_summary = await redis.get(cache_key)
    if cached_summary:
        return json.loads(cached_summary)

    transactions = db.query(Transaction).filter(
        func.date(Transaction.business_day_date) == date).all()
    summary = {}
    for transaction in transactions:
        for bill_item in transaction.bill_items:
            item = bill_item.item
            if item.name not in summary:
                summary[item.name] = {
                    "total_quantity": 0,
                    "category": item.category,
                    "total_sales_amount": 0
                }
            summary[item.name]["total_quantity"] += bill_item.quantity
            summary[item.name]["total_sales_amount"] += bill_item.total_price
    
    for _, item in summary.items():
        item['total_sales_amount'] = round(item['total_sales_amount'], 2)
    
    total_sales = round(sum(item["total_sales_amount"] for item in summary.values()), 2)
    result = {"summary": summary, "total_sales": total_sales}

    await redis.set(cache_key, json.dumps(result), ex=3600)  # Cache for 1 hour
    return result


@app.get("/average-sales")
async def fetch_average_sales(start_date: date = Query(..., example='2024-07-29'), end_date: date = Query(..., example='2024-07-31'), db: Session = Depends(get_db), redis: Redis = Depends(get_redis)):
    """
    Fetch average sales data over a selected date range.
    """

    cache_key = f"average_sales_{start_date}_{end_date}"
    cached_average_sales = await redis.get(cache_key)
    if cached_average_sales:
        return json.loads(cached_average_sales)

    transactions = db.query(Transaction).filter(
        Transaction.business_day_date.between(start_date, end_date)).all()
    transactions_count = len(transactions)
    if transactions_count == 0:
        raise HTTPException(status_code=404, detail="No transactions found")
    summary = {}
    for transaction in transactions:
        for bill_item in transaction.bill_items:
            item = bill_item.item
            if item.name not in summary:
                summary[item.name] = {
                    "total_quantity": 0,
                    "total_sales_amount": 0
                }
            summary[item.name]["total_quantity"] += bill_item.quantity
            summary[item.name]["total_sales_amount"] += bill_item.total_price
    total_sales = sum(item["total_sales_amount"] for item in summary.values())
    average_sales = round(total_sales / transactions_count, 2)
    result = {"average_sales": average_sales}

    await redis.set(cache_key, json.dumps(result), ex=3600)  # Cache for 1 hour
    return result


@app.get("/sales-report")
async def generate_sales_report(start_date: date = Query(..., example='2024-07-29'), end_date: date = Query(..., example='2024-07-31'), db: Session = Depends(get_db), redis: Redis = Depends(get_redis)):
    """
    Generate and download CSV reports for sales data over a selected date range.
    The report includes total sales, average sales, and item-wise sales data.
    """
    cache_key = f"sales_report_{start_date}_{end_date}"
    cached_report = await redis.get(cache_key)
    if cached_report:
        output = io.StringIO(cached_report)
        headers = {
            'Content-Disposition': 'attachment; filename="sales_report.csv"'
        }
        return StreamingResponse(output, media_type="text/csv", headers=headers)

    transactions = db.query(Transaction).filter(
        Transaction.business_day_date.between(start_date, end_date)).all()
    summary = {}
    for transaction in transactions:
        for bill_item in transaction.bill_items:
            item = bill_item.item
            if item.name not in summary:
                summary[item.name] = {
                    "total_quantity": 0,
                    "category": item.category,
                    "total_sales_amount": 0
                }
            summary[item.name]["total_quantity"] += bill_item.quantity
            summary[item.name]["total_sales_amount"] += bill_item.total_price

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
                            'Item Name', 'Category', 'Total Quantity Sold', 'Total Sales Amount'])
    writer.writeheader()
    for item_name, data in summary.items():
        writer.writerow({
            'Item Name': item_name,
            'Category': data['category'],
            'Total Quantity Sold': data['total_quantity'],
            'Total Sales Amount': round(data['total_sales_amount'], 2)
        })

    output.seek(0)
    await redis.set(cache_key, output.getvalue(), ex=3600)  # Cache for 1 hour

    headers = {
        'Content-Disposition': 'attachment; filename="sales_report.csv"'
    }
    return StreamingResponse(output, media_type="text/csv", headers=headers)


@app.get("/trend-analysis")
async def trend_analysis(start_date: date = Query(..., example='2024-07-29'), end_date: date = Query(..., example='2024-07-31'), db: Session = Depends(get_db), redis: Redis = Depends(get_redis)):
    """
    Identify item sales trends over time. Analyze which items/categories are gaining or losing popularity
    using statistical methods.
    """
    cache_key = f"trend_analysis_{start_date}_{end_date}"
    cached_trend_data = await redis.get(cache_key)
    if cached_trend_data:
        return json.loads(cached_trend_data)

    transactions = db.query(Transaction).filter(
        Transaction.business_day_date.between(start_date, end_date)).all()
    trend_data = {}
    for transaction in transactions:
        for bill_item in transaction.bill_items:
            item = bill_item.item
            if item.name not in trend_data:
                trend_data[item.name] = {"quantity": [], "dates": []}
            trend_data[item.name]["quantity"].append(bill_item.quantity)
            trend_data[item.name]["dates"].append(
                transaction.business_day_date.isoformat())
    
    # Cache for 1 hour
    await redis.set(cache_key, json.dumps(trend_data), ex=3600)

    # Further analysis to identify trends can be added here.
    return trend_data


@app.get("/sales-comparison")
async def sales_comparison(start_date_1: date = Query(..., example='2024-07-29'), end_date_1: date = Query(..., example='2024-07-29'), start_date_2: date = Query(..., example='2024-08-02'), end_date_2: date = Query(..., example='2024-08-04'), db: Session = Depends(get_db), redis: Redis = Depends(get_redis)):
    """
    Compare sales data between two different date ranges and generate a statistical summary.
    """
    cache_key = f"sales_comparison_{start_date_1}_{end_date_1}_{start_date_2}_{end_date_2}"
    cached_comparison = await redis.get(cache_key)
    if cached_comparison:
        return json.loads(cached_comparison)

    transactions_1 = db.query(Transaction).filter(
        Transaction.business_day_date.between(start_date_1, end_date_1)).all()
    transactions_2 = db.query(Transaction).filter(
        Transaction.business_day_date.between(start_date_2, end_date_2)).all()

    def summarize(transactions):
        summary = {}
        for transaction in transactions:
            for bill_item in transaction.bill_items:
                item = bill_item.item
                if item.name not in summary:
                    summary[item.name] = {
                        "total_quantity": 0,
                        "category": item.category,
                        "total_sales_amount": 0
                    }
                summary[item.name]["total_quantity"] += bill_item.quantity
                summary[item.name]["total_sales_amount"] += bill_item.total_price

        for _, item in summary.items():
            item['total_sales_amount'] = round(item['total_sales_amount'], 2)

        return summary

    summary_1 = summarize(transactions_1)
    summary_2 = summarize(transactions_2)
    comparison = {"period_1": summary_1, "period_2": summary_2}

    await redis.set(cache_key, json.dumps(comparison), ex=3600)
    return comparison


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Retail Store Transaction System API",
        version="1.0.0",
        description="API documentation for the Retail Store Transaction System",
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
