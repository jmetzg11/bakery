from datetime import date

from collections import defaultdict
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import F, Sum, Subquery, OuterRef
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.views import View

from .models import Ingredient, IngredientOrder, Item, ItemIngredient, ItemSold


class HomeView(View):
    def get(self, request):
        latest_orders = IngredientOrder.objects.filter(
            ingredient=OuterRef('ingredient'),
        ).order_by('-date', '-id')
        recent_orders = IngredientOrder.objects.filter(
            id__in=Subquery(latest_orders.values('id')[:1])
        ).select_related('ingredient').annotate(
            total=F('quantity') * F('cost')
        ).order_by('ingredient__name')

        latest_sales = ItemSold.objects.filter(
            item=OuterRef('item'),
        ).order_by('-date', '-id')
        recent_sales = ItemSold.objects.filter(
            id__in=Subquery(latest_sales.values('id')[:1])
        ).select_related('item').annotate(
            total=F('quantity') * F('price')
        ).order_by('item__name')

        return render(request, 'core/home.html', {
            'recent_orders': recent_orders,
            'recent_sales': recent_sales,
        })


class IngredientsView(View):
    def get(self, request):
        past_orders = IngredientOrder.objects.select_related('ingredient').order_by('-date', '-id')[:20]
        return render(request, 'core/ingredients.html', {
            'ingredients': Ingredient.objects.all().order_by('name'),
            'past_orders': past_orders,
            'today': date.today().isoformat(),
        })

    @method_decorator(login_required)
    def post(self, request):
        order_date_str = request.POST.get('order_date', '')
        try:
            order_date = date.fromisoformat(order_date_str)
        except ValueError:
            order_date = date.today()

        for ingredient in Ingredient.objects.all():
            raw_qty = request.POST.get(f'quantity_{ingredient.id}', '0')
            try:
                qty = int(raw_qty)
            except (ValueError, TypeError):
                qty = 0
            if qty > 0:
                IngredientOrder.objects.create(
                    date=order_date,
                    ingredient=ingredient,
                    quantity=qty,
                    cost=ingredient.cost,
                )

        return redirect('core:ingredients')


class SalesView(View):
    def get(self, request):
        past_sales = ItemSold.objects.select_related('item').order_by('-date', '-id')[:20]
        return render(request, 'core/sales.html', {
            'items': Item.objects.all().order_by('name'),
            'past_sales': past_sales,
            'today': date.today().isoformat(),
        })

    @method_decorator(login_required)
    def post(self, request):
        sale_date_str = request.POST.get('sale_date', '')
        try:
            sale_date = date.fromisoformat(sale_date_str)
        except ValueError:
            sale_date = date.today()

        for item in Item.objects.all():
            raw_qty = request.POST.get(f'quantity_{item.id}', '0')
            try:
                qty = int(raw_qty)
            except (ValueError, TypeError):
                qty = 0
            if qty > 0:
                ItemSold.objects.create(
                    date=sale_date,
                    item=item,
                    quantity=qty,
                    price=item.price_per_serving,
                )

        return redirect('core:sales')


class ReportsView(View):
    def get(self, request):
        return render(request, 'core/reports.html', {
            'today': date.today().isoformat(),
        })

    def post(self, request):
        ing_start_str = request.POST.get('ing_start_date', '')
        ing_end_str = request.POST.get('ing_end_date', '')
        sales_start_str = request.POST.get('sales_start_date', '')
        sales_end_str = request.POST.get('sales_end_date', '')
        try:
            ing_start = date.fromisoformat(ing_start_str)
        except ValueError:
            ing_start = date.today().replace(day=1)
        try:
            ing_end = date.fromisoformat(ing_end_str)
        except ValueError:
            ing_end = date.today()
        try:
            sales_start = date.fromisoformat(sales_start_str)
        except ValueError:
            sales_start = date.today().replace(day=1)
        try:
            sales_end = date.fromisoformat(sales_end_str)
        except ValueError:
            sales_end = date.today()

        # Sales summary: quantity and revenue per item
        sales = (
            ItemSold.objects.filter(date__gte=sales_start, date__lte=sales_end)
            .values('item__name')
            .annotate(total_qty=Sum('quantity'), total_revenue=Sum(F('quantity') * F('price')))
            .order_by('item__name')
        )
        total_revenue = sum(s['total_revenue'] for s in sales)

        # Ingredient orders summary: quantity and cost per ingredient
        orders = (
            IngredientOrder.objects.filter(date__gte=ing_start, date__lte=ing_end)
            .values('ingredient__name', 'ingredient__measurement_type')
            .annotate(total_qty=Sum('quantity'), total_cost=Sum(F('quantity') * F('cost')))
            .order_by('ingredient__name')
        )
        total_ingredient_cost = sum(o['total_cost'] for o in orders)

        # Ingredient usage from items sold
        ingredient_usage = defaultdict(lambda: Decimal('0'))
        sold_items = (
            ItemSold.objects.filter(date__gte=sales_start, date__lte=sales_end)
            .values('item_id')
            .annotate(total_qty=Sum('quantity'))
        )
        for sold in sold_items:
            item_ingredients = ItemIngredient.objects.filter(
                item_id=sold['item_id']
            ).select_related('ingredient')
            for ii in item_ingredients:
                units_made = Decimal(sold['total_qty']) / ii.item.servings_per_unit
                ingredient_usage[ii.ingredient.name] += round(ii.amount * units_made, 2)

        # Build ingredient balance: ordered vs used vs remaining
        ordered_amounts = {}
        for o in orders:
            name = o['ingredient__name']
            ing = Ingredient.objects.get(name=name)
            ordered_amounts[name] = {
                'ordered': o['total_qty'] * ing.measurement_amount,
                'unit': o['ingredient__measurement_type'],
            }

        ingredient_balance = []
        all_names = sorted(set(list(ordered_amounts.keys()) + list(ingredient_usage.keys())))
        for name in all_names:
            ordered = ordered_amounts.get(name, {}).get('ordered', Decimal('0'))
            unit = ordered_amounts.get(name, {}).get('unit', '')
            used = ingredient_usage.get(name, Decimal('0'))
            remaining = ordered - used
            ingredient_balance.append({
                'name': name,
                'ordered': ordered,
                'used': used,
                'remaining': remaining,
                'unit': unit,
            })

        return render(request, 'core/reports.html', {
            'today': date.today().isoformat(),
            'ing_start_date': ing_start_str,
            'ing_end_date': ing_end_str,
            'sales_start_date': sales_start_str,
            'sales_end_date': sales_end_str,
            'sales': sales,
            'total_revenue': total_revenue,
            'orders': orders,
            'total_ingredient_cost': total_ingredient_cost,
            'ingredient_balance': ingredient_balance,
            'profit': total_revenue - total_ingredient_cost,
            'has_report': True,
        })
