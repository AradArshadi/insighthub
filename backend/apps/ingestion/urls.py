from django.urls import path
from . import views

app_name = 'ingestion'

urlpatterns = [
    # Search for businesses
    path('search/', views.BusinessSearchView.as_view(), name='business_search'),
    
    # Get business details
    path('business/<str:business_id>/', views.BusinessDetailView.as_view(), name='business_detail'),
    
    # Get business reviews
    path('business/<str:business_id>/reviews/', views.BusinessReviewsView.as_view(), name='business_reviews'),
    
    # Get competitor analysis
    path('competitors/', views.CompetitorAnalysisView.as_view(), name='competitor_analysis'),
    
    # Get available categories
    path('categories/', views.CategoriesView.as_view(), name='categories'),
    
    # Get data source info
    path('sources/', views.DataSourcesView.as_view(), name='data_sources'),
    
    # Test endpoint
    path('test/', views.TestConnectionView.as_view(), name='test_connection'),
]