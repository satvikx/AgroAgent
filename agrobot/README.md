# BharatAgro AI Assistant

A multi-vendor farming products platform chatbot that assists users with product inquiries, vendor information, order management, and general farming advice through a natural language interface.

## Overview

The BharatAgro AI Assistant is built using Google's Agent Development Kit (ADK) and employs a hierarchical agent architecture with a Main Agent (Gemini 2.0 Flash) orchestrating specialized Sub-Agents for handling different types of queries:

1. **Main Agent (Orchestrator):** Primary conversational interface responsible for understanding user intent, managing conversation flow, and delegating tasks.
2. **Query Executer Agent:** Specialized in handling structured data retrieval from the platform's relational database.
3. **RAG-based Agent:** Specialized in retrieving information from unstructured knowledge bases (agricultural guides, vendor policy documents).

## Features

- **Product Inquiries:** Search for products, compare options, get details, filter results.
- **Vendor Information:** Find vendors, get contact info, list products by vendor.
- **Order Management:** Check order status, track shipments, inquire about returns/refunds.
- **Farming Knowledge:** Get general agricultural advice, crop information, pest/disease identification.
- **User Account Management:** Retrieve user details and order history.
- **Multi-Vendor Specifics:** Compare prices across vendors, check availability.

## Project Structure

```
agrobot/
├── __init__.py            # Package initialization
├── agent.py               # Main agent implementation
├── config.py              # Configuration settings
├── integration.py         # FastAPI integration utilities
├── prompts.py             # Prompts for the agents
├── requirements.txt       # Project dependencies
├── agents/                # Sub-agents implementation
│   ├── __init__.py
│   ├── query_executer.py  # SQL query execution agent
│   └── rag_agent.py       # RAG-based agent for knowledge retrieval
├── entities/              # Entity classes
│   └── __init__.py
├── shared_libraries/      # Shared utility functions
│   ├── __init__.py
│   └── callbacks.py       # ADK callback functions
└── tools/                 # Agent tools
    ├── __init__.py
    ├── db.py              # Database connectivity
    └── tools.py           # Tool implementations
```

## Setup Instructions

### Prerequisites

- Python 3.10 or higher
- MySQL/MariaDB database
- Google API Key for Gemini AI

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/BAgro_Chatbot.git
   cd BAgro_Chatbot
   ```

2. Install the required packages:
   ```bash
   pip install -r agrobot/requirements.txt
   ```

3. Create a `.env` file in the project root with the following variables:
   ```
   GOOGLE_API_KEY=your_google_api_key
   
   # Database Configuration
   DB_HOST=localhost
   DB_USER=your_database_user
   DB_PASSWORD=your_database_password
   DB_NAME=bharatagro
   DB_PORT=3306
   ```

4. Create the database and required tables:
   ```sql
   CREATE DATABASE bharatagro;
   
   USE bharatagro;
   
   CREATE TABLE order_product (
     prod_id VARCHAR(50) PRIMARY KEY,
     prod_name VARCHAR(255) NOT NULL,
     prod_web_url VARCHAR(255),
     vendor_id VARCHAR(50),
     prod_price DECIMAL(10, 2),
     shipping DECIMAL(10, 2),
     discount DECIMAL(10, 2),
     status ENUM('Placed', 'Cancelled', 'Out For delivery', 'Accepted'),
     update_date DATETIME,
     tracking_url VARCHAR(255)
   );
   
   CREATE TABLE order_tracking_status (
     order_id VARCHAR(50),
     product_id VARCHAR(50),
     status VARCHAR(50),
     PRIMARY KEY (order_id, product_id)
   );
   
   CREATE TABLE appuser_login (
     user_unique_id VARCHAR(50) PRIMARY KEY,
     fullname VARCHAR(255),
     phone VARCHAR(20),
     email VARCHAR(255),
     create_by DATETIME
   );
   
   CREATE TABLE cartdetails (
     prod_id VARCHAR(50),
     vendor_id VARCHAR(50),
     PRIMARY KEY (prod_id, vendor_id)
   );
   ```

### Running the Application

1. Start the FastAPI server:
   ```bash
   cd fastapi_server
   uvicorn main:app --reload
   ```

2. Access the chat interface at http://localhost:8000

## Usage Examples

Here are some example queries that the BharatAgro AI Assistant can handle:

- "What's the status of my order ORD-12345?"
- "I'm looking for organic fertilizers for tomato plants"
- "Tell me about the shipping policy for vendor V001"
- "How do I treat powdery mildew on my crops?"
- "Compare the prices of products P123 and P456"
- "What are the best practices for crop rotation?"

## Development

### Adding New Tools

1. Add the tool implementation in `tools/tools.py`
2. Register the tool with the appropriate agent in `agents/` or `agent.py`

### Modifying Prompts

Update the prompts in `prompts.py` to adjust agent behavior and capabilities.

### Adding New Data Sources

1. Update the `db.py` file to include new database tables or external APIs
2. Create new tool functions that interact with these data sources
3. Register the tools with the appropriate agents

## License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.
