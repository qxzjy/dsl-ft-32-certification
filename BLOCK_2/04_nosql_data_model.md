# NoSQL Data Model

## Delivrable description
A detailed schema design for the NoSQL system, including strategies for managing unstructured data, relationships, and indexing.

## Task
**NoSQL Data Model :**
- Design a schema that can handle unstructured and semi-structured data.
- Propose strategies for managing relationships between documents, including embedding, referencing, and indexing.
- Ensure that the model supports integration with OLTP and OLAP systems.

## Data source
**Unstructured and Semi-Structured Data (NoSQL) :**

Data collected from various sources, such as logs, customer interactions, and machine-generated data.
- Log Data (error logs, access logs) => Embeding
- User Interaction Data (clickstream data, session data) => Embeding
- Machine Learning Features (input data for models) => Normal
- Customer Feedback + Reviews => Referencing

## Models details
LogData collection (using log_connections, log_disconnections, log_statement from native modules of PostgreSQL)
```json
{
    "_id": ObjectId("23"),
    "query_id": 1,
    "user": "postgres",
    "dbname": "stripe",
    "pid": 18254,
    "remote_host": "[local]",
    "session_id": "64c6e836.474e",
    "session_start": { "$date": "2025-09-08T22:46:21.808Z" },
    "application_name": "psql",
    "lines": [
      {
        "timestamp": { "$date": "2025-09-08T22:49:21.808Z" },
        "error_severity": "LOG",
        "message": "statement: SELECT * FROM CustomerInteractions;"
      },
      {
        "timestamp": { "$date": "2025-09-08T22:49:21.808Z" },
        "error_severity": "ERROR",
        "state_code": "42P01",
        "message": "Table `CustomerInteractions` does not exist",
        "statement": "SELECT * FROM CustomerInteractions;"
      }
    ]
}
```

db.LogData.createIndex( { "user": 1, "dbname": 1, "lines.error_severity": 1 } )

UserInteractionData collection
```json
{
    "_id": ObjectId("13"),
    "session_id": "64cjbz756.93h3",
    "session_start": { "$date": "2025-09-09T14:22:15Z" },
    "device": {
        "type": "tablet",
        "os": "iPadOS",
        "osVersion": "17.1",
        "browser": "Safari",
        "browserVersion": "16.5"
    },
    "location": {
        "ip": "203.0.113.45",
        "country": "France",
        "city": "Lille"
    },
    "events": [
      {
        "eventType": "page_view",
        "pageUrl": "/home",
        "referrer": "stripe.com",
        "timestamp": { "$date": "2025-09-09T14:23:15Z" }
      },
      {
        "eventType": "click",
        "elementId": "signup_button",
        "pageUrl": "/home",
        "timestamp": { "$date": "2025-09-09T14:23:30Z" }
      },
      {
        "eventType": "form_submit",
        "formId": "signup_form",
        "pageUrl": "/login",
        "timestamp": { "$date": "2025-09-09T14:24:02Z" },
        "formFields": {
            "email": "john.doe@stripe.com",
            "rememberMe": 1
        }
      },
      {
        "eventType": "page_view",
        "pageUrl": "/dashboard",
        "timestamp": { "$date": "2025-09-09T14:24:10Z" }
      }
    ],
    "sessionDuration": 75,
    "isActive": false
}
```

db.UserInteractionData.createIndex( { "location.ip": 1 } )

MachineLearningFeature collection
```json
{
    "_id": ObjectId("823"),
    "transaction_id": 012345,
    "transaction_status_id" : 2,
    "merchant_id": 3,
    "amount": 243.87,
    "currency_id": 1,
    "payment_method_id": 3,
    "device_id": 2,
    "customer_email": "john.doe@stripe.com",
    "ip_address": "203.0.113.45",
    "transaction_city": "Lille",
    "transaction_country": "France",
    "billing_city": "Lille",
    "billing_country": "France",
    "timestamp": { "$date": "2025-09-08T22:49:21.808Z" }
}
```

db.MachineLearningFeature.createIndex( { "transaction_id": 1 }, {"unique": 1} )

Customer collection
```json
{
    "_id": ObjectId("12"),
    "userName": "John42",
    "email": "john.doe@stripe.com",
    "fullName": "John Doe",
    "preferences": {"device": "Tablet", "paymentMethod": "Bank Transfer", "currency": "EUR"},
    "lastUpdated": { "$date": "2025-09-04T14:49:21.808Z" }
}
```

db.Customer.createIndex( { "preferences.device": 1, "preferences.paymentMethod": 1, "preferences.currency": 1 } )

CustomerReview collection
```json
{
    "_id": ObjectId("0"),
    "transaction_id": 012345,
    "customer_id" : ObjectId("12"),
    "rating": 4,
    "message": "The product was not what I wanted, but customer service refunded me quickly.",
    "timestamp": { "$date": "2025-09-09T14:49:21.808Z" }
}
```

db.CustomerReview.createIndex( { "customer_id": 1, "rating": 1 } )