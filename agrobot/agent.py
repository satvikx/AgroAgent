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

"""Agent module for the BharatAgro AI Assistant."""

import logging
import warnings
from typing import Dict, Any, List
from google.adk import Agent
# from google.adk.tools import ToolContext, tool

from .config import Config
from .prompts import GLOBAL_INSTRUCTION, INSTRUCTION
from .shared_libraries.callbacks import (
    rate_limit_callback,
    before_agent,
    before_tool,
    after_tool
)
from .sub_agents.query_executer import query_executer_agent
# from .sub_agents.rag_agent import retrieve_information
# from .tools.tools import (
#     track_order,
#     get_product_details,
#     get_vendor_products,
#     get_user_info,
#     get_user_orders,
#     compare_products
# )

warnings.filterwarnings("ignore", category=UserWarning, module=".*pydantic.*")

configs = Config()

# Configure logging
logger = logging.getLogger(__name__)


# @tool("execute_structured_query")
# def execute_structured_query(query: str) -> Dict[str, Any]:
#     """
#     Execute a structured data query using the specialized Query Executer Agent.
    
#     This tool is used for handling structured data retrieval from the platform's
#     relational database, including product information, order tracking, user data,
#     and vendor details.
    
#     Args:
#         query: Natural language query describing the information needed from the database.
        
#     Returns:
#         A dictionary containing the query results or an error message.
        
#     Example:
#         >>> execute_structured_query("What's the shipping status of order ORD-12345?")
#         {
#             "success": True,
#             "order_id": "ORD-12345",
#             "products": [
#                 {"product_id": "P123", "status": "Shipped", "tracking_url": "..."}
#             ]
#         }
#     """
#     return execute_query(query)


# @tool("retrieve_farming_knowledge")
# def retrieve_farming_knowledge(query: str) -> Dict[str, Any]:
#     """
#     Retrieve farming-related information using the specialized RAG-based Agent.
    
#     This tool provides information about agricultural practices, crop diseases,
#     pest control, and farming tips based on the user's query.
    
#     Args:
#         query: Natural language query asking for agricultural information.
        
#     Returns:
#         A dictionary containing relevant farming knowledge or an error message.
        
#     Example:
#         >>> retrieve_farming_knowledge("How do I treat powdery mildew on my crops?")
#         {
#             "success": True,
#             "query": "How do I treat powdery mildew on my crops?",
#             "results": [
#                 {
#                     "topic": "Powdery Mildew",
#                     "content": "Powdery mildew appears as white powdery spots on leaves and stems...",
#                     "category": "Crop Diseases",
#                     "relevance": "high"
#                 }
#             ]
#         }
#     """
#     return retrieve_information(query, knowledge_type="agriculture")


# @tool("retrieve_vendor_policies")
# def retrieve_vendor_policies(query: str) -> Dict[str, Any]:
#     """
#     Retrieve vendor-specific policies and information using the specialized RAG-based Agent.
    
#     This tool provides information about shipping policies, return policies, payment options,
#     and other vendor-specific details based on the user's query.
    
#     Args:
#         query: Natural language query asking for vendor policy information.
        
#     Returns:
#         A dictionary containing relevant vendor policies or an error message.
        
#     Example:
#         >>> retrieve_vendor_policies("What is the return policy for vendor V001?")
#         {
#             "success": True,
#             "query": "What is the return policy for vendor V001?",
#             "results": [
#                 {
#                     "topic": "V001 Returns",
#                     "content": "Returns accepted within 7 days of delivery for unopened products...",
#                     "vendor": "V001",
#                     "policy_type": "Returns",
#                     "relevance": "high"
#                 }
#             ]
#         }
#     """
#     return retrieve_information(query, knowledge_type="vendor")


# Create the main agent
root_agent = Agent(
    model=configs.agent_settings.model,
    global_instruction=GLOBAL_INSTRUCTION,
    instruction=INSTRUCTION,
    name=configs.agent_settings.name,
    # tools=[
    #     # Orchestration tools that use sub-agents
    #     execute_structured_query,
    #     retrieve_farming_knowledge,
    #     retrieve_vendor_policies,
    # ],
    sub_agents=[query_executer_agent],
    before_tool_callback=before_tool,
    after_tool_callback=after_tool,
    before_agent_callback=before_agent,
    before_model_callback=rate_limit_callback,
)
