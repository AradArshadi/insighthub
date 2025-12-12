"""
API Views for data ingestion.
"""

import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

from .services.data_collector import DataCollector

logger = logging.getLogger(__name__)


class BusinessSearchView(APIView):
    """
    Search for businesses in a location.
    
    GET /api/v1/ingestion/search/?location=New+York&source=foursquare&limit=10
    """
    
    def get(self, request):
        try:
            # Get parameters
            location = request.GET.get('location', settings.DEFAULT_LOCATION)
            source = request.GET.get('source', 'auto')
            query = request.GET.get('query', '')
            category = request.GET.get('category', '')
            limit = int(request.GET.get('limit', 10))
            
            # Validate limit
            limit = min(max(limit, 1), 50)  # Limit to 1-50
            
            # Initialize data collector
            collector = DataCollector()
            
            # Collect data
            result = collector.collect_businesses(
                location=location,
                source=source,
                query=query,
                category=category,
                limit=limit
            )
            
            return Response(result)
            
        except Exception as e:
            logger.error(f"Business search error: {e}")
            return Response(
                {'error': str(e), 'success': False},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BusinessDetailView(APIView):
    """
    Get detailed information about a business.
    
    GET /api/v1/ingestion/business/{business_id}/
    """
    
    def get(self, request, business_id):
        try:
            source = request.GET.get('source', 'auto')
            
            collector = DataCollector()
            
            # Auto-detect source from business_id format
            if source == 'auto':
                if business_id.startswith('mock_'):
                    source = 'mock'
                else:
                    source = collector.get_primary_source()
            
            details = collector.get_business_details(business_id, source)
            
            if details:
                return Response({
                    'success': True,
                    'business_id': business_id,
                    'source': source,
                    'details': details
                })
            else:
                return Response({
                    'success': False,
                    'error': 'Business not found',
                    'business_id': business_id,
                    'source': source
                }, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            logger.error(f"Business detail error: {e}")
            return Response(
                {'error': str(e), 'success': False},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BusinessReviewsView(APIView):
    """
    Get reviews for a business.
    
    GET /api/v1/ingestion/business/{business_id}/reviews/
    """
    
    def get(self, request, business_id):
        try:
            source = request.GET.get('source', 'auto')
            limit = int(request.GET.get('limit', 20))
            
            collector = DataCollector()
            
            # Auto-detect source
            if source == 'auto':
                if business_id.startswith('mock_'):
                    source = 'mock'
                else:
                    source = collector.get_primary_source()
            
            reviews = collector.get_business_reviews(business_id, source, limit)
            
            return Response({
                'success': True,
                'business_id': business_id,
                'source': source,
                'count': len(reviews),
                'reviews': reviews
            })
            
        except Exception as e:
            logger.error(f"Business reviews error: {e}")
            return Response(
                {'error': str(e), 'success': False},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CompetitorAnalysisView(APIView):
    """
    Get competitor analysis for a business.
    
    GET /api/v1/ingestion/competitors/?business=Joe's+Pizza&location=New+York
    """
    
    def get(self, request):
        try:
            business_name = request.GET.get('business', '')
            location = request.GET.get('location', settings.DEFAULT_LOCATION)
            category = request.GET.get('category', '')
            limit = int(request.GET.get('limit', 5))
            
            if not business_name:
                return Response({
                    'error': 'Business name is required',
                    'success': False
                }, status=status.HTTP_400_BAD_REQUEST)
            
            collector = DataCollector()
            
            result = collector.collect_competitors(
                business_name=business_name,
                location=location,
                category=category,
                limit=limit
            )
            
            return Response(result)
            
        except Exception as e:
            logger.error(f"Competitor analysis error: {e}")
            return Response(
                {'error': str(e), 'success': False},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CategoriesView(APIView):
    """
    Get available business categories.
    
    GET /api/v1/ingestion/categories/
    """
    
    def get(self, request):
        try:
            source = request.GET.get('source', 'auto')
            
            collector = DataCollector()
            categories = collector.get_categories(source)
            
            return Response({
                'success': True,
                'source': source,
                'count': len(categories),
                'categories': categories
            })
            
        except Exception as e:
            logger.error(f"Categories error: {e}")
            return Response(
                {'error': str(e), 'success': False},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DataSourcesView(APIView):
    """
    Get information about available data sources.
    
    GET /api/v1/ingestion/sources/
    """
    
    def get(self, request):
        try:
            collector = DataCollector()
            source_info = collector.get_source_info()
            
            return Response({
                'success': True,
                **source_info
            })
            
        except Exception as e:
            logger.error(f"Data sources error: {e}")
            return Response(
                {'error': str(e), 'success': False},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TestConnectionView(APIView):
    """
    Test connection to data sources.
    
    GET /api/v1/ingestion/test/
    """
    
    def get(self, request):
        try:
            collector = DataCollector()
            sources = collector.get_available_sources()
            
            # Test each source
            results = {}
            for source in sources:
                try:
                    # Quick test search
                    test_result = collector.collect_businesses(
                        location='New York',
                        source=source,
                        limit=2
                    )
                    results[source] = {
                        'status': 'connected',
                        'count': test_result.get('count', 0),
                        'test_data': test_result.get('businesses', [])[:1]  # First business only
                    }
                except Exception as e:
                    results[source] = {
                        'status': 'error',
                        'error': str(e)
                    }
            
            return Response({
                'success': True,
                'available_sources': sources,
                'primary_source': collector.get_primary_source(),
                'test_results': results,
                'environment': {
                    'use_mock_data': getattr(settings, 'USE_MOCK_DATA', True),
                    'foursquare_configured': bool(getattr(settings, 'FOURSQUARE_CLIENT_ID', None) and 
                                                 getattr(settings, 'FOURSQUARE_CLIENT_ID') != 'your-client-id-here')
                }
            })
            
        except Exception as e:
            logger.error(f"Test connection error: {e}")
            return Response(
                {'error': str(e), 'success': False},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )