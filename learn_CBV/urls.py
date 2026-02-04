from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'books-viewset', views.BookViewSet, basename='book-viewset')
router.register(r'books-readonly', views.BookReadOnlyViewSet, basename='book-readonly')
router.register(r'borrows', views.BorrowViewSet, basename='borrow')

urlpatterns = [
    # APIView
    path('stats/', views.BookStatsAPIView.as_view(), name='book-stats'),

    # Generic Views
    path('books/', views.BookListCreateView.as_view(), name='book-list-create'),
    path('books/create/', views.BookCreateView.as_view(), name='book-create'),
    path('books/available/', views.AvailableBooksListView.as_view(), name='available-books'),
    path('books/<int:pk>/', views.BookDetailView.as_view(), name='book-detail'),
    path('books/<int:pk>/update/', views.BookUpdateView.as_view(), name='book-update'),
    path('books/isbn/<str:isbn>/', views.BookRetrieveView.as_view(), name='book-by-isbn'),

    # Mixin با GenericAPIView
    path('books-mixin/', views.BookListCreateAPIView.as_view(), name='book-mixin'),

    # ViewSet‌ها
    path('complex/', views.ComplexBookView.as_view(), name='complex-book'),

    # شامل کردن router
    path('api/', include(router.urls)),
]