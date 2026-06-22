# Rental-Market-Intelligence

## Purpose
This project builds an end-to-end data platform to analyze long-term rental markets and evaluate the influence of short-term rentals (Airbnb) on housing prices and supply.

The system collects large-scale housing data through web scraping and public datasets, processes the data using a modern data pipeline (Parquet + DuckDB), and performs statistical analysis and machine learning to uncover market insights.

Key goals include:

- Estimating fair market rent for listings
- Detecting undervalued rental opportunities
- Measuring the impact of Airbnb density on long-term rents
- Providing interactive dashboards for market analysis

---

## Project Overview

## Research Questions

## Logic
Rent cleaning logic:

1. If rent_min = 1 and rent_max is valid:
   Treat rent_min as a placeholder.
   Use rent_max as the usable rent value.

2. If rent_min = 1 and rent_max is NULL:
   No usable rent value.

3. If rent_min and rent_max are both normal values:
   Keep both and calculate rent_avg.

4. If rent_min or rent_max is greater than 20000:
   Do not remove or modify it in staging.
   Keep it as-is because it may be a real luxury listing.

5. If rent_min > rent_max:
   Flag it as an invalid rent range.

## Project Structure

## Data Sources

## Methodology

## Project Status
Phase 1 - Data Ingestion finished
Current learning PostgreSQL, expect delays in development

## Future Improvements

## Contributing

## Contact
The author is Christopher(Yizhou) Jiang, if you have any questions, feel free to contact via email: christjiang1492@gmail.com
