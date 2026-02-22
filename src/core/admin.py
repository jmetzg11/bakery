import json

from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.utils.safestring import mark_safe

from .models import Ingredient, IngredientOrder, Item, ItemIngredient, ItemSold, BASE_UNIT_MAP

admin.site.unregister(User)
admin.site.unregister(Group)

admin.site.site_header = 'Bakery Admin'
admin.site.site_url = '/'


class ItemIngredientInline(admin.TabularInline):
    model = ItemIngredient
    extra = 1
    exclude = ('measurement_type',)
    readonly_fields = ('unit_display',)

    def unit_display(self, obj):
        if obj.pk and obj.ingredient:
            return BASE_UNIT_MAP.get(obj.ingredient.measurement_type, '')
        return '-'
    unit_display.short_description = 'Unit'


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_amount', 'measurement_type', 'cost')


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'price_per_unit', 'price_per_serving', 'servings_per_unit', 'sold_by_slice')
    fields = ('name', 'price_per_unit', 'sold_by_slice','servings_per_unit', 'price_per_serving')
    inlines = [ItemIngredientInline]
    change_form_template = 'admin/core/item/change_form.html'

    def _get_unit_map_json(self):
        unit_map = {}
        for ing in Ingredient.objects.all():
            unit_map[str(ing.id)] = BASE_UNIT_MAP.get(ing.measurement_type, ing.measurement_type)
        return mark_safe(json.dumps(unit_map))

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['unit_map_json'] = self._get_unit_map_json()
        return super().change_view(request, object_id, form_url, extra_context)

    def add_view(self, request, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['unit_map_json'] = self._get_unit_map_json()
        return super().add_view(request, form_url, extra_context)


@admin.register(IngredientOrder)
class IngredientOrderAdmin(admin.ModelAdmin):
    list_display = ('date', 'ingredient', 'quantity', 'cost')


@admin.register(ItemSold)
class ItemSoldAdmin(admin.ModelAdmin):
    list_display = ('date', 'item', 'quantity', 'price')
