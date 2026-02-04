from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    فقط صاحب شیء می‌تواند آن را ویرایش کند
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user


class IsStaffOrReadOnly(permissions.BasePermission):
    """
    فقط staff می‌تواند ایجاد/ویرایش/حذف کند، دیگران فقط خواندن
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff
