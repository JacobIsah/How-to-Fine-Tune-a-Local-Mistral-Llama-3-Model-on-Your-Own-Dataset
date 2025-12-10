import logging
import sys
from typing import Dict
from fastmcp import FastMCP

# Configure logging to stderr (critical for MCP protocol integrity)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# Create the FastMCP server instance
mcp = FastMCP(name="CalculatorServer")

# ==================== TOOLS ====================

@mcp.tool
def add(a: float, b: float) -> float:
    """
    Add two numbers together.
    
    Args:
        a: First number
        b: Second number
        
    Returns:
        Sum of a and b
    """
    try:
        result = a + b
        logger.info(f"Addition performed: {a} + {b} = {result}")
        return result
    except TypeError as e:
        logger.error(f"Type error in add: {e}")
        raise ValueError(f"Invalid input types: {e}")


@mcp.tool
def subtract(a: float, b: float) -> float:
    """
    Subtract b from a.
    
    Args:
        a: First number (minuend)
        b: Second number (subtrahend)
        
    Returns:
        Difference of a and b
    """
    try:
        result = a - b
        logger.info(f"Subtraction performed: {a} - {b} = {result}")
        return result
    except TypeError as e:
        logger.error(f"Type error in subtract: {e}")
        raise ValueError(f"Invalid input types: {e}")


@mcp.tool
def multiply(a: float, b: float) -> float:
    """
    Multiply two numbers.
    
    Args:
        a: First number
        b: Second number
        
    Returns:
        Product of a and b
    """
    try:
        result = a * b
        logger.info(f"Multiplication performed: {a} * {b} = {result}")
        return result
    except TypeError as e:
        logger.error(f"Type error in multiply: {e}")
        raise ValueError(f"Invalid input types: {e}")


@mcp.tool
def divide(a: float, b: float) -> float:
    """
    Divide a by b.
    
    Args:
        a: Dividend (numerator)
        b: Divisor (denominator)
        
    Returns:
        Quotient of a divided by b
        
    Raises:
        ValueError: If attempting to divide by zero
    """
    try:
        if b == 0:
            logger.warning(f"Division by zero attempted: {a} / {b}")
            raise ValueError("Cannot divide by zero")
        
        result = a / b
        logger.info(f"Division performed: {a} / {b} = {result}")
        return result
    except (TypeError, ZeroDivisionError) as e:
        logger.error(f"Error in divide: {e}")
        raise ValueError(f"Division error: {e}")


# ==================== RESOURCES ====================

@mcp.resource("config://calculator/settings")
def get_settings() -> Dict:
    """
    Provides calculator configuration and available operations.
    
    Returns:
        Dictionary containing calculator settings and metadata
    """
    logger.debug("Fetching calculator settings")
    
    return {
        "version": "1.0.0",
        "operations": ["add", "subtract", "multiply", "divide"],
        "precision": "IEEE 754 double precision",
        "max_value": 1.7976931348623157e+308,
        "min_value": -1.7976931348623157e+308,
        "supports_negative": True,
        "supports_decimals": True
    }


@mcp.resource("docs://calculator/guide")
def get_guide() -> str:
    """
    Provides a user guide for the calculator server.
    
    Returns:
        String containing usage guide and examples
    """
    logger.debug("Retrieving calculator guide")
    
    guide = """
    # Calculator Server Guide
    
    ## Available Operations
    
    1. **add(a, b)**: Returns a + b
       Example: add(5, 3) = 8
    
    2. **subtract(a, b)**: Returns a - b
       Example: subtract(10, 4) = 6
    
    3. **multiply(a, b)**: Returns a * b
       Example: multiply(7, 6) = 42
    
    4. **divide(a, b)**: Returns a / b
       Example: divide(20, 4) = 5.0
    
    ## Error Handling
    
    - Division by zero will raise a ValueError
    - Non-numeric inputs will raise a ValueError
    - All inputs should be valid numbers (int or float)
    
    ## Precision
    
    The calculator uses IEEE 754 double precision floating-point arithmetic.
    Results may contain minor rounding errors for some operations.
    """
    
    return guide


# ==================== PROMPTS ====================

@mcp.prompt
def calculate_expression(expression: str) -> str:
    """
    Provides instructions for evaluating a mathematical expression.
    
    Args:
        expression: A mathematical expression to evaluate
        
    Returns:
        Formatted prompt instructing the LLM how to evaluate the expression
    """
    logger.debug(f"Generating calculation prompt for: {expression}")
    
    prompt = f"""
    Please evaluate the following mathematical expression step by step:
    
    Expression: {expression}
    
    Instructions:
    1. Break down the expression into individual operations
    2. Use the appropriate calculator tool for each operation
    3. Follow order of operations (parentheses, multiplication/division, addition/subtraction)
    4. Show all intermediate steps
    5. Provide the final result
    
    Available tools: add, subtract, multiply, divide
    """
    
    return prompt.strip()


# ==================== SERVER STARTUP ====================

if __name__ == "__main__":
    logger.info("Starting Calculator MCP Server...")
    
    try:
        # Run the server with stdio transport (default for Claude Desktop)
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)