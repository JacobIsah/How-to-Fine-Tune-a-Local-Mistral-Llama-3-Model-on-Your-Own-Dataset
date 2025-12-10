import asyncio
import logging
import sys
from typing import Any
from fastmcp import Client, FastMCP

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)


async def main():
    """
    Main client function demonstrating server interaction.
    """
    
    # Create server instance for in-process communication
    # This avoids subprocess complexity for testing
    from calculator_server import mcp as server
    
    logger.info("Initializing Calculator Client...")
    
    try:
        # Create client connected to the server
        async with Client(server) as client:
            logger.info("✓ Connected to Calculator Server")
            
            # ==================== 1. DISCOVER CAPABILITIES ====================
            
            print("\n" + "="*60)
            print("1. DISCOVERING SERVER CAPABILITIES")
            print("="*60)
            
            # List available tools
            tools = await client.list_tools()
            print(f"\nAvailable Tools ({len(tools)}):")
            for tool in tools:
                print(f"  • {tool.name}: {tool.description}")
            
            # List available resources
            resources = await client.list_resources()
            print(f"\nAvailable Resources ({len(resources)}):")
            for resource in resources:
                print(f"  • {resource.uri}: {resource.name or resource.uri}")
            
            # List available prompts
            prompts = await client.list_prompts()
            print(f"\nAvailable Prompts ({len(prompts)}):")
            for prompt in prompts:
                print(f"  • {prompt.name}: {prompt.description}")
            
            # ==================== 2. CALL TOOLS ====================
            
            print("\n" + "="*60)
            print("2. CALLING TOOLS")
            print("="*60)
            
            # Simple addition
            print("\nTest 1: Adding 15 + 27")
            result = await client.call_tool("add", {"a": 15, "b": 27})
            result_value = extract_tool_result(result)
            print(f"  Result: 15 + 27 = {result_value}")
            
            # Division with error handling
            print("\nTest 2: Dividing 100 / 5")
            result = await client.call_tool("divide", {"a": 100, "b": 5})
            result_value = extract_tool_result(result)
            print(f"  Result: 100 / 5 = {result_value}")
            
            # Error case: division by zero
            print("\nTest 3: Division by Zero (Error Handling)")
            try:
                result = await client.call_tool("divide", {"a": 10, "b": 0})
                print(f"  Unexpected success: {result}")
            except Exception as e:
                print(f"  ✓ Error caught correctly: {str(e)}")
            
            # ==================== 3. READ RESOURCES ====================
            
            print("\n" + "="*60)
            print("3. READING RESOURCES")
            print("="*60)
            
            # Read settings resource
            print("\nFetching Calculator Settings...")
            settings_resource = await client.read_resource("config://calculator/settings")
            print(f"  Version: {settings_resource[0].text}")
            
            # Read guide resource
            print("\nFetching Calculator Guide...")
            guide_resource = await client.read_resource("docs://calculator/guide")
            # Print first 200 characters of guide
            guide_text = guide_resource[0].text[:200] + "..."
            print(f"  {guide_text}")
            
            # ==================== 4. CHAINING OPERATIONS ====================
            
            print("\n" + "="*60)
            print("4. CHAINING MULTIPLE OPERATIONS")
            print("="*60)
            
            # Calculate: (10 + 5) * 3 - 7
            print("\nCalculating: (10 + 5) * 3 - 7")
            
            # Step 1: Add
            print("  Step 1: Add 10 + 5")
            add_result = await client.call_tool("add", {"a": 10, "b": 5})
            step1 = extract_tool_result(add_result)
            print(f"    Result: {step1}")
            
            # Step 2: Multiply
            print("  Step 2: Multiply 15 * 3")
            mult_result = await client.call_tool("multiply", {"a": step1, "b": 3})
            step2 = extract_tool_result(mult_result)
            print(f"    Result: {step2}")
            
            # Step 3: Subtract
            print("  Step 3: Subtract 45 - 7")
            final_result = await client.call_tool("subtract", {"a": step2, "b": 7})
            final = extract_tool_result(final_result)
            print(f"    Final Result: {final}")
            
            # ==================== 5. GET PROMPT TEMPLATE ====================
            
            print("\n" + "="*60)
            print("5. USING PROMPT TEMPLATES")
            print("="*60)
            
            expression = "25 * 4 + 10 / 2"
            print(f"\nPrompt Template for: {expression}")
            prompt_response = await client.get_prompt(
                "calculate_expression",
                {"expression": expression}
            )
            print(f"  Template:\n{prompt_response.messages[0].content.text}")
            
            logger.info("✓ Client operations completed successfully")
    
    except Exception as e:
        logger.error(f"Client error: {e}", exc_info=True)
        sys.exit(1)


def extract_tool_result(response: Any) -> Any:
    """
    Extract the actual result value from a tool response.
    
    MCP wraps results in content objects, this helper unwraps them.
    """
    try:
        if hasattr(response, 'content') and response.content:
            content = response.content[0]
            # Prefer explicit text content when available (TextContent)
            if hasattr(content, 'text') and content.text is not None:
                # If the text is JSON, try to parse and extract a `result` field
                import json as _json
                text_val = content.text
                try:
                    parsed_text = _json.loads(text_val)
                    # If JSON contains a result field, return it
                    if isinstance(parsed_text, dict) and 'result' in parsed_text:
                        return parsed_text.get('result')
                    return parsed_text
                except _json.JSONDecodeError:
                    # Try to convert plain text to number
                    try:
                        if '.' in text_val:
                            return float(text_val)
                        return int(text_val)
                    except Exception:
                        return text_val

            # Try to extract JSON result via model `.json()` or dict-like `.json`
            if hasattr(content, 'json'):
                try:
                    if callable(content.json):
                        json_str = content.json()
                        import json as _json
                        try:
                            parsed = _json.loads(json_str)
                        except _json.JSONDecodeError:
                            return json_str
                    else:
                        parsed = content.json

                    # If parsed is a dict, try common shapes
                    if isinstance(parsed, dict):
                        # If nested result exists
                        if 'result' in parsed:
                            res = parsed.get('result')
                        elif 'text' in parsed:
                            res = parsed.get('text')
                        else:
                            res = parsed

                        # If res is str that looks like a number, convert
                        if isinstance(res, str):
                            try:
                                if '.' in res:
                                    return float(res)
                                return int(res)
                            except Exception:
                                return res
                        return res

                    return parsed
                except Exception:
                    pass
        return response
    except Exception as e:
        logger.warning(f"Could not extract result: {e}")
        return response


if __name__ == "__main__":
    logger.info("Calculator Client Starting...")
    asyncio.run(main())