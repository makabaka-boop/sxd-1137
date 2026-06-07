from rest_framework.permissions import BasePermission, IsAdminUser, SAFE_METHODS


class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.is_staff


class IsUploader(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return obj.uploader == request.user or request.user.is_staff


class IsReviewer(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class IsAdminUser(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_staff
