from django.urls import path
from .views import RegisterView, VerifyOTPView, LoginView, ProductUploadView, CheckSuperuserView, ProductListView, DeleteProductView, RefreshTokenView, LikeProductView, ProductDetailView,UpdateProductView, AddToCartView,CartView,CartCountView,LikedProductsView,CategoryListView,IncreaseQuantity, DecreaseQuantity,RemoveItem,CheckoutAPIView,OrderConfirmationAPIView,InvoiceAPIView,SendInvoiceEmailView,ProfileView,RateOrderAPIView,OrderHistoryView
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
    path('liked-products/', LikedProductsView.as_view(), name='liked-products'),
    path('cart/count/', CartCountView.as_view(), name='cart_count'),
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('cart/increase-quantity/<int:item_id>/', IncreaseQuantity.as_view(), name='increase-quantity'),
    path('cart/decrease-quantity/<int:item_id>/', DecreaseQuantity.as_view(), name='decrease-quantity'),
    path('cart/remove-item/<int:item_id>/', RemoveItem.as_view(), name='remove-item'),
    path('checkout/', views.CheckoutAPIView.as_view(), name='checkout'),
    path('order/confirmation/<int:pk>/', views.OrderConfirmationAPIView.as_view(), name='order_confirmation'),
     path('order/invoice/<int:pk>/', InvoiceAPIView.as_view(), name='generate_invoice'), 
     path('order/invoice/send-email/<int:order_id>/', SendInvoiceEmailView.as_view(), name='send_invoice_email'),
     path('profile/', ProfileView.as_view(), name='profile'),
      path('order/rate/<int:order_id>/', RateOrderAPIView.as_view(), name='rate_order'),
       path('order-history/', OrderHistoryView.as_view(), name='order-history'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)