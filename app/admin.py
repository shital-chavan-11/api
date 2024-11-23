from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, OTP

# Register CustomUser with UserAdmin to make it manageable in admin
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'first_name', 'last_name', 'phone_number', 'address', 'is_staff', 'is_active']
    list_filter = ['is_staff', 'is_active']
    search_fields = ['username', 'email']
    ordering = ['username']

    # Define the fields to be displayed in the form for creating/editing users
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'phone_number', 'address')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    # Define the fields to be displayed in the add user form
    add_fieldsets = (
        (None, {'fields': ('username', 'password1', 'password2')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'phone_number', 'address')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )

# Register the CustomUserAdmin
admin.site.register(CustomUser, CustomUserAdmin)

# Register the OTP model
@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ['user', 'otp_code', 'created_at', 'expires_at']
    list_filter = ['expires_at']
    search_fields = ['user__username', 'otp_code']
    ordering = ['-created_at']
# app/admin.py

from django.contrib import admin
from .models import Product

# Optionally, you can customize the display of your Product model
from django.contrib import admin
from .models import Product, Cart, Like

# Register the Product model
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'description', 'image')  # Customize the display fields in the admin
    search_fields = ('name',)  # Enable search by product name
    list_filter = ('price',)  # Enable filtering by price

admin.site.register(Product, ProductAdmin)

# Register the Like model
class LikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'created_at')  # Customize the display fields
    search_fields = ('user__username', 'product__name')  # Enable search by user and product name
    list_filter = ('created_at',)  # Filter by created date

from django.contrib import admin
from .models import Cart, CartItem, Product

# Inline admin for CartItem
class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 1

class CartAdmin(admin.ModelAdmin):
    # Define list_display with a custom method for product and quantity
    list_display = ('user', 'get_total_items', 'get_total_price', 'created_at')

    # Add custom methods to retrieve related fields
    def get_total_items(self, obj):
        # Returns the total number of items in the cart
        return sum([item.quantity for item in obj.cartitem_set.all()])
    get_total_items.short_description = 'Total Items'

    def get_total_price(self, obj):
        # Returns the total price of items in the cart
        return sum([item.product.price * item.quantity for item in obj.cartitem_set.all()])
    get_total_price.short_description = 'Total Price'

    def created_at(self, obj):
        # Assuming 'created_at' is the timestamp when the cart was created
        return obj.created_at
    created_at.short_description = 'Created At'

    # Include the CartItem inline so that CartItem entries can be edited directly from the Cart model
    inlines = [CartItemInline]

    # Filter by user
    list_filter = ['user']

# Register Cart model with custom CartAdmin
admin.site.register(Cart, CartAdmin)
admin.site.register(CartItem)
