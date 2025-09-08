# Schema Design for OLAP System

## Delivrable description
A detailed schema design for the OLAP system, including star or snowflake schemas, aggregation strategies, and query optimization techniques.

## Task
**OLAP Data Model :**
- Design a star or snowflake schema that supports complex queries and aggregations. => OK
- Propose a strategy for handling large-scale joins, subqueries, and time-series analysis. => OK (Dimensions)
- Include a plan for pre-aggregations, materialized views, or summary tables to optimize query performance. => OK (Pre-aggregations directly on FACT tables)

## Data source
**Analytical Data (OLAP) :**

Aggregated and historical data used for reporting and analysis.
- Revenue Metrics (daily, weekly, monthly)
- Customer Segmentation Data
- Product Performance Metrics
- Fraud Analysis Data
- Compliance and Audit Logs

## Star schemas
![olap_fact_revenue](img/olap_fact_revenue.png)
![olap_fact_customer_segmentation](img/olap_fact_customer_segmentation.png)
![olap_fact_product_performance](img/olap_fact_product_performance.png)
![olap_fact_fraud_analysis](img/olap_fact_fraud_analysis.png)
![olap_fact_compliance_audit](img/olap_fact_compliance_audit.png)