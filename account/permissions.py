from rest_framework.permissions import BasePermission

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        if request.user.role == 'admin':
            return True

class IsParentOrAdmin(BasePermission):
    def has_permission(self, request, view):
        if request.user.role in ['parent', 'admin']:
            return True
        
        
    

