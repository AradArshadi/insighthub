"""
Yelp Fusion API integration.
"""

import requests
from typing import Dict, List, Optional
from django.conf import settings
from .base import DataSource
from ..budget_control import BudgetTracker, RateLimiter


class YelpSource(DataSource):
    """Yelp Fusion API implementation."""
    
    BASE_URL = "https://api.yelp.com/v3"
    
    def __init__(self):
        self.api_key = settings.YELP_API_KEY
        self.budget_tracker = BudgetTracker()
        self.rate_limiter = RateLimiter(requests_per_minute=10)  # Yelp's limit
        
        if not self.api_key or self.api_key == 'your-yelp-api-key-here':
            raise ValueError("Yelp API key not configured")
        
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Accept': 'application/json'
        }
    
    def search_businesses(self, location: str, term: str = "", 
                         categories: str = "", radius: int = 1000, 
                         limit: int = 20) -> List[Dict]:
        """Search for businesses on Yelp."""
        
        if not self.budget_tracker.can_make_request('yelp', 'search'):
            raise Exception("Daily limit reached for Yelp API")
        
        self.rate_limiter.wait_if_needed()
        
        params = {
            'location': location,
            'limit': limit,
            'radius': radius
        }
        
        if term:
            params['term'] = term
        if categories:
            params['categories'] = categories
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/businesses/search",
                headers=self.headers,
                params=params,
                timeout=10
            )
            
            # Check for rate limiting
            if response.status_code == 429:
                logger.warning("Yelp API rate limit reached")
                raise Exception("Yelp API rate limit reached")
            
            response.raise_for_status()
            data = response.json()
            
            self.budget_tracker.record_request('yelp', 'search')
            
            businesses = []
            for business in data.get('businesses', []):
                formatted = self._format_business(business)
                if formatted:
                    businesses.append(formatted)
            
            return businesses
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Yelp API error: {e}")
            raise Exception(f"Yelp API error: {str(e)}")
    
    def get_business_details(self, business_id: str) -> Optional[Dict]:
        """Get detailed business information from Yelp."""
        
        if not self.budget_tracker.can_make_request('yelp', 'business'):
            raise Exception("Daily limit reached for Yelp API")
        
        self.rate_limiter.wait_if_needed()
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/businesses/{business_id}",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            self.budget_tracker.record_request('yelp', 'business')
            
            return self._format_detailed_business(data)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Yelp business details error: {e}")
            return None
    
    def get_reviews(self, business_id: str, limit: int = 50) -> List[Dict]:
        """Get reviews for a business from Yelp."""
        
        if not self.budget_tracker.can_make_request('yelp', 'reviews'):
            raise Exception("Daily limit reached for Yelp API")
        
        self.rate_limiter.wait_if_needed()
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/businesses/{business_id}/reviews",
                headers=self.headers,
                params={'limit': limit},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            self.budget_tracker.record_request('yelp', 'reviews')
            
            reviews = []
            for review in data.get('reviews', []):
                reviews.append(self._format_review(review))
            
            return reviews
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Yelp reviews error: {e}")
            return []
    
    def _format_business(self, business_data: Dict) -> Optional[Dict]:
        """Format Yelp business data to our schema."""
        try:
            return {
                'id': business_data.get('id'),
                'name': business_data.get('name'),
                'address': ', '.join(business_data.get('location', {}).get('display_address', [])),
                'city': business_data.get('location', {}).get('city'),
                'state': business_data.get('location', {}).get('state'),
                'zip_code': business_data.get('location', {}).get('zip_code'),
                'latitude': business_data.get('coordinates', {}).get('latitude'),
                'longitude': business_data.get('coordinates', {}).get('longitude'),
                'rating': business_data.get('rating'),
                'review_count': business_data.get('review_count'),
                'price': business_data.get('price'),  # $, $$, etc.
                'categories': [cat.get('title') for cat in business_data.get('categories', [])],
                'phone': business_data.get('display_phone'),
                'image_url': business_data.get('image_url'),
                'url': business_data.get('url'),
                'source': 'yelp',
                'raw_data': business_data
            }
        except Exception as e:
            logger.error(f"Error formatting Yelp business: {e}")
            return None
    
    def _format_detailed_business(self, business_data: Dict) -> Dict:
        """Format detailed Yelp business information."""
        hours = {}
        for day in business_data.get('hours', []):
            if day.get('open'):
                for time_slot in day['open']:
                    day_idx = time_slot.get('day')
                    day_name = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 
                               'Friday', 'Saturday', 'Sunday'][day_idx]
                    hours[day_name] = f"{time_slot.get('start')[:2]}:{time_slot.get('start')[2:]} - {time_slot.get('end')[:2]}:{time_slot.get('end')[2:]}"
        
        return {
            'id': business_data.get('id'),
            'name': business_data.get('name'),
            'full_address': ', '.join(business_data.get('location', {}).get('display_address', [])),
            'rating': business_data.get('rating'),
            'review_count': business_data.get('review_count'),
            'price': business_data.get('price'),
            'categories': [cat.get('title') for cat in business_data.get('categories', [])],
            'phone': business_data.get('display_phone'),
            'photos': business_data.get('photos', []),
            'hours': hours,
            'transactions': business_data.get('transactions', []),
            'source': 'yelp'
        }
    
    def _format_review(self, review_data: Dict) -> Dict:
        """Format Yelp review data."""
        return {
            'id': review_data.get('id'),
            'rating': review_data.get('rating'),
            'text': review_data.get('text'),
            'user': review_data.get('user', {}).get('name'),
            'user_image': review_data.get('user', {}).get('image_url'),
            'created_at': review_data.get('time_created'),
            'url': review_data.get('url'),
            'source': 'yelp'
        }