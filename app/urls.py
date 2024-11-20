from django.urls import path
from .views import RegisterView, VerifyOTPView, LoginView,ProductUploadView,CheckSuperuserView,ProductListView,UpdateProductView, DeleteProductView,RefreshTokenView, LikeProductView
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('login/', LoginView.as_view(), name='login'),
    path('upload-product/', ProductUploadView.as_view(), name='upload-product'),
        path('check-superuser/', CheckSuperuserView.as_view(), name='check-superuser'),
            path('products/', ProductListView.as_view(), name='product-list'),
         path('update-product/<int:product_id>/', UpdateProductView.as_view(), name='update_product'),
    path('delete-product/<int:product_id>/', DeleteProductView.as_view(), name='delete-product'),
        path('csrf/', views.csrf, name='csrf'),
            path('api/token/refresh/', RefreshTokenView.as_view(), name='token_refresh'),
          path('like/<int:product_id>/', LikeProductView.as_view(), name='like_product'),
]
if settings.DEBUG:  # Serve media files only in development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)