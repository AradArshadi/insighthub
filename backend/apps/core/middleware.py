"""
Custom middleware for security and logging.
"""

import json
import time
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from .security import SecurityUtils


class SecurityHeadersMiddleware(MiddlewareMixin):
    """Add security headers to all responses."""
    
    def process_response(self, request, response):
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        
        if settings.SECURE_SSL_REDIRECT:
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        return response


class SensitiveDataLoggingMiddleware(MiddlewareMixin):
    """Middleware to sanitize sensitive data in logs."""
    
    def process_request(self, request):
        # Start timer for request duration
        request.start_time = time.time()
        return None
    
    def process_response(self, request, response):
        # Calculate request duration
        duration = 0
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
        
        # Get request data and sanitize it
        request_data = {
            'method': request.method,
            'path': request.path,
            'user': str(request.user) if request.user.is_authenticated else 'anonymous',
            'duration': f"{duration:.3f}s",
            'status_code': response.status_code,
        }
        
        # Add query params (sanitized)
        if request.GET:
            request_data['query_params'] = SecurityUtils.sanitize_log_data(dict(request.GET))
        
        # Add request body for POST/PUT (sanitized)
        if request.method in ['POST', 'PUT', 'PATCH'] and request.body:
            try:
                body = json.loads(request.body.decode('utf-8'))
                request_data['body'] = SecurityUtils.sanitize_log_data(body)
            except:
                request_data['body'] = '[BINARY OR INVALID JSON]'
        
        # Log the request (in production, you'd use structured logging)
        if settings.DEBUG:
            from .utils import logger
            logger.info(f"Request: {request_data}")
        
        return response


class APIKeyValidationMiddleware(MiddlewareMixin):
    """Middleware to validate API keys for external API endpoints."""
    
    EXTERNAL_API_PATHS = ['/api/v1/ingestion/']
    
    def process_request(self, request):
        # Only check for ingestion API endpoints
        if any(request.path.startswith(path) for path in self.EXTERNAL_API_PATHS):
            from django.conf import settings
            
            # Check if API keys are configured
            if not settings.YELP_API_KEY or settings.YELP_API_KEY == 'your-yelp-api-key-here':
                from django.http import JsonResponse
                return JsonResponse({
                    'error': 'Yelp API key not configured',
                    'message': 'Please configure YELP_API_KEY in environment variables'
                }, status=500)
            
            if not settings.GOOGLE_PLACES_API_KEY or settings.GOOGLE_PLACES_API_KEY == 'your-google-places-api-key-here':
                from django.http import JsonResponse
                return JsonResponse({
                    'error': 'Google Places API key not configured',
                    'message': 'Please configure GOOGLE_PLACES_API_KEY in environment variables'
                }, status=500)
        
        return None