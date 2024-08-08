import asyncio
import os
from api_client import test_api_connection

async def main():
    is_connected = await test_api_connection()
    print(f"API connection successful: {is_connected}")

if __name__ == "__main__":
    asyncio.run(main())