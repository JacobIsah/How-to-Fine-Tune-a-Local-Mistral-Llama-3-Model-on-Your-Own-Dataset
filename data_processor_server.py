import json
import logging
import sys
from typing import Dict, List
import asyncio
from fastmcp import FastMCP

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

mcp = FastMCP(name="DataProcessorServer")

# Simulated data store
DATA_STORE: Dict[str, List[Dict]] = {
    "users": [
        {"id": 1, "name": "Alice", "email": "alice@example.com"},
        {"id": 2, "name": "Bob", "email": "bob@example.com"},
        {"id": 3, "name": "Charlie", "email": "charlie@example.com"},
    ],
    "products": [
        {"id": 101, "name": "Laptop", "price": 999.99},
        {"id": 102, "name": "Mouse", "price": 29.99},
        {"id": 103, "name": "Keyboard", "price": 79.99},
    ]
}


# ==================== ASYNC TOOLS ====================

@mcp.tool
async def search_users(query: str) -> List[Dict]:
    """
    Asynchronously search for users by name or email.
    
    Args:
        query: Search term (name or email)
        
    Returns:
        List of matching users
        
    Raises:
        ValueError: If query is empty
    """
    try:
        # Validate input
        if not query or not isinstance(query, str):
            raise ValueError("Query must be a non-empty string")
        
        query_lower = query.lower()
        
        # Simulate async operation (e.g., database query)
        await asyncio.sleep(0.1)
        
        matches = [
            user for user in DATA_STORE["users"]
            if query_lower in user["name"].lower() or query_lower in user["email"].lower()
        ]
        
        logger.info(f"User search for '{query}' found {len(matches)} results")
        return matches
    
    except ValueError as e:
        logger.error(f"Invalid search query: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in search_users: {e}", exc_info=True)
        raise RuntimeError(f"Search failed: {e}")


@mcp.tool
async def get_user_details(user_id: int) -> Dict:
    """
    Retrieve detailed information for a specific user.
    
    Args:
        user_id: The unique identifier of the user
        
    Returns:
        User details including all available information
        
    Raises:
        ValueError: If user_id is invalid
        KeyError: If user not found
    """
    try:
        if not isinstance(user_id, int) or user_id < 0:
            raise ValueError(f"Invalid user_id: {user_id}")
        
        # Simulate async database operation
        await asyncio.sleep(0.05)
        
        user = next(
            (u for u in DATA_STORE["users"] if u["id"] == user_id),
            None
        )
        
        if not user:
            logger.warning(f"User {user_id} not found")
            raise KeyError(f"User with id {user_id} not found")
        
        # Add computed fields
        user_with_details = {
            **user,
            "account_status": "active",
            "created_at": "2024-01-15"
        }
        
        logger.info(f"Retrieved details for user {user_id}")
        return user_with_details
    
    except (ValueError, KeyError) as e:
        logger.error(f"Error getting user details: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_user_details: {e}", exc_info=True)
        raise RuntimeError(f"Failed to retrieve user: {e}")


@mcp.tool
async def calculate_average_product_price() -> float:
    """
    Calculate the average price of all products.
    
    Returns:
        Average product price
    """
    try:
        # Simulate complex calculation
        await asyncio.sleep(0.2)
        
        if not DATA_STORE["products"]:
            logger.warning("No products available for price calculation")
            raise ValueError("No products in store")
        
        total = sum(p["price"] for p in DATA_STORE["products"])
        average = total / len(DATA_STORE["products"])
        
        logger.info(f"Calculated average product price: ${average:.2f}")
        return round(average, 2)
    
    except ValueError as e:
        logger.error(f"Calculation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in calculate_average_product_price: {e}", exc_info=True)
        raise RuntimeError(f"Price calculation failed: {e}")


# ==================== DYNAMIC RESOURCES ====================

@mcp.resource("data://users/count")
def get_user_count() -> Dict:
    """Dynamic resource showing current user count."""
    count = len(DATA_STORE["users"])
    logger.debug(f"Retrieving user count: {count}")
    return {"count": count, "resource": "users"}


@mcp.resource("data://product/{product_id}")
def get_product_by_id(product_id: int) -> Dict:
    """
    Dynamic resource with parameter.
    Retrieve a specific product by ID.
    """
    logger.debug(f"Fetching product {product_id}")
    
    product = next(
        (p for p in DATA_STORE["products"] if p["id"] == product_id),
        None
    )
    
    if not product:
        logger.warning(f"Product {product_id} not found")
        return {
            "error": f"Product {product_id} not found",
            "available_ids": [p["id"] for p in DATA_STORE["products"]]
        }
    
    return product


# ==================== PROMPTS ====================

@mcp.prompt
def analyze_user_data(user_id: int) -> str:
    """Prompt template for analyzing user data."""
    return f"""
    You are analyzing data for user ID {user_id}.
    
    1. First, retrieve the user details using get_user_details tool with user_id={user_id}
    2. Then, fetch any related products (use calculate_average_product_price for context)
    3. Provide a summary of the user's profile
    4. Suggest relevant products based on the data
    """


# ==================== SERVER STARTUP ====================

if __name__ == "__main__":
    logger.info("Starting Data Processor MCP Server...")
    
    try:
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        logger.info("Server interrupted")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal server error: {e}", exc_info=True)
        sys.exit(1)