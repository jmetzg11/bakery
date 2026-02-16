from django.contrib import admin
from django.contrib.auth.models import User, Group

from .models import Ingredient, IngredientOrder, Item, ItemIngredient, ItemSold

admin.site.unregister(User)
admin.site.unregister(Group)


class ItemIngredientInline(admin.TabularInline):
    model = ItemIngredient
    extra = 1


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_amount', 'measurement_type', 'cost')


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'servings_per_unit', 'price_per_unit', 'price_per_serving')
    inlines = [ItemIngredientInline]


@admin.register(IngredientOrder)
class IngredientOrderAdmin(admin.ModelAdmin):
    list_display = ('date', 'ingredient', 'quantity', 'cost')


@admin.register(ItemSold)
class ItemSoldAdmin(admin.ModelAdmin):
    list_display = ('date', 'item', 'quantity', 'price')
