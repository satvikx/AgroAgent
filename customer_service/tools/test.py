import logging
from typing import Dict, Any
from pathlib import Path
import sys

logger = logging.getLogger(__name__)

def track_order(order_id: str) -> dict:
    """
    Tracks the status of an order by its ID.
    
    This function simply queries the order_tracking_status table to get the 
    basic status information of an order.
    
    Args:
        order_id (str): The unique identifier of the order to track.
        
    Returns:
        dict: A dictionary containing order status information.
        
    Example:
        >>> track_order(order_id='ORD-12345')
        {
            'order_id': 'ORD-12345',
            'products': [
                {'product_id': 'soil-123', 'status': 'Shipped', 'created_at': '2025-05-15 14:30:22'},
                {'product_id': 'fert-456', 'status': 'Packed', 'created_at': '2025-05-15 12:15:10'}
            ]
        }
    """
    # Add the root directory to the Python path
    root_dir = Path(__file__).resolve().parent.parent.parent
    sys.path.append(str(root_dir))
    
    from db import execute_query
    
    logger.info("Tracking order status for order ID: %s", order_id)
    
    try:
        # Simple query to get basic order status information
        query = """
        SELECT order_id, product_id, status, created_at
        FROM order_tracking_status
        WHERE order_id = %s
        """
        
        results = execute_query(query, (order_id,))
        
        if not results:
            return {
                "status": "error",
                "message": f"Order ID {order_id} not found"
            }
        
        # Create a simple list of products with their status
        products = []
        for item in results:
            products.append({
                "product_id": item["product_id"],
                "status": item["status"],  # Expecting values: Packed, Shipped, or Cancelled
                "created_at": item["created_at"].strftime("%Y-%m-%d %H:%M:%S") if hasattr(item["created_at"], "strftime") else str(item["created_at"])
            })
        
        return {
            "order_id": order_id,
            "products": products
        }
        
    except Exception as e:
        logger.error(f"Error tracking order {order_id}: {e}")
        return {
            "status": "error",
            "message": f"Failed to retrieve order status: {str(e)}"
        }


if __name__ == "__main__":
    # Example usage
    order_info = track_order("ODRSZI9VG063275")
    print(order_info)