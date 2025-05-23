## Product Requirements Document: BharatAgro AI Assistant

**Document Version:** 1.0
**Date:** May 21, 2025
**Prepared For:** Coding Agent / Development Team
**Prepared By:** AI Assistant (Gemini)

---

### 1. Introduction

#### 1.1 Project Overview
The BharatAgro AI Assistant is a multi-vendor farming products platform designed to assist users with product inquiries, vendor information, order management, and general farming advice through a natural language interface. This document outlines the requirements for developing the core AI agent architecture, focusing on a robust, modular, and scalable design using Google's Gemini 2.0 Flash as the central orchestrator and specialized sub-agents for specific tasks.

#### 1.2 Vision
To empower farmers and agricultural product buyers with instant, accurate, and personalized information, facilitating better purchasing decisions and farming practices through an intuitive AI conversational interface.

#### 1.3 Goals
* **Enhance User Experience:** Provide quick and relevant responses to diverse user queries.
* **Improve Operational Efficiency:** Automate information retrieval from structured and unstructured data sources.
* **Scalability:** Design an architecture capable of handling increasing query volumes and data complexity.
* **Maintainability:** Ensure the codebase is clean, modular, and easily updated.
* **Security:** Protect user data and prevent unauthorized access or malicious operations.

#### 1.4 Target Audience
* Farmers seeking agricultural products and advice.
* Buyers looking for specific farming equipment, seeds, fertilizers, etc.
* Existing customers of the BharatAgro platform checking order status or vendor details.

### 2. Core Functionality

The BharatAgro AI Assistant will be able to process natural language queries and provide information related to the following high-level intents:

* **Product Inquiries:** Searching for products, comparing, getting details, filtering.
* **Vendor Information:** Finding vendors, getting contact info, listing products by vendor.
* **Order Management:** Checking order status, tracking shipments, inquiring about returns/refunds.
* **Farming Knowledge:** General agricultural advice, crop information, pest/disease identification.
* **User Account Management:** Retrieving user details, order history.
* **Multi-Vendor Specifics:** Comparing prices across vendors, checking availability.

### 3. Architecture & Agent Workflow

The system will employ a hierarchical agent architecture, with a **Main Agent** orchestrating specialized **Sub-Agents**.

#### 3.1 Main Agent: "Gemini 2.0 Flash Exp" (Orchestrator)

* **Role:** The primary conversational interface. Responsible for understanding user intent, managing conversation flow, delegating tasks to appropriate sub-agents, and synthesizing responses.
* **Technology:** Google Gemini 2.0 Flash (as the underlying LLM for reasoning and orchestration).
* **Key Functions:**
    * **Intent Classification:** Determines the user's primary goal.
    * **Parameter Extraction:** Extracts necessary entities (e.g., product name, vendor ID, query type) from the user's input.
    * **Agent Routing:** Based on intent and extracted parameters, decides which sub-agent(s) to invoke.
    * **Context Management:** Maintains conversational state and history.
    * **Response Synthesis:** Combines information received from sub-agents into a cohesive, natural language response.
    * **Error Handling:** Manages scenarios where sub-agents fail or cannot fulfill a request.

#### 3.2 Sub-Agent 1: Query Executer Agent (Sequential Agent)

* **Role:** Specialized in handling structured data retrieval from the platform's relational database. It is responsible for translating natural language into SQL, executing it securely, and returning structured data.
* **Type:** This agent operates sequentially: Natural Language -> SQL Generation -> SQL Validation -> DB Execution -> JSON Output.
* **Key Functions / Tools:**
    * **`generate_sql_query(user_query: str, db_schema: str, examples: List[Dict]) -> str`**:
        * **Description:** Uses an LLM (e.g., Gemini Pro, as an internal tool within this agent or external API) to generate a SQL query based on the natural language request and the provided database schema.
        * **Method:** LLM Interaction (Prompt Engineering)
        * **Inputs:** `user_query` (natural language request from Main Agent), `db_schema` (textual representation of relevant database schema), `examples` (few-shot examples of NL to SQL pairs).
        * **Output:** SQL query string (e.g., `SELECT * FROM products WHERE category = 'fertilizer';`) or a specific error/fallback string (`NO_QUERY_POSSIBLE`).
        * **Prompts:** Will be defined in `prompts.py` for clarity and maintainability.
    * **`validate_sql_query(sql_query: str) -> bool`**:
        * **Description:** Performs rigorous security validation on the generated SQL query to prevent SQL injection and unauthorized operations.
        * **Method:** Code Logic (SQL parsing library like `sqlglot` or custom regex/keyword checks).
        * **Inputs:** Generated `sql_query` string.
        * **Output:** Boolean indicating if the query is safe for execution.
    * **`execute_database_query(validated_sql_query: str) -> List[Dict]`**:
        * **Description:** Establishes a database connection (via connection pooling), executes the validated SQL query, and fetches the results.
        * **Method:** DB Lookup (using `asyncpg` or SQLAlchemy with an async driver).
        * **Inputs:** Validated `sql_query` string.
        * **Output:** List of dictionaries, where each dictionary represents a row and keys are column names (JSON-ready).
    * **`handle_query_failure(error_details: str) -> str`**:
        * **Description:** Manages errors arising from SQL generation or execution, providing a graceful fallback message.
        * **Method:** Code Logic.
        * **Inputs:** Error details from the preceding steps.
        * **Output:** User-friendly error message for the Main Agent.

#### 3.3 Sub-Agent 2: RAG-based Agent

* **Role:** Specialized in retrieving information from unstructured knowledge bases (e.g., agricultural guides, vendor policy documents) using Retrieval Augmented Generation.


### 4. Data Sources

* **Relational Database (MySQL):**
    * `order_product` table (prod_id, prod_name, prod_web_url, vendor_id, prod_price, shipping, discount, status (Placed, Cancelled, Out For delivery, Accepted), update_date, tracking_url)
    * `order_tracking_status` table (order_id, product_id, status)
    * `appuser_login` table (user_unique_id, fullname, phone, email, create_by (date))
    * `cartdetails` table (prod_id, vendor_id)
* **Unstructured Knowledge Bases (for RAG Agent):**
    * **Agricultural Knowledge Base:** Collection of articles, guides, research papers on farming practices, crop diseases, pest control.
    * **Vendor Documents:** PDFs, web pages, FAQs containing vendor-specific shipping, return, refund policies.
* **External APIs:**
    * **Shipping Provider API:** For real-time shipment tracking. (Use dummy values)



### 6. Non-Functional Requirements

#### 6.1 Performance
* **Response Time:** Target average response time for simple queries: < 3 seconds.
* **Throughput:** Ability to handle X concurrent users (to be defined during prototyping/scaling).
* **Query Executer Agent Latency:** Minimize latency in SQL generation and execution.

#### 6.2 Scalability
* **Horizontal Scaling:** The FastAPI application and its agents should be designed for horizontal scaling on Render.
* **Database Scalability:** Choose a database solution capable of scaling with data and query volume.

#### 6.3 Security
* **Authorization (Internal):** Ensure sub-agents only perform actions authorized by the Main Agent.
* **SQL Injection Prevention:** **CRITICAL**. Robust SQL validation and sanitization within the `Query Executer Agent` before any query execution. Database user with least privileges.
* **Logging:** Secure and comprehensive logging for auditing and debugging.

#### 6.4 Reliability
* **Error Handling:** Graceful degradation and informative error messages for users if an agent fails or data is unavailable.
* **Retry Mechanisms:** Implement retries for external API calls and database connections.
* **Monitoring:** Implement logging and monitoring for agent performance, errors, and resource usage.

#### 6.5 Maintainability
* **Modular Codebase:** Clear separation of concerns between agents, tools, and utilities.
* **Descriptive Prompt Management:** **All prompts for LLMs MUST be externalized into a dedicated `prompts.py` file** (or similar structure). Each prompt should be clearly named and include comments explaining its purpose, inputs, and expected output format.
* **Best Coding Practices:**
    * **PEP 8 Compliance:** Adhere to Python's style guide.
    * **Type Hinting:** Use type hints extensively for improved readability and maintainability.
    * **Docstrings:** Provide clear docstrings for all modules, classes, and functions.
    * **Unit Testing:** Implement unit tests for key components and agent logic.
    * **Readability:** Write clean, self-documenting code.
    * **Error Handling:** Implement `try-except` blocks for all I/O operations and agent interactions.

---