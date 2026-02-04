from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Book, BorrowRecord


class BookSerializer(serializers.ModelSerializer):
    genre_display = serializers.CharField(source='get_genre_display', read_only=True)
    is_available = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = [
            'id', 'title', 'author', 'isbn', 'genre',
            'genre_display', 'published_date', 'page_count',
            'available_copies', 'price', 'is_available'
        ]

    def get_is_available(self, obj):
        return obj.available_copies > 0


class BorrowRecordSerializer(serializers.ModelSerializer):
    book_title = serializers.CharField(source='book.title', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = BorrowRecord
        fields = ['id', 'book', 'book_title', 'user', 'user_username',
                  'borrow_date', 'return_date', 'returned']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_staff']