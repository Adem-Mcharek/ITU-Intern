"""
Test script to verify Azure OpenAI GPT-4 connection
Run this to test your Azure OpenAI configuration before processing meetings
"""
import os
from dotenv import load_dotenv
from openai import AzureOpenAI

# Load environment variables
load_dotenv()

# Configuration
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "https://z-openai-openai4tsb-dev-chn.openai.azure.com/")
deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "GPT-4")
subscription_key = os.getenv("AZURE_OPENAI_API_KEY")
api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")

print("Azure OpenAI Configuration Test")
print("=" * 50)
print(f"Endpoint: {endpoint}")
print(f"Deployment: {deployment}")
print(f"API Version: {api_version}")
print(f"API Key: {'*' * 20 if subscription_key else 'NOT SET'}")
print("=" * 50)

if not subscription_key:
    print("\n❌ ERROR: AZURE_OPENAI_API_KEY not set in .env file")
    print("Please add your API key to the .env file:")
    print("AZURE_OPENAI_API_KEY=your-actual-api-key")
    exit(1)

try:
    # Initialize client
    print("\n🔄 Initializing Azure OpenAI client...")
    client = AzureOpenAI(
        api_version=api_version,
        azure_endpoint=endpoint,
        api_key=subscription_key,
    )
    print("✅ Client initialized successfully")
    
    # Test API call
    print("\n🔄 Testing GPT-4 connection with a simple query...")
    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant.",
            },
            {
                "role": "user",
                "content": "Say 'Hello! GPT-4 is working correctly.' in exactly those words.",
            }
        ],
        max_tokens=100,
        temperature=0.1,
        model=deployment
    )
    
    print("✅ API call successful!")
    print("\n" + "=" * 50)
    print("Response from GPT-4:")
    print("=" * 50)
    print(response.choices[0].message.content)
    print("=" * 50)
    
    print("\n✅ SUCCESS! Azure OpenAI GPT-4 is configured correctly.")
    print("\nYou can now use the enhanced speaker identification system.")
    print("Run: python run.py")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print("\nTroubleshooting:")
    print("1. Check that AZURE_OPENAI_API_KEY is correct")
    print("2. Verify the endpoint URL is correct")
    print("3. Ensure the deployment name 'GPT-4' exists in your Azure OpenAI resource")
    print("4. Check that you have access to the GPT-4 model")
    exit(1)

