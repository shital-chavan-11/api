from django.urls import path
from .views import RegisterView, VerifyOTPView, LoginView, ProductUploadView, CheckSuperuserView, ProductListView, DeleteProductView, RefreshTokenView, LikeProductView, ProductDetailView,UpdateProductView, AddToCartView,CartView,CartCountView
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
      path('add_to_cart/<int:product_id>/', AddToCartView.as_view(), name='add_to_cart'),
    path('cart/', CartView.as_view(), name='cart_view'),
    path('delete-product/<int:product_id>/', DeleteProductView.as_view(), name='delete-product'),
    path('csrf/', views.csrf, name='csrf'),
    path('refresh-token/', RefreshTokenView.as_view(), name='refresh-token'),
    path('like/<int:product_id>/', LikeProductView.as_view(), name='like_product'),
    path('products/<int:product_id>/', ProductDetailView.as_view(), name='product-detail'),
     path('update-product/<int:id>/', UpdateProductView.as_view(), name='update-product'),
     path('cart/count/', CartCountView.as_view(), name='cart_count'),
]

if settings.DEBUG:  # Serve media files only in development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)