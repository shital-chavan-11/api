from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.http import HttpResponse
import csv
from django.utils.html import format_html
from .models import CustomUser, OTP, Product, Cart, CartItem, Like, Order, OrderItem
from .models import Category

# Custom User Admin
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'first_name', 'last_name', 'phone_number', 'address', 'is_staff', 'is_active']
    list_filter = ['is_staff', 'is_active']
    search_fields = ['username', 'email']
    ordering = ['username']
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}), 
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'phone_number', 'address')}), 
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}), 
        ('Important dates', {'fields': ('last_login', 'date_joined')}), 
    )
    add_fieldsets = (
        (None, {'fields': ('username', 'password1', 'password2')}), 
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'phone_number', 'address')}), 
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}), 
    )

admin.site.register(CustomUser, CustomUserAdmin)

# OTP Admin
@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ['user', 'otp_code', 'created_at', 'expires_at']
    list_filter = ['expires_at']
    search_fields = ['user__username', 'otp_code']
    ordering = ['-created_at']

# Product Admin
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'description', 'image_preview', 'get_category_name')  # Show category name
    search_fields = ('name',)
    list_filter = ('price', 'category')

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" />', obj.image.url)
        return '-'
    image_preview.short_description = 'Image'

    def get_category_name(self, obj):
        return obj.category.name if obj.category else '-'
    get_category_name.short_description = 'Category'

admin.site.register(Product, ProductAdmin)

# Like Admin
class LikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'created_at')
    search_fields = ('user__username', 'product__name')
    list_filter = ('created_at',)

admin.site.register(Like, LikeAdmin)

# Cart Item Admin
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'product', 'quantity')
    search_fields = ('cart__user__username', 'product__name')
    list_filter = ('cart',)

admin.site.register(CartItem, CartItemAdmin)

# Cart Admin with Inline CartItem Management
class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 1

class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_total_items', 'get_total_price', 'created_at')
    list_filter = ['user']
    inlines = [CartItemInline]
    actions = ['export_as_csv']

    def get_total_items(self, obj):
        return sum([item.quantity for item in obj.cartitem_set.all()])
    get_total_items.short_description = 'Total Items'

    def get_total_price(self, obj):
        return sum([item.product.price * item.quantity for item in obj.cartitem_set.all()])
    get_total_price.short_description = 'Total Price'

    def export_as_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=carts.csv'
        writer = csv.writer(response)
        writer.writerow(['User', 'Total Items', 'Total Price', 'Created At'])
        for cart in queryset:
            writer.writerow([cart.user.username, cart.get_total_items(), cart.get_total_price(), cart.created_at])
        return response

admin.site.register(Cart, CartAdmin)

# Order Item Admin
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price')
    search_fields = ('order__user__username', 'product__name')
    list_filter = ('order',)

admin.site.register(OrderItem, OrderItemAdmin)

# Order Admin with Inline OrderItem Management
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1


from django.contrib import admin
from .models import Profile

class ProfileAdmin(admin.ModelAdmin):
    # List the fields you want to display in the admin list view
    list_display = ('user', 'phone_number', 'address')

    # Add search functionality by phone number or address (optional)
    search_fields = ('phone_number', 'address')

    # Add filter options (optional)
    list_filter = ('user',)

    # Define which fields to display in the form view
    fieldsets = (
        (None, {
            'fields': ('user', 'phone_number', 'address')
        }),
    )

    # Optionally, you can add ordering
    ordering = ('user',)

admin.site.register(Profile, ProfileAdmin)


class OrderAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_price', 'status', 'ordered_at', 'address', 'phone_number')
    list_filter = ['status', 'ordered_at']
    search_fields = ['user__username', 'status']
    inlines = [OrderItemInline]

    def total_price(self, obj):
        return sum([item.price * item.quantity for item in obj.items.all()])
    total_price.short_description = 'Total Price'

    def get_shipping_address(self, obj):
        return obj.shipping_address  # This should return the shipping address field from Order
    get_shipping_address.short_description = 'Shipping Address'

admin.site.register(Order, OrderAdmin)