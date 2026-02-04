from django.contrib.auth.models import User
from django.db import models


class Book(models.Model):
    class Genre(models.TextChoices):
        FICTION = 'FI', 'داستانی'
        SCI_FI = 'SF', 'علمی-تخیلی'
        HISTORY = 'HI', 'تاریخی'
        BIOGRAPHY = 'BI', 'زندگینامه'
        PROGRAMMING = 'PR', 'برنامه‌نویسی'

    title = models.CharField(max_length=200, verbose_name='عنوان')
    author = models.CharField(max_length=100, verbose_name='نویسنده')
    isbn = models.CharField(max_length=13, unique=True, verbose_name='شابک')
    genre = models.CharField(max_length=2, choices=Genre.choices, verbose_name='ژانر')
    published_date = models.DateField(verbose_name='تاریخ انتشار')
    page_count = models.IntegerField(verbose_name='تعداد صفحات')
    available_copies = models.IntegerField(default=1, verbose_name='تعداد نسخه‌های موجود')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='قیمت')

    class Meta:
        ordering = ['title']

    def __str__(self):
        return f"{self.title} - {self.author}"


class BorrowRecord(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='borrow_records')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    borrow_date = models.DateField(auto_now_add=True)
    return_date = models.DateField(null=True, blank=True)
    returned = models.BooleanField(default=False)

    class Meta:
        ordering = ['-borrow_date']
