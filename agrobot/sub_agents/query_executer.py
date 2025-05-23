# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Query Executer Agent for BharatAgro AI Assistant."""

import logging
import re
from google.adk import Agent
from google.adk.agents import SequentialAgent
from google.adk.tools.agent_tool import AgentTool
from typing import Dict, Any

from ..prompts import SQL_GENERATION_PROMPT, SQL_EXECUTION_PROMPT
from ..tools.tools import (
    query_executer
)

logger = logging.getLogger(__name__)

generated_query = "query"

# SQL Query Executer Agent
query_writer_agent = Agent(
    name="query_writer_agent",
    model="gemini-2.0-flash",
    instruction=SQL_GENERATION_PROMPT,
    description="Writes initial SQL query based on a specification.",
    # output_schema=QueryOutput,
    output_key= "generated_query" 
)
query_executer_agent = Agent(
    name="query_executer_agent",
    model="gemini-2.0-flash-exp",
    instruction=SQL_GENERATION_PROMPT,
    description="Writes and Executes the SQL query.",
    tools=[
        query_executer
    ],
    # output_schema=QueryOutput,
    output_key= "result" 
)

# query_pipeline_agent = SequentialAgent(
#     name="QueryPipelineAgent",
#     sub_agents=[query_writer_agent, query_executer_agent],
#     description="Executes a sequence of query writing and executing."
#     # The agents will run in the order provided: Writer -> Validater -> Executer
# )

# def execute_query(query: str) -> Dict[str, Any]:
#     """
#     Execute a query using the Query Pipeline Agent.
    
#     This function uses the SequentialAgent to process a natural language query
#     through a pipeline of steps: SQL generation, validation, and execution.
    
#     Args:
#         query: The natural language query from the user
        
#     Returns:
#         The results from the database or error message
#     """
#     try:
#         # Use the sequential pipeline agent to process the query
#         logger.info(f"Processing query through sequential pipeline: {query}")
        
#         # For direct execution using the pipeline
#         response = query_pipeline_agent.execute(input=query)
#         return response
        
#     except Exception as e:
#         logger.error(f"Error in sequential query pipeline: {e}")
        
#         # Fallback to direct approach with specific tools if the pipeline fails
#         logger.info(f"Pipeline failed, attempting direct tool approach with query: {query}")
        
#         # Check for specific intents in the query
#         query_lower = query.lower()
        
#         if "track" in query_lower and "order" in query_lower:
#             # Extract order ID if present and call the track_order tool
#             order_id_match = re.search(r'order[:\s]+(\w+[-]?\w+)', query_lower)
#             if order_id_match:
#                 order_id = order_id_match.group(1)
#                 return track_order(order_id)
        
#         elif "product" in query_lower and ("details" in query_lower or "information" in query_lower):
#             # Extract product name if present and call the get_product_details tool
#             product_match = re.search(r'product[:\s]+(\w+)', query_lower)
#             if product_match:
#                 product_name = product_match.group(1)
#                 return get_product_details(product_name=product_name)
        
#         # If all fails, return a generic error
#         return {
#             "success": False,
#             "message": f"An error occurred while processing your query: {str(e)}"
#         }
