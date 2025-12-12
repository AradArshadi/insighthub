"""
Google Places API integration with budget control.
"""

import requests
import time
from typing import Dict, List, Optional
from django.conf import settings
from .base import DataSource
from ..budget_control import BudgetTracker, RateLimiter


class GooglePlacesSource(DataSource):
    """Google Places API implementation."""
    
    BASE_URL = "https://maps.googleapis.com/maps/api/place"
    
    def __init__(self):
        self.api_key = settings.GOOGLE_PLACES_API_KEY
        self.budget_tracker = BudgetTracker()
        self.rate_limiter = RateLimiter(requests_per_minute=10)  # Google's limit
        
        if not self.api_key or self.api_key == 'your-google-places-api-key-here':
            raise ValueError("Google Places API key not configured")
    
    def search_businesses(self, location: str, query: str = "", 
                         radius: int = 1000, business_type: str = "") -> List[Dict]:
        """Search for businesses near a location."""
        
        # Check budget
        if not self.budget_tracker.can_make_request('google_places', 'search'):
            raise Exception("Budget limit reached for Google Places API")
        
        # Apply rate limiting
        self.rate_limiter.wait_if_needed()
        
        # Build request parameters
        params = {
            'key': self.api_key,
            'location': self._parse_location(location),
            'radius': radius,
            'type': business_type if business_type else 'restaurant'
        }
        
        if query:
            params['keyword'] = query
        
        try:
            # Make API request
            response = requests.get(
                f"{self.BASE_URL}/nearbysearch/json",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            # Record the request cost
            self.budget_tracker.record_request('google_places', 'search')
            
            # Process results
            businesses = []
            for place in data.get('results', [])[:10]:  # Limit to 10 results
                business = self._format_business(place)
                if business:
                    businesses.append(business)
            
            return businesses
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Google Places API error: {e}")
            raise Exception(f"Google Places API error: {str(e)}")
    
    def get_business_details(self, place_id: str) -> Optional[Dict]:
        """Get detailed information about a business."""
        
        if not self.budget_tracker.can_make_request('google_places', 'details'):
            raise Exception("Budget limit reached for Google Places API")
        
        self.rate_limiter.wait_if_needed()
        
        params = {
            'key': self.api_key,
            'place_id': place_id,
            'fields': 'name,formatted_address,geometry,rating,user_ratings_total,'
                     'price_level,opening_hours,types,website,formatted_phone_number'
        }
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/details/json",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            self.budget_tracker.record_request('google_places', 'details')
            
            if data.get('status') == 'OK':
                result = data.get('result', {})
                return self._format_detailed_business(result)
            
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Google Places details error: {e}")
            return None
    
    def get_reviews(self, place_id: str, limit: int = 5) -> List[Dict]:
        """Get reviews for a business."""
        # Note: Google Places API doesn't return reviews in free tier
        # This would require additional permissions and billing
        logger.warning("Google Places reviews require additional permissions and billing")
        return []
    
    def _parse_location(self, location: str) -> str:
        """Parse location string to lat,lng format."""
        # If location is already lat,lng
        if ',' in location and len(location.split(',')) == 2:
            try:
                lat, lng = location.split(',')
                float(lat), float(lng)
                return location
            except ValueError:
                pass
        
        # For demo, use default coordinates
        # In production, you'd use Geocoding API here
        defaults = {
            'new york': '40.7128,-74.0060',
            'los angeles': '34.0522,-118.2437',
            'chicago': '41.8781,-87.6298',
            'houston': '29.7604,-95.3698',
            'miami': '25.7617,-80.1918',
        }
        
        location_lower = location.lower()
        for city, coords in defaults.items():
            if city in location_lower:
                return coords
        
        # Default to NYC
        return '40.7128,-74.0060'
    
    def _format_business(self, place_data: Dict) -> Optional[Dict]:
        """Format Google Places data to our schema."""
        try:
            return {
                'id': place_data.get('place_id'),
                'name': place_data.get('name'),
                'address': place_data.get('vicinity'),
                'latitude': place_data.get('geometry', {}).get('location', {}).get('lat'),
                'longitude': place_data.get('geometry', {}).get('location', {}).get('lng'),
                'rating': place_data.get('rating'),
                'review_count': place_data.get('user_ratings_total'),
                'price_level': place_data.get('price_level'),  # 0-4 scale
                'types': place_data.get('types', []),
                'source': 'google_places',
                'raw_data': place_data  # Keep raw for debugging
            }
        except Exception as e:
            logger.error(f"Error formatting business: {e}")
            return None
    
    def _format_detailed_business(self, place_data: Dict) -> Dict:
        """Format detailed business information."""
        return {
            'id': place_data.get('place_id'),
            'name': place_data.get('name'),
            'full_address': place_data.get('formatted_address'),
            'latitude': place_data.get('geometry', {}).get('location', {}).get('lat'),
            'longitude': place_data.get('geometry', {}).get('location', {}).get('lng'),
            'rating': place_data.get('rating'),
            'review_count': place_data.get('user_ratings_total'),
            'price_level': place_data.get('price_level'),
            'website': place_data.get('website'),
            'phone': place_data.get('formatted_phone_number'),
            'hours': self._parse_hours(place_data.get('opening_hours', {})),
            'categories': place_data.get('types', []),
            'source': 'google_places'
        }
    
    def _parse_hours(self, hours_data: Dict) -> Dict:
        """Parse opening hours."""
        if not hours_data or 'weekday_text' not in hours_data:
            return {}
        
        hours = {}
        for day_text in hours_data.get('weekday_text', []):
            if ': ' in day_text:
                day, time_range = day_text.split(': ', 1)
                hours[day] = time_range
        
        return hours