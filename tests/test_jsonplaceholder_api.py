"""Quick test script for JSONPlaceholder API integration."""
import asyncio
import json

from pipelinekit.sources.http import HttpConnector


async def test_jsonplaceholder_api():
    """Test the JSONPlaceholder API connection."""

    # Configuration for JSONPlaceholder API
    config = {
        "url": "https://jsonplaceholder.typicode.com/posts",
        "method": "GET",
        "headers": {
            "Accept": "application/json"
        },
        "timeout": 30
    }

    print("=" * 60)
    print("Testing JSONPlaceholder API connection...")
    print("=" * 60)
    print(f"URL: {config['url']}")
    print()

    connector = HttpConnector(config)

    try:
        # Fetch data
        print("Fetching posts data...")
        data = await connector.fetch()

        print("\nSUCCESS! Data received:")
        print("-" * 60)

        # If it's a list, show count and first few items
        if isinstance(data, list):
            print(f"Total posts received: {len(data)}")
            print("\nFirst 3 posts:")
            for i, post in enumerate(data[:3], 1):
                title = post.get('title', 'No title')
                body = post.get('body', 'No body')
                print(f"\n{i}. Title: {title}")
                print(f"   Body: {body[:80]}...")
        else:
            # If it's a dict, show the full response
            print(json.dumps(data, indent=2))

        print("\n" + "=" * 60)
        print("Test completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\nERROR: {e}")
        print("\nPlease check:")
        print("1. Internet connection")
        print("2. API endpoint is accessible")

    finally:
        await connector.close()


if __name__ == "__main__":
    asyncio.run(test_jsonplaceholder_api())
