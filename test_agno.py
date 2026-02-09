"""
Test Agno installation and basic functionality
"""
import sys

print("🔍 Checking Agno installation...\n")

# Test 1: Import agno
try:
    import agno
    print("✅ agno imported successfully")
    print(f"   Version: {agno.__version__ if hasattr(agno, '__version__') else 'unknown'}")
except ImportError as e:
    print(f"❌ Failed to import agno: {e}")
    print("   Install with: pip install agno --break-system-packages")
    sys.exit(1)

# Test 2: Check API key
import os
if os.environ.get("OPENROUTER_API_KEY"):
    print("✅ OPENROUTER_API_KEY is set")
elif os.environ.get("OPENAI_API_KEY"):
    print("✅ OPENAI_API_KEY is set")
    print("   (Note: Original demo uses OpenAI, Agno version uses OpenRouter)")
else:
    print("⚠️  No API key found in environment")
    print("   You'll be prompted to enter one when running the agent")

# Test 3: Create a simple test agent (no API call)
try:
    def test_tool(message: str) -> str:
        """A simple test tool."""
        return f"Received: {message}"
    
    test_agent = agno.Agent(
        model=agno.OpenRouterModel(id="anthropic/claude-3.5-haiku"),
        tools=[test_tool],
        instructions="You are a test agent."
    )
    print("✅ Agno agent created successfully")
    
except Exception as e:
    print(f"❌ Failed to create agent: {e}")
    sys.exit(1)

print("\n✅ All checks passed! Agno is ready.\n")
