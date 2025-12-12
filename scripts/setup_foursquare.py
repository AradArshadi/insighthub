#!/usr/bin/env python3
"""
Foursquare API setup script.
Get FREE API keys in 2 minutes!
"""

import webbrowser
import sys

def main():
    print("\n" + "="*60)
    print("   FOURSQUARE API SETUP - FREE 50,000 REQUESTS/MONTH")
    print("="*60)
    
    print("\n🚀 Getting Foursquare API keys is FREE and takes 2 minutes:")
    print("   1. Go to: https://foursquare.com/developers/signup")
    print("   2. Sign up with GitHub or email")
    print("   3. Create a new app")
    print("   4. Get your Client ID and Client Secret")
    
    open_browser = input("\n📱 Open browser to Foursquare? (y/n): ")
    if open_browser.lower() == 'y':
        webbrowser.open('https://foursquare.com/developers/signup')
    
    print("\n🔑 Once you have your keys, add them to your .env file:")
    print("""
    # FOURSQUARE API (FREE - 50K requests/month)
    FOURSQUARE_CLIENT_ID=your-actual-client-id-here
    FOURSQUARE_CLIENT_SECRET=your-actual-client-secret-here
    USE_MOCK_DATA=False  # Set to True for mock data only
    """)
    
    print("\n✅ That's it! You now have:")
    print("   - Real business data")
    print("   - 50,000 free requests per month")
    print("   - No credit card required")
    print("   - Global coverage")
    
    print("\n🎯 Test it with:")
    print("   curl 'http://localhost:8000/api/v1/ingestion/search/?location=new+york'")
    
    input("\nPress Enter to continue...")

if __name__ == '__main__':
    main()