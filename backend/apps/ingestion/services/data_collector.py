"""
Main data collection service - Foursquare + Mock.
"""

import logging
from typing import Dict, List, Optional
from django.conf import settings
from django.core.cache import cache

from ..sources.base import DataSource
from ..sources.foursquare import FoursquareSource
from ..sources.mock_data import MockDataSource

logger = logging.getLogger(__name__)


class DataCollector:
    """
    Smart data collector that uses Foursquare (free) and falls back to mock data.
    """
    
    def __init__(self):
        self.sources: Dict[str, DataSource] = {}
        self._initialize_sources()
    
    def _initialize_sources(self):
        """Initialize available data sources."""
        
        # Always include mock data
        self.sources['mock'] = MockDataSource()
        logger.info("✅ Mock data source ready")
        
        # Try to initialize Foursquare (FREE - no credit card needed)
        try:
            if (hasattr(settings, 'FOURSQUARE_CLIENT_ID') and 
                settings.FOURSQUARE_CLIENT_ID and 
                settings.FOURSQUARE_CLIENT_ID != 'your-client-id-here'):
                
                self.sources['foursquare'] = FoursquareSource()
                logger.info("✅ Foursquare API source ready (50K free requests/month)")
                
            else:
                logger.warning("⚠️  Foursquare API not configured. Using mock data only.")
                logger.info("💡 Get FREE keys at: https://foursquare.com/developers")
                
        except Exception as e:
            logger.warning(f"❌ Foursquare API initialization failed: {e}")
            logger.info("Falling back to mock data only")
    
    def get_available_sources(self) -> List[str]:
        """Get list of available data sources."""
        return list(self.sources.keys())
    
    def get_primary_source(self) -> str:
        """Get the primary data source (foursquare if available, else mock)."""
        if 'foursquare' in self.sources:
            return 'foursquare'
        return 'mock'
    
    def collect_businesses(self, location: str, source: str = 'auto', 
                          query: str = "", category: str = "",
                          limit: int = 10) -> Dict:
        """
        Collect businesses from specified or auto-selected source.
        
        Args:
            location: City name or "lat,lng"
            source: 'auto', 'foursquare', or 'mock'
            query: Search query (optional)
            category: Category filter (optional)
            limit: Maximum results
        
        Returns:
            Dictionary with businesses and metadata
        """
        
        # Auto-select best source
        if source == 'auto':
            source = self.get_primary_source()
        
        # Validate source
        if source not in self.sources:
            available = self.get_available_sources()
            raise ValueError(f"Source '{source}' not available. Available: {available}")
        
        data_source = self.sources[source]
        
        try:
            logger.info(f"📡 Collecting from {source}: {location}")
            
            # Get data from source
            businesses = data_source.search_businesses(
                location=location,
                query=query,
                category=category,
                limit=limit
            )
            
            # Add source metadata to each business
            for business in businesses:
                business['data_source'] = source
            
            result = {
                'success': True,
                'source': source,
                'location': location,
                'query': query,
                'category': category,
                'count': len(businesses),
                'businesses': businesses,
                'timestamp': self._get_timestamp(),
                'cache_info': {
                    'cached': False,
                    'source': 'live_api' if source != 'mock' else 'generated'
                }
            }
            
            logger.info(f"✅ Collected {len(businesses)} businesses from {source}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error collecting from {source}: {e}")
            
            # Fallback to mock data if real API fails
            if source != 'mock' and 'mock' in self.sources:
                logger.info("🔄 Falling back to mock data")
                return self.collect_businesses(
                    location=location,
                    source='mock',
                    query=query,
                    category=category,
                    limit=limit
                )
            
            raise
    
    def get_business_details(self, business_id: str, source: str) -> Optional[Dict]:
        """Get detailed business information."""
        if source not in self.sources:
            return None
        
        try:
            details = self.sources[source].get_business_details(business_id)
            if details:
                details['data_source'] = source
            return details
        except Exception as e:
            logger.error(f"Error getting details from {source}: {e}")
            return None
    
    def get_business_reviews(self, business_id: str, source: str, 
                            limit: int = 20) -> List[Dict]:
        """Get reviews for a business."""
        if source not in self.sources:
            return []
        
        try:
            reviews = self.sources[source].get_reviews(business_id, limit)
            for review in reviews:
                review['data_source'] = source
            return reviews
        except Exception as e:
            logger.error(f"Error getting reviews from {source}: {e}")
            return []
    
    def collect_competitors(self, business_name: str, location: str, 
                           category: str = "", limit: int = 5) -> Dict:
        """
        Find competitor businesses.
        """
        # Search for businesses in the same area/category
        search_results = self.collect_businesses(
            location=location,
            query=category or "",
            limit=limit * 2  # Get extra to filter
        )
        
        # Filter out the exact match business
        competitors = []
        for business in search_results['businesses']:
            if business_name.lower() not in business['name'].lower():
                competitors.append(business)
        
        competitors = competitors[:limit]
        
        # Simple analysis
        if competitors:
            ratings = [b.get('rating', 0) for b in competitors if b.get('rating')]
            avg_rating = sum(ratings) / len(ratings) if ratings else 0
            
            review_counts = [b.get('stats', {}).get('tip_count', 0) for b in competitors]
            avg_reviews = sum(review_counts) / len(review_counts) if review_counts else 0
        else:
            avg_rating = avg_reviews = 0
        
        return {
            'success': True,
            'source': search_results['source'],
            'target_business': business_name,
            'competitors_count': len(competitors),
            'competitors': competitors,
            'analysis': {
                'average_competitor_rating': round(avg_rating, 2),
                'average_competitor_reviews': round(avg_reviews, 0),
                'market_saturation': len(competitors)
            }
        }
    
    def get_categories(self, source: str = 'auto') -> List[Dict]:
        """Get available business categories."""
        if source == 'auto':
            source = self.get_primary_source()
        
        if source in self.sources and hasattr(self.sources[source], 'get_categories'):
            return self.sources[source].get_categories()
        
        return []
    
    def get_source_info(self, source: str = None) -> Dict:
        """Get information about data sources."""
        if source:
            if source in self.sources:
                return {
                    'name': source,
                    'available': True,
                    'type': 'real_api' if source == 'foursquare' else 'mock_data',
                    'requests_per_month': 50000 if source == 'foursquare' else 'unlimited'
                }
            return {'name': source, 'available': False}
        
        # Return all sources
        sources_info = []
        for src_name, src_obj in self.sources.items():
            sources_info.append({
                'name': src_name,
                'available': True,
                'type': 'real_api' if src_name == 'foursquare' else 'mock_data',
                'description': 'Foursquare Places API (50K free requests/month)' if src_name == 'foursquare' else 'Generated mock data for development'
            })
        
        return {
            'sources': sources_info,
            'primary_source': self.get_primary_source(),
            'total_sources': len(sources_info)
        }
    
    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()