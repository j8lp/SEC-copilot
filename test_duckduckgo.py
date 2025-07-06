from langchain_community.tools import DuckDuckGoSearchRun
import time

def test_duckduckgo_search():
    """Test DuckDuckGo search functionality"""
    print("Testing DuckDuckGo Search...")
    print("=" * 50)
    
    try:
        # Create DuckDuckGo search tool
        search = DuckDuckGoSearchRun()
        print("✅ DuckDuckGo search tool created successfully")
        
        # Test query
        test_query = "Apple stock news"
        print(f"\n🔍 Testing search with query: '{test_query}'")
        
        # Add delay to be respectful
        print("⏳ Waiting 2 seconds before search...")
        time.sleep(2)
        
        # Perform search
        results = search.run(test_query)
        
        if results:
            print("✅ Search completed successfully!")
            print(f"📄 Results length: {len(results)} characters")
            print(f"📝 First 200 characters: {results[:200]}...")
        else:
            print("❌ Search returned empty results")
            
    except Exception as e:
        error_str = str(e)
        print(f"❌ DuckDuckGo search failed")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {error_str}")
        
        if "ratelimit" in error_str.lower() or "rate limit" in error_str.lower():
            print("\n⚠️  This is a rate limiting error - DuckDuckGo is blocking requests")
            print("   This usually happens when making too many requests too quickly")
        elif "403" in error_str or "forbidden" in error_str.lower():
            print("\n⚠️  This is a 403 Forbidden error - access is being blocked")
        elif "timeout" in error_str.lower():
            print("\n⚠️  This is a timeout error - the request took too long")
        else:
            print(f"\n❓ This appears to be a different type of error")
    
    print("\n" + "=" * 50)
    print("Test complete!")

if __name__ == "__main__":
    test_duckduckgo_search()
