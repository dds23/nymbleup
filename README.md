# Retail Store Transaction System

This project is a transaction system for a retail store, developed using FastAPI and PostgreSQL.

## Features

## Features

- **Fetch Item Details**: Retrieve details of all items available in the store.
- **Add Sales**: Add sales records with corresponding item codes, prices, and quantities.
- **Sales Summary**: Fetch consolidated sales figures for a business day.
- **Average Sales**: Return average sales data over a selected date range.
- **Sales Report**: Generate and download CSV reports for sales data over a selected date range.
- **Trend Analysis**: Identify item sales trends over time.
- **Sales Comparison**: Compare sales data between two different date ranges.
- **Populate Dummy Data**: Populate the database with dummy data for testing purposes.
- **List Cached Results**: Retrieve all cached results from Redis.

## Setup

### Prerequisites

- Python 3.10
- PostgreSQL
- Redis

### Installation

1. Clone the repository:

```bash
git clone https://github.com/dds23/nymbleup.git
cd nymbleup
```

2. Create a virtual environment and activate it:
   ```bash
   python3 -m venv my_env
   source my_env/bin/activate
   ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

### Database Setup

1. Create a `.env` file in the root directory of the project and add your database connection URL:
   ```
   DB_URL=postgresql://username:password@localhost/dbname
   ```

### Running the Project

1. Start the FastAPI server:
   ```bash
   uvicorn main:app --reload
   ```

2. Populate dummy data:
   
   Run the `/add-items` endpoint to populate the dummy data.

3. The API will be available at `http://localhost:8000` and the documentation will be available at `http://localhost:8000/docs`

### Testing

For testing, first ensure that the server is closed and then run the command
```bash
pytest
```


## API Endpoints

### Fetch Item Details
`GET /items`

Fetch details of all items available in the store.

### Add Sales
`POST /sales`

Add sales records with corresponding item codes, prices, and quantities.

### Fetch Sales Summary
`GET /sales-summary?date=2024-08-01`

Fetch consolidated sales figures for the business day.

### Fetch Average Sales
`GET /average-sales?start_date=2024-08-01&end_date=2024-08-31`

Fetch average sales data over a selected date range.

### Generate Sales Report
`GET /sales-report?start_date=2024-08-01&end_date=2024-08-31`

Generate and download CSV reports for sales data over a selected date range.

### Trend Analysis
`GET /trend-analysis?start_date=2024-08-01&end_date=2024-08-31`

Identify item sales trends over time.

### Sales Comparison
`GET /sales-comparison?start_date_1=2024-08-01&end_date_1=2024-08-15&start_date_2=2024-08-16&end_date_2=2024-08-31`

Compare sales data between two different date ranges.