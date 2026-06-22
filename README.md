# Adidas Product Data Scraper

A Python-based data extraction project that collected and structured data from 1,336 Adidas products.

## Overview

This scraper was built to collect detailed product information from Adidas product listings and export the data into a structured CSV dataset for analysis and automation purposes.

The final dataset contains 1,336 products and 30+ attributes per product.

## Data Collected

Examples of extracted fields include:

- Product ID
- Product Name
- Brand
- Category
- Product Type
- Gender
- Sport
- Color
- Current Price
- Original Price
- Sale Price
- Discount
- Sizes Available
- Material
- Product Description
- Image URL
- Product URL
- Model Number
- Scrape Timestamp

## Output

- 1,336 Adidas products collected
- 30+ structured attributes per product
- CSV export for further analysis

## Dataset Statistics

- Total Products Collected: 1,336
- Total Attributes: 30+
- Export Format: CSV

## Sample Dataset Preview

See the screenshots folder for examples of the collected dataset and scraper execution.

## Technologies Used

- Python
- Requests
- JSON Processing
- CSV
- Data Cleaning

## Repository Structure

```text
adidas-product-data-scraper/
│
├── adidas_scraper.py
├── adidas_products.csv
├── requirements.txt
├── README.md
└── screenshots/
    ├── dataset_preview.png
    └── scraper_execution.png
```

## Sample Use Cases

- E-commerce analysis
- Product catalog research
- Pricing analysis
- Inventory monitoring
- Competitive intelligence

## How To Run

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Run the scraper:

```bash
python adidas_scraper.py
```

3. Output will be saved as:

```text
adidas_products.csv
```

## Author

Shameer Shahid

Computer Science Student focused on Web Scraping, Data Extraction, Automation, and API-Based Data Collection.
