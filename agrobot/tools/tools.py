import re
import logging
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import json
from datetime import datetime
from .db import get_connection, execute_query

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QueryType(Enum):
    SELECT = "SELECT"
    INSERT = "INSERT" 
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    UNKNOWN = "UNKNOWN"

@dataclass
class QueryResult:
    success: bool
    data: Optional[List[Dict[str, Any]]] = None
    error_message: Optional[str] = None
    rows_affected: Optional[int] = None
    execution_time: Optional[float] = None
    query_type: Optional[QueryType] = None

class QueryValidator:
    """Validates SQL queries for security and safety"""
    
    # Dangerous keywords that should be blocked
    DANGEROUS_KEYWORDS = {
        'DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE', 'GRANT', 
        'REVOKE', 'EXEC', 'EXECUTE', 'SHUTDOWN', 'KILL', 'LOAD_FILE',
        'INTO OUTFILE', 'INTO DUMPFILE', 'UNION', 'INFORMATION_SCHEMA',
        'MYSQL', 'PERFORMANCE_SCHEMA', 'SYS', 'SHOW', 'DESCRIBE', 'DESC'
    }
    
    # Allowed tables for BharatAgro platform
    ALLOWED_TABLES = {
        'cartdetails', 'appuser_login', 'order_tracking_status', 'order_product',
        'products', 'vendors', 'categories', 'crops', 'diseases', 
        'pest_management', 'fertilizers', 'seeds', 'pesticides',
        'user_profiles', 'orders', 'reviews', 'inventory',
        'crop_calendar', 'weather_data', 'soil_types', 'regions'
    }
    
    # Maximum allowed result set size
    MAX_RESULT_LIMIT = 1000
    
    def __init__(self):
        self.validation_rules = [
            self._check_dangerous_keywords,
            self._check_allowed_tables,
            self._check_query_structure,
            self._check_limit_clause,
            self._check_injection_patterns
        ]
    
    def validate_query(self, query: str) -> Dict[str, Any]:
        """
        Validates a SQL query for security and safety
        
        Args:
            query: SQL query string to validate
            
        Returns:
            Dict containing validation results
        """
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'query_type': self._detect_query_type(query),
            'sanitized_query': query.strip()
        }
        
        # Apply all validation rules
        for rule in self.validation_rules:
            rule_result = rule(query)
            if not rule_result['passed']:
                validation_result['is_valid'] = False
                validation_result['errors'].extend(rule_result.get('errors', []))
            
            validation_result['warnings'].extend(rule_result.get('warnings', []))
        
        return validation_result
    
    def _detect_query_type(self, query: str) -> QueryType:
        """Detects the type of SQL query"""
        query_upper = query.strip().upper()
        
        if query_upper.startswith('SELECT'):
            return QueryType.SELECT
        elif query_upper.startswith('INSERT'):
            return QueryType.INSERT
        elif query_upper.startswith('UPDATE'):
            return QueryType.UPDATE
        elif query_upper.startswith('DELETE'):
            return QueryType.DELETE
        else:
            return QueryType.UNKNOWN
    
    def _check_dangerous_keywords(self, query: str) -> Dict[str, Any]:
        """Check for dangerous SQL keywords"""
        query_upper = query.upper()
        found_dangerous = []
        
        for keyword in self.DANGEROUS_KEYWORDS:
            if keyword in query_upper:
                found_dangerous.append(keyword)
        
        return {
            'passed': len(found_dangerous) == 0,
            'errors': [f"Dangerous keyword found: {kw}" for kw in found_dangerous]
        }
    
    def _check_allowed_tables(self, query: str) -> Dict[str, Any]:
        """Check if query only accesses allowed tables"""
        # Extract table names using regex
        table_pattern = r'(?:FROM|JOIN|UPDATE|INTO)\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        matches = re.findall(table_pattern, query, re.IGNORECASE)
        
        invalid_tables = []
        for table in matches:
            if table.lower() not in [t.lower() for t in self.ALLOWED_TABLES]:
                invalid_tables.append(table)
        
        return {
            'passed': len(invalid_tables) == 0,
            'errors': [f"Access to table '{table}' not allowed" for table in invalid_tables],
            'warnings': []
        }
    
    def _check_query_structure(self, query: str) -> Dict[str, Any]:
        """Check basic query structure"""
        errors = []
        warnings = []
        
        # Check for basic SQL injection patterns
        suspicious_patterns = [
            r';\s*--',  # Comment after semicolon
            r'\/\*.*\*\/',  # Block comments
            r'@@\w+',  # System variables
            r'char\s*\(',  # CHAR function calls
            r'0x[0-9a-f]+',  # Hex values
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                warnings.append(f"Suspicious pattern detected: {pattern}")
        
        return {
            'passed': True,  # Warnings don't fail validation
            'errors': errors,
            'warnings': warnings
        }
    
    def _check_limit_clause(self, query: str) -> Dict[str, Any]:
        """Ensure SELECT queries have reasonable LIMIT clause"""
        query_upper = query.upper().strip()
        warnings = []
        
        if query_upper.startswith('SELECT'):
            if 'LIMIT' not in query_upper:
                warnings.append(f"No LIMIT clause found. Adding LIMIT {self.MAX_RESULT_LIMIT}")
            else:
                # Extract limit value
                limit_match = re.search(r'LIMIT\s+(\d+)', query_upper)
                if limit_match:
                    limit_value = int(limit_match.group(1))
                    if limit_value > self.MAX_RESULT_LIMIT:
                        warnings.append(f"LIMIT {limit_value} exceeds maximum {self.MAX_RESULT_LIMIT}")
        
        return {
            'passed': True,
            'errors': [],
            'warnings': warnings
        }
    
    def _check_injection_patterns(self, query: str) -> Dict[str, Any]:
        """Check for common SQL injection patterns"""
        injection_patterns = [
            r"'\s*OR\s*'.*'='",  # OR '1'='1'
            r"'\s*AND\s*'.*'='",  # AND '1'='1'
            r"'\s*;\s*DROP\s+",  # '; DROP
            r"UNION\s+SELECT",  # UNION SELECT
            r"'\s*OR\s+1\s*=\s*1",  # OR 1=1
        ]
        
        errors = []
        for pattern in injection_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                errors.append(f"Potential SQL injection pattern detected")
                break
        
        return {
            'passed': len(errors) == 0,
            'errors': errors
        }

class DatabaseManager:
    """Manages database connections and query execution using existing MySQL connection"""
    
    def __init__(self, get_connection_func, execute_query_func):
        """
        Initialize DatabaseManager with existing connection functions
        
        Args:
            get_connection_func: Your existing get_connection context manager
            execute_query_func: Your existing execute_query function
        """
        self.get_connection = get_connection_func
        self.execute_query_db = execute_query_func
        self.validator = QueryValidator()
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> QueryResult:
        """
        Execute a validated SQL query using existing MySQL connection
        
        Args:
            query: SQL query string to execute
            params: Optional tuple of parameters for prepared statement
            
        Returns:
            QueryResult object with execution results
        """
        start_time = datetime.now()
        
        try:
            # Validate query first
            validation = self.validator.validate_query(query)
            
            if not validation['is_valid']:
                return QueryResult(
                    success=False,
                    error_message=f"Query validation failed: {'; '.join(validation['errors'])}"
                )
            
            # Add LIMIT clause if missing for SELECT queries
            processed_query = self._process_query(query, validation)
            
            # Execute query using existing database function
            query_type = validation['query_type']
            
            if query_type == QueryType.SELECT:
                # Use existing execute_query function for SELECT
                data = self.execute_query_db(processed_query, params)
                
                return QueryResult(
                    success=True,
                    data=data,
                    rows_affected=len(data),
                    execution_time=(datetime.now() - start_time).total_seconds(),
                    query_type=query_type
                )
            else:
                # For INSERT, UPDATE, DELETE - use connection directly
                with self.get_connection() as connection:
                    cursor = connection.cursor()
                    try:
                        cursor.execute(processed_query, params or ())
                        connection.commit()
                        rows_affected = cursor.rowcount
                        
                        return QueryResult(
                            success=True,
                            rows_affected=rows_affected,
                            execution_time=(datetime.now() - start_time).total_seconds(),
                            query_type=query_type
                        )
                    except Exception as e:
                        connection.rollback()
                        raise e
                    finally:
                        cursor.close()
                    
        except Exception as e:
            logger.error(f"Database error: {str(e)}")
            return QueryResult(
                success=False,
                error_message=f"Database error: {str(e)}",
                execution_time=(datetime.now() - start_time).total_seconds()
            )
    
    def _process_query(self, query: str, validation: Dict[str, Any]) -> str:
        """Process and modify query based on validation results"""
        processed_query = query.strip()
        
        # Add LIMIT clause for SELECT queries without one
        if (validation['query_type'] == QueryType.SELECT and 
            'LIMIT' not in query.upper()):
            processed_query += f" LIMIT {self.validator.MAX_RESULT_LIMIT}"
        
        return processed_query

# Tool function for the SequentialAgent
def query_executer(query: str, params_json: Optional[str] = None, **kwargs) -> Dict[str, Any]:
    """
    Tool function for executing SQL queries in the BharatAgro system
    
    Args:
        query: SQL query string to execute
        params_json: Optional JSON string representation of parameters for prepared statement
        **kwargs: Additional parameters
        
    Returns:
        Dictionary with execution results
    """
    
    # Convert JSON string to tuple if provided
    params = None
    if params_json:
        try:
            # Convert JSON array to tuple
            params = tuple(json.loads(params_json))
        except json.JSONDecodeError:
            return {
                'success': False,
                'error': f"Invalid JSON format for params: {params_json}"
            }
    
    # Initialize database manager with your existing functions
    db_manager = DatabaseManager(get_connection, execute_query)
    
    # Execute query
    result = db_manager.execute_query(query, params)
    
    # Format response for the agent
    response = {
        'success': result.success,
        'execution_time': result.execution_time,
        'query_type': result.query_type.value if result.query_type else None
    }
    
    if result.success:
        if result.data is not None:
            serializable_data = []
            for row in result.data:
                serializable_row = {}
                for key, value in row.items():
                    if isinstance(value, datetime):
                        serializable_row[key] = value.isoformat()
                    else:
                        serializable_row[key] = value
                serializable_data.append(serializable_row)

            response['data'] = serializable_data
            response['row_count'] = len(result.data)
        else:
            response['rows_affected'] = result.rows_affected
        
        logger.info(f"Query executed successfully: {result.rows_affected or len(result.data or [])} rows")
    else:
        response['error'] = result.error_message
        logger.error(f"Query execution failed: {result.error_message}")
    
    return response

# Example usage and testing
def test_query_system():
    """Test the query validation and execution system"""
    
    # Test queries
    test_queries = [
    # 1. Select all products with status 'Placed'
    "SELECT * FROM order_product WHERE status = 'Placed';",

    # 2. Select products with a discount greater than $5
    "SELECT prod_id, prod_name, discount FROM order_product WHERE discount > 5.00;",

    # 3. Join order_product with order_tracking_status to get tracking status
    "SELECT op.prod_id, op.prod_name, ots.status AS tracking_status "
    "FROM order_product op "
    "JOIN order_tracking_status ots ON op.prod_id = ots.product_id;",

    # 4. Select the most recently updated product
    "SELECT * FROM order_product ORDER BY update_date DESC LIMIT 1;",

    # 5. Select user details by email
    "SELECT fullname, phone FROM appuser_login WHERE email = 'alice@example.com';",

    # 6. Count how many orders have status 'Cancelled'
    "SELECT COUNT(*) AS cancelled_orders FROM order_product WHERE status = 'Cancelled';",

    # 7. List all distinct statuses used in order_product
    "SELECT DISTINCT status FROM order_product;",

    # 8. Select cart items for a specific vendor
    "SELECT * FROM cartdetails WHERE vendor_id = 'VEND123';",

    # 9. Join cartdetails with order_product to get full product info in cart
    "SELECT cd.prod_id, op.prod_name, op.prod_price "
    "FROM cartdetails cd "
    "JOIN order_product op ON cd.prod_id = op.prod_id;",

    # 10. Get total price (after discount + shipping) for all 'Accepted' orders
    "SELECT SUM(prod_price - discount + shipping) AS total_accepted_price "
    "FROM order_product WHERE status = 'Accepted';"
]

    
    db_manager = DatabaseManager(get_connection, execute_query)
    
    for query in test_queries:
        print(f"\nTesting query: {query}")
        result = db_manager.execute_query(query)
        print(f"Success: {result.success}")
        if not result.success:
            print(f"Error: {result.error_message}")
        else:
            print(f"Rows affected/returned: {result.rows_affected}")


# if __name__ == "__main__":
#     test_query_system()