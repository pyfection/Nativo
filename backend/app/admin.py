"""
Starlette Admin configuration for Nativo.

Provides an admin interface for managing users, languages, words, documents, and audio.
"""
from starlette_admin.contrib.sqla import Admin, ModelView
from starlette_admin.auth import AdminUser, AuthProvider
from starlette_admin.exceptions import FormValidationError, LoginFailed
from starlette.requests import Request
from starlette.responses import Response

from app.database import engine, SessionLocal
from app.models.user import User, UserRole
from app.models.language import Language
from app.models.word.word import Word
from app.models.document import Document
from app.models.audio import Audio
from app.models.user_language import UserLanguage
from app.models.location import Location
from app.models.image import Image
from app.models.tag import Tag
from app.utils.security import verify_password


class NativoAuthProvider(AuthProvider):
    """
    Authentication provider for Starlette Admin.
    Only allows admin and superuser access.
    """
    
    async def login(
        self,
        username: str,
        password: str,
        remember_me: bool,
        request: Request,
        response: Response,
    ) -> Response:
        """Authenticate user for admin access"""
        db = SessionLocal()
        try:
            # Find user by username or email
            user = db.query(User).filter(
                (User.username == username) | (User.email == username)
            ).first()
            
            if not user:
                raise LoginFailed("Invalid username or password")
            
            # Verify password
            if not verify_password(password, user.hashed_password):
                raise LoginFailed("Invalid username or password")
            
            # Check if user has admin access
            if not (user.is_superuser or user.role == UserRole.ADMIN):
                raise LoginFailed("Access denied: Admin privileges required")
            
            # Store user info in session
            request.session.update({
                "user_id": str(user.id),
                "username": user.username,
                "role": user.role.value,
                "is_superuser": user.is_superuser
            })
            
        finally:
            db.close()
        
        return response
    
    async def is_authenticated(self, request: Request) -> bool:
        """Check if user is authenticated"""
        user_id = request.session.get("user_id")
        return user_id is not None
    
    def get_admin_user(self, request: Request) -> AdminUser:
        """Get current admin user from session"""
        user_id = request.session.get("user_id")
        username = request.session.get("username", "Unknown")
        
        if not user_id:
            return None
        
        return AdminUser(username=username)
    
    async def logout(self, request: Request, response: Response) -> Response:
        """Logout current user"""
        request.session.clear()
        return response


class UserAdmin(ModelView):
    """Admin view for User model"""
    exclude_fields_from_list = ["hashed_password"]
    exclude_fields_from_detail = ["hashed_password"]
    exclude_fields_from_create = ["hashed_password", "created_at", "updated_at"]
    exclude_fields_from_edit = ["hashed_password", "created_at", "updated_at"]
    
    searchable_fields = ["username", "email"]
    sortable_fields = ["username", "email", "role", "created_at"]
    
    page_size = 25
    page_size_options = [25, 50, 100]


class LanguageAdmin(ModelView):
    """Admin view for Language model"""
    exclude_fields_from_create = ["created_at", "updated_at"]
    exclude_fields_from_edit = ["created_at", "updated_at"]
    
    searchable_fields = ["name", "native_name", "iso_639_3"]
    sortable_fields = ["name", "native_name", "iso_639_3", "is_endangered", "created_at"]
    
    page_size = 25
    page_size_options = [25, 50, 100]


class WordAdmin(ModelView):
    """Admin view for Word model"""
    exclude_fields_from_create = ["created_at", "updated_at"]
    exclude_fields_from_edit = ["created_at", "updated_at"]
    
    searchable_fields = ["word", "romanization"]
    sortable_fields = ["word", "part_of_speech", "is_verified", "status", "created_at"]
    
    page_size = 25
    page_size_options = [25, 50, 100]


class DocumentAdmin(ModelView):
    """Admin view for Document model"""
    exclude_fields_from_create = ["created_at", "updated_at"]
    exclude_fields_from_edit = ["created_at", "updated_at"]
    
    searchable_fields = ["content", "source"]
    sortable_fields = ["document_type", "created_at"]
    
    page_size = 25
    page_size_options = [25, 50, 100]


class AudioAdmin(ModelView):
    """Admin view for Audio model"""
    exclude_fields_from_create = ["created_at"]
    exclude_fields_from_edit = ["created_at", "file_path", "uploaded_by_id"]
    
    searchable_fields = ["file_path"]
    sortable_fields = ["file_size", "duration", "created_at"]
    
    page_size = 25
    page_size_options = [25, 50, 100]


class UserLanguageAdmin(ModelView):
    """Admin view for UserLanguage model"""
    exclude_fields_from_create = ["created_at"]
    exclude_fields_from_edit = ["created_at"]
    
    sortable_fields = ["proficiency_level", "can_edit", "can_verify", "created_at"]
    
    page_size = 25
    page_size_options = [25, 50, 100]


class LocationAdmin(ModelView):
    """Admin view for Location model"""
    exclude_fields_from_create = ["created_at"]
    exclude_fields_from_edit = ["created_at"]
    
    searchable_fields = ["name", "description"]
    sortable_fields = ["name", "latitude", "longitude", "created_at"]
    
    page_size = 25
    page_size_options = [25, 50, 100]


class ImageAdmin(ModelView):
    """Admin view for Image model"""
    exclude_fields_from_create = ["created_at"]
    exclude_fields_from_edit = ["created_at", "file_path", "uploaded_by_id"]
    
    searchable_fields = ["file_path", "alt_text", "caption"]
    sortable_fields = ["created_at"]
    
    page_size = 25
    page_size_options = [25, 50, 100]


class TagAdmin(ModelView):
    """Admin view for Tag model"""
    exclude_fields_from_create = ["created_at"]
    exclude_fields_from_edit = ["created_at"]
    
    searchable_fields = ["name", "description"]
    sortable_fields = ["name", "created_at"]
    
    page_size = 25
    page_size_options = [25, 50, 100]


def create_admin(app):
    """
    Create and configure the admin interface.
    
    Args:
        app: FastAPI application instance
        
    Returns:
        Admin instance
    """
    # Create admin with authentication
    admin = Admin(
        engine,
        title="Nativo Admin",
        base_url="/admin",
        auth_provider=NativoAuthProvider(),
        middlewares=None,  # Will use the app's middlewares
    )
    
    # Register model views
    admin.add_view(UserAdmin(User, icon="fa fa-users"))
    admin.add_view(LanguageAdmin(Language, icon="fa fa-language"))
    admin.add_view(WordAdmin(Word, icon="fa fa-book"))
    admin.add_view(DocumentAdmin(Document, icon="fa fa-file-text"))
    admin.add_view(AudioAdmin(Audio, icon="fa fa-volume-up"))
    admin.add_view(ImageAdmin(Image, icon="fa fa-image"))
    admin.add_view(LocationAdmin(Location, icon="fa fa-map-marker"))
    admin.add_view(TagAdmin(Tag, icon="fa fa-tags"))
    admin.add_view(UserLanguageAdmin(UserLanguage, icon="fa fa-link"))
    
    # Mount admin to app
    admin.mount_to(app)
    
    return admin

