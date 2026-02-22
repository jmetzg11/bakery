from datetime import date

from collections import defaultdict
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import F, Sum, Subquery, OuterRef
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.views import View

from .dto import (
    HomeContext, IngredientsContext, SalesContext, ReportContext,
    IngredientBalance, UsageBreakdown,
)
from .forms import OrderDateForm, ReportDateForm, SaleDateForm
from .models import (
    Ingredient, IngredientOrder, Item, ItemIngredient, ItemSold,
    CONVERSION_TO_BASE, BASE_UNIT_MAP,
)


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

        ctx = HomeContext(
            recent_orders=recent_orders,
            recent_sales=recent_sales,
        )
        return render(request, 'core/home.html', vars(ctx))


class IngredientsView(View):
    def get(self, request):
        past_orders = IngredientOrder.objects.select_related('ingredient').order_by('-date', '-id')[:20]
        ctx = IngredientsContext(
            ingredients=Ingredient.objects.all().order_by('name'),
            past_orders=past_orders,
            today=date.today().isoformat(),
        )
        return render(request, 'core/ingredients.html', vars(ctx))

    @method_decorator(login_required)
    def post(self, request):
        form = OrderDateForm(request.POST)
        form.is_valid()

        for ingredient in Ingredient.objects.all():
            raw_qty = request.POST.get(f'quantity_{ingredient.id}', '0')
            try:
                qty = int(raw_qty)
            except (ValueError, TypeError):
                qty = 0
            if qty > 0:
                IngredientOrder.objects.create(
                    date=form.cleaned_data['order_date'],
                    ingredient=ingredient,
                    quantity=qty,
                    cost=ingredient.cost,
                )

        return redirect('core:ingredients')


class SalesView(View):
    def get(self, request):
        past_sales = ItemSold.objects.select_related('item').order_by('-date', '-id')[:20]
        ctx = SalesContext(
            items=Item.objects.all().order_by('name'),
            past_sales=past_sales,
            today=date.today().isoformat(),
        )
        return render(request, 'core/sales.html', vars(ctx))

    @method_decorator(login_required)
    def post(self, request):
        form = SaleDateForm(request.POST)
        form.is_valid()
        sale_date = form.cleaned_data['sale_date']

        for item in Item.objects.all():
            raw_unit = request.POST.get(f'unit_qty_{item.id}', '0')
            raw_slice = request.POST.get(f'slice_qty_{item.id}', '0')
            try:
                unit_qty = Decimal(raw_unit)
            except Exception:
                unit_qty = Decimal('0')
            try:
                slice_qty = Decimal(raw_slice)
            except Exception:
                slice_qty = Decimal('0')

            quantity = unit_qty + slice_qty / item.servings_per_unit
            if quantity > 0:
                revenue = unit_qty * item.price_per_unit + slice_qty * item.price_per_serving
                ItemSold.objects.create(
                    date=sale_date,
                    item=item,
                    quantity=quantity,
                    price=round(revenue / quantity, 2),
                )

        return redirect('core:sales')


class ReportsView(View):
    def get(self, request):
        return render(request, 'core/reports.html', {
            'today': date.today().isoformat(),
        })

    def post(self, request):
        form = ReportDateForm(request.POST)
        form.is_valid()
        ing_start = form.cleaned_data['ing_start_date']
        ing_end = form.cleaned_data['ing_end_date']
        sales_start = form.cleaned_data['sales_start_date']
        sales_end = form.cleaned_data['sales_end_date']

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

        # Ingredient usage from items sold (with per-item breakdown)
        ingredient_usage = defaultdict(lambda: Decimal('0'))
        ingredient_item_usage = defaultdict(lambda: defaultdict(lambda: Decimal('0')))
        sold_items = (
            ItemSold.objects.filter(date__gte=sales_start, date__lte=sales_end)
            .values('item_id')
            .annotate(total_qty=Sum('quantity'))
        )
        for sold in sold_items:
            item_obj = Item.objects.get(id=sold['item_id'])
            item_ingredients = ItemIngredient.objects.filter(
                item_id=sold['item_id']
            ).select_related('ingredient')
            for ii in item_ingredients:
                usage_amount = round(ii.amount * Decimal(sold['total_qty']), 2)
                ingredient_usage[ii.ingredient.name] += usage_amount
                ingredient_item_usage[ii.ingredient.name][item_obj.name] += usage_amount

        # Build ingredient balance: ordered vs used vs remaining (all in base units)
        ordered_amounts = {}
        for o in orders:
            name = o['ingredient__name']
            ing = Ingredient.objects.get(name=name)
            conversion = CONVERSION_TO_BASE[ing.measurement_type]
            ordered_amounts[name] = {
                'ordered': o['total_qty'] * ing.measurement_amount * conversion,
                'unit': BASE_UNIT_MAP[ing.measurement_type],
            }

        all_names = sorted(set(list(ordered_amounts.keys()) + list(ingredient_usage.keys())))
        ingredient_balance = []
        for name in all_names:
            ordered = ordered_amounts.get(name, {}).get('ordered', Decimal('0'))
            unit = ordered_amounts.get(name, {}).get('unit', '')
            used = ingredient_usage.get(name, Decimal('0'))
            breakdown = []
            if used > 0 and name in ingredient_item_usage:
                for item_name, amount in sorted(ingredient_item_usage[name].items()):
                    pct = round(amount / used * 100)
                    breakdown.append(UsageBreakdown(item_name=item_name, amount=amount, percentage=pct))
            ingredient_balance.append(IngredientBalance(
                name=name,
                ordered=ordered,
                used=used,
                remaining=ordered - used,
                unit=unit,
                breakdown=breakdown,
            ))

        ctx = ReportContext(
            today=date.today().isoformat(),
            ing_start_date=ing_start.isoformat(),
            ing_end_date=ing_end.isoformat(),
            sales_start_date=sales_start.isoformat(),
            sales_end_date=sales_end.isoformat(),
            sales=sales,
            total_revenue=total_revenue,
            orders=orders,
            total_ingredient_cost=total_ingredient_cost,
            ingredient_balance=ingredient_balance,
            profit=total_revenue - total_ingredient_cost,
        )
        return render(request, 'core/reports.html', vars(ctx))
