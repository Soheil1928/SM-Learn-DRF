from rest_framework import generics, viewsets, mixins, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Avg, Sum
from django.contrib.auth.models import User

from .models import Book, BorrowRecord
from .serializers import BookSerializer, BorrowRecordSerializer, UserSerializer
from .permissions import IsOwnerOrReadOnly, IsStaffOrReadOnly


# 1. APIView (پایه‌ای‌ترین)
class BookStatsAPIView(APIView):
    """نمایش آمار کلی - APIView برای عملیات سفارشی"""
    permission_classes = [AllowAny]

    def get(self, request):
        stats = {
            'total_books': Book.objects.count(),
            'available_books': Book.objects.filter(available_copies__gt=0).count(),
            'total_genres': Book.objects.values('genre').distinct().count(),
            'avg_price': Book.objects.aggregate(avg=Avg('price'))['avg'] or 0,
            'total_pages': Book.objects.aggregate(total=Sum('page_count'))['total'] or 0,
        }
        return Response(stats)


# 2. GenericAPIView با mixin‌ها
class BookListCreateAPIView(mixins.ListModelMixin,
                            mixins.CreateModelMixin,
                            generics.GenericAPIView):
    """لیست و ایجاد کتاب - استفاده از mixin‌ها"""
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [IsStaffOrReadOnly]

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def get_queryset(self):
        # فیلتر بر اساس جستجو
        queryset = super().get_queryset()
        search = self.request.query_params.get('search')
        genre = self.request.query_params.get('genre')

        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(author__icontains=search) |
                Q(isbn__icontains=search)
            )

        if genre:
            queryset = queryset.filter(genre=genre)

        return queryset


# 3. ListCreateAPIView (پر استفاده‌ترین)
class BookListCreateView(generics.ListCreateAPIView):
    """لیست و ایجاد کتاب - استفاده از ListCreateAPIView"""
    serializer_class = BookSerializer
    permission_classes = [IsStaffOrReadOnly]
    filterset_fields = ['genre', 'author']
    search_fields = ['title', 'author', 'isbn']

    def get_queryset(self):
        queryset = Book.objects.all()
        # فقط کتاب‌های موجود را نشان بده اگر پارامتر available=1 باشد
        available_only = self.request.query_params.get('available')
        if available_only == '1':
            queryset = queryset.filter(available_copies__gt=0)
        return queryset

    def perform_create(self, serializer):
        # لاگ‌گیری قبل از ذخیره
        print(f"Creating new book: {serializer.validated_data['title']}")
        serializer.save()


# 4. RetrieveUpdateDestroyAPIView
class BookDetailView(generics.RetrieveUpdateDestroyAPIView):
    """نمایش جزئیات، به‌روزرسانی و حذف یک کتاب"""
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [IsStaffOrReadOnly]
    lookup_field = 'pk'

    def perform_update(self, serializer):
        # لاگ‌گیری هنگام به‌روزرسانی
        print(f"Updating book ID: {self.kwargs['pk']}")
        serializer.save()

    def perform_destroy(self, instance):
        # لاگ‌گیری هنگام حذف
        print(f"Deleting book: {instance.title}")
        instance.delete()


# 5. RetrieveAPIView (فقط خواندن)
class BookRetrieveView(generics.RetrieveAPIView):
    """فقط نمایش جزئیات کتاب - بدون امکان ویرایش"""
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [AllowAny]
    lookup_field = 'isbn'  # استفاده از ISBN به جای ID

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        # افزایش view count در صورت نیاز
        return Response(serializer.data)


# 6. UpdateAPIView (فقط به‌روزرسانی)
class BookUpdateView(generics.UpdateAPIView):
    """فقط به‌روزرسانی کتاب - بدون امکان مشاهده یا حذف"""
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [IsAdminUser]

    def partial_update(self, request, *args, **kwargs):
        # اضافه کردن لاگ برای partial update
        print(f"Partial update for book ID: {kwargs['pk']}")
        return super().partial_update(request, *args, **kwargs)


# 7. CreateAPIView (فقط ایجاد)
class BookCreateView(generics.CreateAPIView):
    """فقط ایجاد کتاب جدید"""
    serializer_class = BookSerializer
    permission_classes = [IsAdminUser]

    def create(self, request, *args, **kwargs):
        # اعتبارسنجی اضافی قبل از ایجاد
        isbn = request.data.get('isbn')
        if Book.objects.filter(isbn=isbn).exists():
            return Response(
                {'error': 'کتاب با این شابک از قبل موجود است'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().create(request, *args, **kwargs)


# 8. ListAPIView (فقط لیست)
class AvailableBooksListView(generics.ListAPIView):
    """فقط لیست کتاب‌های موجود"""
    serializer_class = BookSerializer

    def get_queryset(self):
        return Book.objects.filter(available_copies__gt=0)


# 9. ViewSet (قدرتمندترین)
class BookViewSet(viewsets.ModelViewSet):
    """ViewSet کامل برای کتاب‌ها - همه عملیات CRUD"""
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [IsStaffOrReadOnly]

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def borrow(self, request, pk=None):
        """اکشن سفارشی: امانت گرفتن کتاب"""
        book = self.get_object()

        if book.available_copies <= 0:
            return Response(
                {'error': 'این کتاب موجود نیست'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ایجاد رکورد امانت
        borrow_record = BorrowRecord.objects.create(
            book=book,
            user=request.user
        )

        # کاهش تعداد کتاب‌های موجود
        book.available_copies -= 1
        book.save()

        serializer = BorrowRecordSerializer(borrow_record)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """اکشن سفارشی: آمار"""
        stats = {
            'total': Book.objects.count(),
            'by_genre': Book.objects.values('genre').annotate(count=Count('id')),
            'top_authors': Book.objects.values('author').annotate(
                count=Count('id')
            ).order_by('-count')[:5]
        }
        return Response(stats)

    @action(detail=True, methods=['get'])
    def similar_books(self, request, pk=None):
        """اکشن سفارشی: کتاب‌های مشابه"""
        book = self.get_object()
        similar = Book.objects.filter(
            genre=book.genre
        ).exclude(id=book.id)[:5]
        serializer = self.get_serializer(similar, many=True)
        return Response(serializer.data)


# 10. ReadOnlyModelViewSet
class BookReadOnlyViewSet(viewsets.ReadOnlyModelViewSet):
    """فقط عملیات خواندن - مناسب برای API عمومی"""
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=['get'])
    def recent(self, request):
        """کتاب‌های منتشر شده در سال جاری"""
        from datetime import date
        current_year = date.today().year

        recent_books = Book.objects.filter(
            published_date__year=current_year
        )
        serializer = self.get_serializer(recent_books, many=True)
        return Response(serializer.data)


# 11. GenericViewSet با mixin‌ها
class BorrowViewSet(mixins.ListModelMixin,
                    mixins.RetrieveModelMixin,
                    mixins.CreateModelMixin,
                    viewsets.GenericViewSet):
    """ViewSet سفارشی با mixin‌های انتخابی"""
    serializer_class = BorrowRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # هر کاربر فقط رکوردهای خودش را می‌بیند
        if self.request.user.is_staff:
            return BorrowRecord.objects.all()
        return BorrowRecord.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # ذخیره کاربر جاری به‌طور خودکار
        serializer.save(user=self.request.user)


# 12. ترکیب ViewSet با APIView
class ComplexBookView(APIView):
    """ترکیب چندین عملیات در یک View"""
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        # لیست کتاب‌ها با فیلترهای پیچیده
        books = Book.objects.all()

        # فیلترهای مختلف
        genre = request.query_params.get('genre')
        min_pages = request.query_params.get('min_pages')
        max_price = request.query_params.get('max_price')

        if genre:
            books = books.filter(genre=genre)
        if min_pages:
            books = books.filter(page_count__gte=int(min_pages))
        if max_price:
            books = books.filter(price__lte=float(max_price))

        serializer = BookSerializer(books, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        # ایجاد چندین کتاب به‌طور همزمان
        if not isinstance(request.data, list):
            return Response(
                {'error': 'داده باید یک لیست باشد'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = BookSerializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)