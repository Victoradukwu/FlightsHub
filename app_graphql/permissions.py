from strawberry.permission import BasePermission

from models.authentication import UserRole


class IsAuthenticated(BasePermission):
    message = "Authentication required"

    def has_permission(self, source, info, **kwargs):
        return info.context.get("user") is not None
    
    
class IsAdminUser(BasePermission):
    message = "Only Admins can perform this operation"

    def has_permission(self, source, info, **kwargs)-> bool:
        user = info.context.get("user")
        return user is not None and user.role == UserRole.GLOBAL_ADMIN
