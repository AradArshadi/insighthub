import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from django.core.cache import cache
from django.db.models import QuerySet
import pandas as pd
from dateutil.relativedelta import relativedelta

logger = logging.getLogger(__name__)


class DataProcessor:
    """Utility class for data processing operations."""
    
    @staticmethod
    def normalize_ratings(df: pd.DataFrame, source: str) -> pd.DataFrame:
        """Normalize ratings from different sources to 0-5 scale."""
        if source == 'google':
            # Google ratings are already 0-5
            df['normalized_rating'] = df['rating'].clip(0, 5)
        elif source == 'yelp':
            # Yelp ratings are 0-5
            df['normalized_rating'] = df['rating'].clip(0, 5)
        elif source == 'tripadvisor':
            # TripAdvisor ratings are 0-5
            df['normalized_rating'] = df['rating'].clip(0, 5)
        else:
            df['normalized_rating'] = df['rating']
        
        return df
    
    @staticmethod
    def calculate_weighted_score(df: pd.DataFrame, weight_col: str = 'review_count') -> float:
        """Calculate weighted average score."""
        if df.empty:
            return 0.0
        
        total_weight = df[weight_col].sum()
        if total_weight == 0:
            return df['normalized_rating'].mean()
        
        weighted_sum = (df['normalized_rating'] * df[weight_col]).sum()
        return weighted_sum / total_weight


class CacheManager:
    """Cache management utilities."""
    
    @staticmethod
    def get_or_set(key: str, func, timeout: int = 3600, *args, **kwargs) -> Any:
        """Get value from cache or set it if not present."""
        value = cache.get(key)
        if value is None:
            value = func(*args, **kwargs)
            cache.set(key, value, timeout)
        return value
    
    @staticmethod
    def invalidate_pattern(pattern: str):
        """Invalidate cache keys matching pattern."""
        from django_redis import get_redis_connection
        redis = get_redis_connection("default")
        
        keys = redis.keys(pattern)
        if keys:
            redis.delete(*keys)


class DateRange:
    """Date range utilities for analytics."""
    
    @staticmethod
    def get_date_ranges() -> Dict[str, Dict[str, datetime]]:
        """Get common date ranges for analytics."""
        now = datetime.now()
        
        return {
            'today': {
                'start': now.replace(hour=0, minute=0, second=0, microsecond=0),
                'end': now
            },
            'yesterday': {
                'start': (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0),
                'end': (now - timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=999999)
            },
            'this_week': {
                'start': (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0),
                'end': now
            },
            'this_month': {
                'start': now.replace(day=1, hour=0, minute=0, second=0, microsecond=0),
                'end': now
            },
            'last_30_days': {
                'start': (now - timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0),
                'end': now
            },
            'last_90_days': {
                'start': (now - timedelta(days=90)).replace(hour=0, minute=0, second=0, microsecond=0),
                'end': now
            },
            'this_year': {
                'start': now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0),
                'end': now
            }
        }


class QuerySetHelper:
    """Utilities for working with QuerySets."""
    
    @staticmethod
    def filter_by_date_range(queryset: QuerySet, start_date: datetime, end_date: datetime, 
                            date_field: str = 'created_at') -> QuerySet:
        """Filter queryset by date range."""
        return queryset.filter(**{
            f'{date_field}__gte': start_date,
            f'{date_field}__lte': end_date
        })
    
    @staticmethod
    def annotate_period(queryset: QuerySet, period: str = 'day', 
                       date_field: str = 'created_at') -> QuerySet:
        """Annotate queryset with period grouping."""
        from django.db.models.functions import Trunc
        
        trunc_map = {
            'day': Trunc('day', date_field),
            'week': Trunc('week', date_field),
            'month': Trunc('month', date_field),
            'year': Trunc('year', date_field),
        }
        
        if period not in trunc_map:
            raise ValueError(f"Invalid period: {period}. Choose from: {list(trunc_map.keys())}")
        
        return queryset.annotate(period=trunc_map[period])


class ErrorHandler:
    """Error handling utilities."""
    
    @staticmethod
    def log_exception(exception: Exception, context: Optional[Dict] = None):
        """Log exception with context."""
        logger.error(f"Exception occurred: {str(exception)}")
        if context:
            logger.error(f"Context: {context}")
    
    @staticmethod
    def retry_on_failure(func, max_attempts: int = 3, delay: int = 1):
        """Retry decorator for handling transient failures."""
        import time
        from functools import wraps
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(delay * (2 ** attempt))  # Exponential backoff
                    else:
                        raise last_exception
            raise last_exception
        
        return wrapper