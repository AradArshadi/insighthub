"""
Foursquare Places API integration - FREE TIER (50K requests/month)
No credit card required!
"""

import requests
import logging
from typing import Dict, List, Optional
from datetime import datetime
from django.conf import settings
from django.core.cache import cache
from .base import DataSource

logger = logging.getLogger(__name__)


class FoursquareSource(DataSource):
    """
    Foursquare Places API implementation.
    Free tier: 50,000 requests per month!
    """
    
    BASE_URL = "https://api.foursquare.com/v3"
    SEARCH_ENDPOINT = "/places/search"
    PLACE_DETAILS_ENDPOINT = "/places/{fsq_id}"
    PLACE_TIPS_ENDPOINT = "/places/{fsq_id}/tips"
    PLACE_PHOTOS_ENDPOINT = "/places/{fsq_id}/photos"
    
    def __init__(self):
        self.client_id = settings.FOURSQUARE_CLIENT_ID
        self.client_secret = settings.FOURSQUARE_CLIENT_SECRET
        self.api_key = settings.FOURSQUARE_API_KEY if hasattr(settings, 'FOURSQUARE_API_KEY') else None
        
        # Foursquare v3 uses API key, v2 uses client_id/secret
        if not self.api_key and (not self.client_id or not self.client_secret):
            raise ValueError(
                "Foursquare API credentials not configured. "
                "Get FREE keys at: https://foursquare.com/developers"
            )
        
        # Prepare headers for v3 API
        self.headers = {
            'Accept': 'application/json',
            'Authorization': self.api_key if self.api_key else f'{self.client_id}{self.client_secret}'
        }
        
        # For v2 API fallback
        self.v2_params = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'v': '20240101'  # API version date
        }
        
        logger.info("✅ Foursquare API source initialized (FREE tier)")
    
    def search_businesses(self, location: str, query: str = "", 
                         category: str = "", radius: int = 5000, 
                         limit: int = 20) -> List[Dict]:
        """
        Search for businesses/places on Foursquare.
        
        Args:
            location: City name, address, or "lat,lng"
            query: Search term (optional)
            category: Foursquare category ID (optional)
            radius: Search radius in meters (max 100,000)
            limit: Maximum results to return (max 50)
        
        Returns:
            List of business dictionaries
        """
        
        # Check cache first (5 minutes)
        cache_key = f"foursquare_search:{location}:{query}:{category}:{limit}"
        cached = cache.get(cache_key)
        if cached:
            logger.info(f"Cache hit for {cache_key}")
            return cached
        
        # Prepare parameters
        params = {
            'near': location if ',' not in location else None,
            'll': location if ',' in location and len(location.split(',')) == 2 else None,
            'query': query if query else None,
            'categories': category if category else None,
            'radius': min(radius, 100000),  # Foursquare max radius
            'limit': min(limit, 50),  # Foursquare max per request
            'fields': 'fsq_id,name,categories,location,geocodes,distance,rating,price,stats,hours,popularity,tastes'
        }
        
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
        
        try:
            logger.info(f"Searching Foursquare for: {location}")
            
            # Try v3 API first
            if self.api_key:
                response = requests.get(
                    f"{self.BASE_URL}{self.SEARCH_ENDPOINT}",
                    headers=self.headers,
                    params=params,
                    timeout=15
                )
            else:
                # Fallback to v2 API
                params.update(self.v2_params)
                response = requests.get(
                    "https://api.foursquare.com/v2/venues/search",
                    params=params,
                    timeout=15
                )
            
            response.raise_for_status()
            data = response.json()
            
            # Parse response based on API version
            if self.api_key:
                # v3 API response
                places = data.get('results', [])
            else:
                # v2 API response
                places = data.get('response', {}).get('venues', [])
            
            businesses = []
            for place in places[:limit]:
                business = self._format_business(place)
                if business:
                    businesses.append(business)
            
            # Cache results for 5 minutes
            cache.set(cache_key, businesses, 300)
            
            logger.info(f"Found {len(businesses)} businesses from Foursquare")
            return businesses
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Foursquare API error: {e}")
            if response.status_code == 429:
                logger.warning("Foursquare rate limit reached (but FREE tier is generous!)")
            raise Exception(f"Foursquare API error: {str(e)}")
        except Exception as e:
            logger.error(f"Error processing Foursquare data: {e}")
            raise
    
    def get_business_details(self, fsq_id: str) -> Optional[Dict]:
        """Get detailed information about a place."""
        
        cache_key = f"foursquare_details:{fsq_id}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        try:
            if self.api_key:
                # v3 API
                response = requests.get(
                    f"{self.BASE_URL}{self.PLACE_DETAILS_ENDPOINT.format(fsq_id=fsq_id)}",
                    headers=self.headers,
                    params={'fields': 'fsq_id,name,categories,location,geocodes,rating,price,stats,hours,popularity,tastes,website,tel,email,description,photos,social_media'},
                    timeout=15
                )
            else:
                # v2 API
                params = self.v2_params.copy()
                response = requests.get(
                    f"https://api.foursquare.com/v2/venues/{fsq_id}",
                    params=params,
                    timeout=15
                )
            
            response.raise_for_status()
            data = response.json()
            
            if self.api_key:
                place_data = data
            else:
                place_data = data.get('response', {}).get('venue', {})
            
            details = self._format_detailed_business(place_data)
            
            # Cache for 1 hour
            cache.set(cache_key, details, 3600)
            
            return details
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Foursquare details error: {e}")
            return None
    
    def get_reviews(self, fsq_id: str, limit: int = 20) -> List[Dict]:
        """Get tips (reviews) for a place."""
        
        cache_key = f"foursquare_tips:{fsq_id}:{limit}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        try:
            if self.api_key:
                # v3 API - tips endpoint
                response = requests.get(
                    f"{self.BASE_URL}{self.PLACE_TIPS_ENDPOINT.format(fsq_id=fsq_id)}",
                    headers=self.headers,
                    params={'limit': min(limit, 50)},
                    timeout=15
                )
            else:
                # v2 API - tips endpoint
                params = self.v2_params.copy()
                params['limit'] = min(limit, 50)
                response = requests.get(
                    f"https://api.foursquare.com/v2/venues/{fsq_id}/tips",
                    params=params,
                    timeout=15
                )
            
            response.raise_for_status()
            data = response.json()
            
            if self.api_key:
                tips = data.get('results', [])
            else:
                tips = data.get('response', {}).get('tips', {}).get('items', [])
            
            reviews = []
            for tip in tips[:limit]:
                review = self._format_tip(tip)
                if review:
                    reviews.append(review)
            
            # Cache for 30 minutes
            cache.set(cache_key, reviews, 1800)
            
            return reviews
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Foursquare tips error: {e}")
            return []
    
    def get_photos(self, fsq_id: str, limit: int = 10) -> List[Dict]:
        """Get photos for a place."""
        try:
            if self.api_key:
                response = requests.get(
                    f"{self.BASE_URL}{self.PLACE_PHOTOS_ENDPOINT.format(fsq_id=fsq_id)}",
                    headers=self.headers,
                    params={'limit': min(limit, 50)},
                    timeout=15
                )
            else:
                params = self.v2_params.copy()
                params['limit'] = min(limit, 50)
                response = requests.get(
                    f"https://api.foursquare.com/v2/venues/{fsq_id}/photos",
                    params=params,
                    timeout=15
                )
            
            response.raise_for_status()
            data = response.json()
            
            if self.api_key:
                photos = data.get('results', [])
            else:
                photos = data.get('response', {}).get('photos', {}).get('items', [])
            
            return photos[:limit]
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Foursquare photos error: {e}")
            return []
    
    def _format_business(self, place_data: Dict) -> Optional[Dict]:
        """Format Foursquare place data to our schema."""
        try:
            # Extract location
            location = place_data.get('location', {})
            geocodes = place_data.get('geocodes', {}).get('main', {})
            
            # Extract categories
            categories = []
            for cat in place_data.get('categories', []):
                categories.append({
                    'id': cat.get('id'),
                    'name': cat.get('name'),
                    'short_name': cat.get('short_name'),
                    'icon': cat.get('icon', {}).get('prefix') if isinstance(cat.get('icon'), dict) else cat.get('icon')
                })
            
            # Format business data
            business = {
                'id': place_data.get('fsq_id') or place_data.get('id'),
                'name': place_data.get('name', 'Unknown'),
                'address': location.get('formatted_address') or location.get('address'),
                'city': location.get('locality'),
                'state': location.get('region'),
                'country': location.get('country'),
                'postal_code': location.get('postcode'),
                'latitude': geocodes.get('latitude') or location.get('lat'),
                'longitude': geocodes.get('longitude') or location.get('lng'),
                'categories': categories,
                'category_names': [cat.get('name') for cat in categories],
                'distance': place_data.get('distance'),  # in meters
                'rating': place_data.get('rating'),
                'price': place_data.get('price', {}).get('tier') if isinstance(place_data.get('price'), dict) else place_data.get('price'),
                'stats': place_data.get('stats', {}),
                'hours': place_data.get('hours', {}),
                'popularity': place_data.get('popularity'),
                'tastes': place_data.get('tastes', []),
                'source': 'foursquare',
                'raw_data': place_data
            }
            
            # Clean up empty values
            business = {k: v for k, v in business.items() if v not in [None, '', [], {}]}
            
            return business
            
        except Exception as e:
            logger.error(f"Error formatting Foursquare business: {e}")
            logger.debug(f"Problematic data: {place_data}")
            return None
    
    def _format_detailed_business(self, place_data: Dict) -> Dict:
        """Format detailed business information."""
        details = self._format_business(place_data)
        if not details:
            return {}
        
        # Add additional details
        details.update({
            'website': place_data.get('website'),
            'phone': place_data.get('tel'),
            'email': place_data.get('email'),
            'description': place_data.get('description'),
            'social_media': place_data.get('social_media', {}),
            'photos': self.get_photos(details['id'], limit=5),
            'tips_count': place_data.get('stats', {}).get('tip_count', 0),
            'users_count': place_data.get('stats', {}).get('users_count', 0),
            'checkins_count': place_data.get('stats', {}).get('checkins_count', 0),
            'here_now': place_data.get('here_now', {}).get('count', 0) if isinstance(place_data.get('here_now'), dict) else 0,
            'menu': place_data.get('menu', {}),
            'attributes': place_data.get('attributes', {}),
            'verified': place_data.get('verified', False)
        })
        
        return details
    
    def _format_tip(self, tip_data: Dict) -> Dict:
        """Format Foursquare tip to review schema."""
        user = tip_data.get('user', {})
        created_at = tip_data.get('created_at')
        
        return {
            'id': tip_data.get('id'),
            'text': tip_data.get('text', ''),
            'rating': None,  # Foursquare tips don't have ratings
            'user': user.get('name') or user.get('first_name', '') + ' ' + user.get('last_name', ''),
            'user_photo': user.get('photo', {}).get('prefix') + '100x100' + user.get('photo', {}).get('suffix') if user.get('photo') else None,
            'likes_count': tip_data.get('agree_count', 0) or tip_data.get('likes', {}).get('count', 0),
            'created_at': datetime.fromtimestamp(created_at).isoformat() if created_at else None,
            'source': 'foursquare'
        }
    
    def get_categories(self) -> List[Dict]:
        """Get all available Foursquare categories."""
        cache_key = "foursquare_categories"
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        try:
            if self.api_key:
                response = requests.get(
                    f"{self.BASE_URL}/places/categories",
                    headers=self.headers,
                    timeout=15
                )
            else:
                response = requests.get(
                    "https://api.foursquare.com/v2/venues/categories",
                    params=self.v2_params,
                    timeout=15
                )
            
            response.raise_for_status()
            data = response.json()
            
            if self.api_key:
                categories = data.get('results', [])
            else:
                categories = data.get('response', {}).get('categories', [])
            
            # Cache for 24 hours
            cache.set(cache_key, categories, 86400)
            
            return categories
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Foursquare categories error: {e}")
            return []
    
    def search_by_category(self, location: str, category_id: str, 
                          limit: int = 20) -> List[Dict]:
        """Search for places by specific category."""
        return self.search_businesses(
            location=location,
            category=category_id,
            limit=limit
        )