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

"""RAG-based Agent for BharatAgro AI Assistant."""

import logging
from google.adk import Agent
from typing import Dict, Any

from ..prompts import RAG_PROMPT
from ..tools.tools import search_knowledge_base

logger = logging.getLogger(__name__)

# RAG-based Agent
rag_agent = Agent(
    name="rag_agent",
    model="gemini-2.0-flash-exp",
    instruction=RAG_PROMPT,
    tools=[
        search_knowledge_base
    ]
)

def retrieve_information(query: str, knowledge_type: str = "agriculture") -> Dict[str, Any]:
    """
    Retrieve information using the RAG-based Agent.
    
    Args:
        query: The natural language query from the user
        knowledge_type: Type of knowledge to search (agriculture or vendor)
        
    Returns:
        The agent's response with relevant information
    """
    try:
        # Use the search_knowledge_base tool to retrieve relevant information
        response = search_knowledge_base(query, knowledge_type)
        
        if not response.get("success", False):
            return {
                "success": False,
                "message": "I couldn't find any relevant information in our knowledge base. Please try rephrasing your question or providing more specific details."
            }
            
        # Format the retrieved information for presentation
        formatted_response = {
            "success": True,
            "query": query,
            "results": []
        }
        
        for key, item in response.get("data", {}).items():
            formatted_result = {
                "topic": key.replace("_", " ").title(),
                "content": item.get("content", ""),
                "relevance": item.get("relevance", "low")
            }
            
            if knowledge_type == "agriculture":
                formatted_result["category"] = item.get("category", "").replace("_", " ").title()
            elif knowledge_type == "vendor":
                formatted_result["vendor"] = item.get("vendor", "")
                formatted_result["policy_type"] = item.get("type", "").replace("_", " ").title()
                
            formatted_response["results"].append(formatted_result)
            
        # Sort results by relevance
        formatted_response["results"].sort(
            key=lambda x: 0 if x["relevance"] == "high" else (1 if x["relevance"] == "medium" else 2)
        )
            
        return formatted_response
        
    except Exception as e:
        logger.error(f"Error in retrieve_information: {e}")
        return {
            "success": False,
            "message": f"An error occurred while retrieving information: {str(e)}"
        }
