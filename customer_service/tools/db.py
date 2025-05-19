"""
Database connection module for MySQL/phpMyAdmin.

This module handles database connections and provides utility functions
for querying the database used by the BAgro Chatbot application.
"""

import mysql.connector
from mysql.connector import Error
from typing import Dict, List, Optional, Any, Tuple
import logging
from contextlib import contextmanager
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Database configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "bagro"),
    "port": int(os.getenv("DB_PORT", "3306"))
}


@contextmanager
def get_connection():
    """
    Context manager for database connections.
    
    Creates and yields a new connection which is automatically closed when done.
    
    Yields:
        mysql.connector.connection.MySQLConnection: Database connection
    
    Raises:
        Error: If connection fails
    """
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        logger.debug("Database connection established")
        yield connection
    except Error as e:
        logger.error(f"Error connecting to MySQL: {e}")
        raise
    finally:
        if connection and connection.is_connected():
            connection.close()
            logger.debug("Database connection closed")


def execute_query(query: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
    """
    Execute a query and return the results.
    
    Args:
        query: SQL query string
        params: Optional tuple of parameters to substitute into query
        
    Returns:
        List of dictionaries representing rows of data
        
    Raises:
        Error: If query execution fails
    """
    with get_connection() as connection:
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(query, params or ())
            result = cursor.fetchall()
            return result
        except Error as e:
            logger.error(f"Error executing query: {e}")
            logger.debug(f"Query: {query}")
            logger.debug(f"Params: {params}")
            raise
        finally:
            cursor.close()


def execute_update(query: str, params: Optional[Tuple] = None) -> int:
    """
    Execute an INSERT, UPDATE, or DELETE query.
    
    Args:
        query: SQL query string
        params: Optional tuple of parameters to substitute into query
        
    Returns:
        Number of affected rows
        
    Raises:
        Error: If query execution fails
    """
    with get_connection() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(query, params or ())
            connection.commit()
            return cursor.rowcount
        except Error as e:
            connection.rollback()
            logger.error(f"Error executing update: {e}")
            logger.debug(f"Query: {query}")
            logger.debug(f"Params: {params}")
            raise
        finally:
            cursor.close()


# Customer-specific database functions
def get_customer_by_id(customer_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a customer by their ID.
    
    Args:
        customer_id: The unique ID of the customer
    
    Returns:
        Customer data as a dictionary or None if not found
    """
    query = "SELECT * FROM customers WHERE customer_id = %s"
    params = (customer_id,)
    results = execute_query(query, params)
    return results[0] if results else None


def get_customer_purchases(customer_id: str) -> List[Dict[str, Any]]:
    """
    Retrieve a customer's purchase history.
    
    Args:
        customer_id: The unique ID of the customer
    
    Returns:
        List of purchase records
    """
    query = """
    SELECT p.*, pi.product_id, pi.quantity, pr.name
    FROM purchases p
    JOIN purchase_items pi ON p.purchase_id = pi.purchase_id
    JOIN products pr ON pi.product_id = pr.product_id
    WHERE p.customer_id = %s
    ORDER BY p.date DESC
    """
    params = (customer_id,)
    return execute_query(query, params)


def get_customer_address(customer_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a customer's billing address.
    
    Args:
        customer_id: The unique ID of the customer
    
    Returns:
        Address data as a dictionary or None if not found
    """
    query = """
    SELECT * FROM addresses
    WHERE customer_id = %s AND address_type = 'billing'
    """
    params = (customer_id,)
    results = execute_query(query, params)
    return results[0] if results else None


def test_connection() -> bool:
    """
    Test if the database connection is working.
    
    Returns:
        True if connection successful, False otherwise
    """
    try:
        with get_connection():
            return True
    except Error:
        return False


if __name__ == "__main__":
    # Test the connection when running this module directly
    if test_connection():
        print("Database connection successful!")
    else:
        print("Database connection failed.")