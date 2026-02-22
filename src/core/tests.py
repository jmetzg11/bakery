from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from core.models import (
    CONVERSION_TO_BASE,
    Ingredient, IngredientOrder, Item, ItemIngredient, ItemSold,
)

# --- Ingredient config ---
FLOUR_TYPE = 'kg'
FLOUR_AMOUNT = 1       # 1kg bag
FLOUR_COST = Decimal('2.00')

BUTTER_TYPE = 'g'
BUTTER_AMOUNT = 500    # 500g pack
BUTTER_COST = Decimal('3.00')

EGGS_TYPE = 'units'
EGGS_AMOUNT = 12       # 12-egg carton
EGGS_COST = Decimal('4.00')

MILK_TYPE = 'l'
MILK_AMOUNT = 1        # 1L bottle
MILK_COST = Decimal('1.50')

# --- Item config ---
CAKE_SERVINGS = 8
CAKE_PRICE_UNIT = Decimal('20.00')
CAKE_PRICE_SLICE = Decimal('3.00')

CROISSANT_SERVINGS = 1
CROISSANT_PRICE_UNIT = Decimal('2.50')

# --- Recipes (base units: g, ml, units) ---
CAKE_FLOUR = Decimal('500')
CAKE_BUTTER = Decimal('200')
CAKE_EGGS = Decimal('4')
CAKE_MILK = Decimal('200')

CROISSANT_FLOUR = Decimal('100')
CROISSANT_BUTTER = Decimal('50')
CROISSANT_EGGS = Decimal('1')
CROISSANT_MILK = Decimal('50')

# --- Order quantities (number of packages) ---
ORDER_FLOUR = 5
ORDER_BUTTER = 5
ORDER_EGGS = 4
ORDER_MILK = 3

# --- Sales quantities ---
CAKE_UNITS_SOLD = Decimal('4')
CAKE_SLICES_SOLD = Decimal('8')
CROISSANT_UNITS_SOLD = Decimal('10')


class BakeryE2ETest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='baker', password='testpass')

        cls.flour = Ingredient.objects.create(
            name='Flour', measurement_type=FLOUR_TYPE,
            measurement_amount=FLOUR_AMOUNT, cost=FLOUR_COST,
        )
        cls.butter = Ingredient.objects.create(
            name='Butter', measurement_type=BUTTER_TYPE,
            measurement_amount=BUTTER_AMOUNT, cost=BUTTER_COST,
        )
        cls.eggs = Ingredient.objects.create(
            name='Eggs', measurement_type=EGGS_TYPE,
            measurement_amount=EGGS_AMOUNT, cost=EGGS_COST,
        )
        cls.milk = Ingredient.objects.create(
            name='Milk', measurement_type=MILK_TYPE,
            measurement_amount=MILK_AMOUNT, cost=MILK_COST,
        )

        cls.cake = Item.objects.create(
            name='Cake', servings_per_unit=CAKE_SERVINGS,
            price_per_unit=CAKE_PRICE_UNIT, price_per_serving=CAKE_PRICE_SLICE,
            sold_by_slice=True,
        )
        cls.croissant = Item.objects.create(
            name='Croissant', servings_per_unit=CROISSANT_SERVINGS,
            price_per_unit=CROISSANT_PRICE_UNIT,
            sold_by_slice=False,
        )

        for item, amounts in [
            (cls.cake, {'flour': CAKE_FLOUR, 'butter': CAKE_BUTTER, 'eggs': CAKE_EGGS, 'milk': CAKE_MILK}),
            (cls.croissant, {'flour': CROISSANT_FLOUR, 'butter': CROISSANT_BUTTER, 'eggs': CROISSANT_EGGS, 'milk': CROISSANT_MILK}),
        ]:
            for ing_name, amount in amounts.items():
                ItemIngredient.objects.create(
                    item=item, ingredient=getattr(cls, ing_name), amount=amount,
                )

    def test_full_order_sale_report_cycle(self):
        self.client.login(username='baker', password='testpass')

        # --- Step 1: Order ingredients ---
        resp = self.client.post('/ingredients/', {
            'order_date': '2026-02-15',
            f'quantity_{self.flour.id}': str(ORDER_FLOUR),
            f'quantity_{self.butter.id}': str(ORDER_BUTTER),
            f'quantity_{self.eggs.id}': str(ORDER_EGGS),
            f'quantity_{self.milk.id}': str(ORDER_MILK),
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(IngredientOrder.objects.count(), 4)

        for ing, qty, cost in [
            (self.flour, ORDER_FLOUR, FLOUR_COST),
            (self.butter, ORDER_BUTTER, BUTTER_COST),
            (self.eggs, ORDER_EGGS, EGGS_COST),
            (self.milk, ORDER_MILK, MILK_COST),
        ]:
            order = IngredientOrder.objects.get(ingredient=ing)
            self.assertEqual(order.quantity, qty)
            self.assertEqual(order.cost, cost)

        # --- Step 2: Record sales ---
        resp = self.client.post('/sales/', {
            'sale_date': '2026-02-15',
            f'unit_qty_{self.cake.id}': str(int(CAKE_UNITS_SOLD)),
            f'slice_qty_{self.cake.id}': str(int(CAKE_SLICES_SOLD)),
            f'unit_qty_{self.croissant.id}': str(int(CROISSANT_UNITS_SOLD)),
            f'slice_qty_{self.croissant.id}': '0',
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(ItemSold.objects.count(), 2)

        # Cake: quantity = units + slices/servings
        cake_qty = CAKE_UNITS_SOLD + CAKE_SLICES_SOLD / CAKE_SERVINGS
        cake_revenue = CAKE_UNITS_SOLD * CAKE_PRICE_UNIT + CAKE_SLICES_SOLD * CAKE_PRICE_SLICE
        cake_price = round(cake_revenue / cake_qty, 2)

        cake_sale = ItemSold.objects.get(item=self.cake)
        self.assertEqual(cake_sale.quantity, cake_qty)
        self.assertEqual(cake_sale.price, cake_price)

        # Croissant: just units
        croissant_qty = CROISSANT_UNITS_SOLD
        croissant_sale = ItemSold.objects.get(item=self.croissant)
        self.assertEqual(croissant_sale.quantity, croissant_qty)
        self.assertEqual(croissant_sale.price, CROISSANT_PRICE_UNIT)

        # --- Step 3: Generate report ---
        resp = self.client.post('/reports/', {
            'ing_start_date': '2026-02-01',
            'ing_end_date': '2026-02-28',
            'sales_start_date': '2026-02-01',
            'sales_end_date': '2026-02-28',
        })
        self.assertEqual(resp.status_code, 200)
        ctx = resp.context

        # Revenue
        total_revenue = cake_qty * cake_price + croissant_qty * CROISSANT_PRICE_UNIT
        self.assertEqual(ctx['total_revenue'], total_revenue)

        # Ingredient costs
        flour_cost = ORDER_FLOUR * FLOUR_COST
        butter_cost = ORDER_BUTTER * BUTTER_COST
        eggs_cost = ORDER_EGGS * EGGS_COST
        milk_cost = ORDER_MILK * MILK_COST
        total_cost = flour_cost + butter_cost + eggs_cost + milk_cost
        self.assertEqual(ctx['total_ingredient_cost'], total_cost)

        orders_by_name = {o['ingredient__name']: o for o in ctx['orders']}
        self.assertEqual(orders_by_name['Flour']['total_cost'], flour_cost)
        self.assertEqual(orders_by_name['Butter']['total_cost'], butter_cost)
        self.assertEqual(orders_by_name['Eggs']['total_cost'], eggs_cost)
        self.assertEqual(orders_by_name['Milk']['total_cost'], milk_cost)

        # Profit
        self.assertEqual(ctx['profit'], total_revenue - total_cost)

        # Ingredient balance
        balance = {b.name: b for b in ctx['ingredient_balance']}

        # ordered = packages * package_amount * conversion_to_base
        # used = recipe_amount * cake_qty + recipe_amount * croissant_qty
        for name, ing_type, ing_amount, order_qty, cake_recipe, croissant_recipe in [
            ('Flour', FLOUR_TYPE, FLOUR_AMOUNT, ORDER_FLOUR, CAKE_FLOUR, CROISSANT_FLOUR),
            ('Butter', BUTTER_TYPE, BUTTER_AMOUNT, ORDER_BUTTER, CAKE_BUTTER, CROISSANT_BUTTER),
            ('Eggs', EGGS_TYPE, EGGS_AMOUNT, ORDER_EGGS, CAKE_EGGS, CROISSANT_EGGS),
            ('Milk', MILK_TYPE, MILK_AMOUNT, ORDER_MILK, CAKE_MILK, CROISSANT_MILK),
        ]:
            ordered = order_qty * ing_amount * CONVERSION_TO_BASE[ing_type]
            used_cake = cake_recipe * cake_qty
            used_croissant = croissant_recipe * croissant_qty
            used = round(used_cake + used_croissant, 2)
            remaining = ordered - used

            b = balance[name]
            self.assertEqual(b.ordered, ordered, f'{name} ordered')
            self.assertEqual(b.used, used, f'{name} used')
            self.assertEqual(b.remaining, remaining, f'{name} remaining')

            # Usage breakdown
            bd = {bd.item_name: bd for bd in b.breakdown}
            self.assertEqual(bd['Cake'].amount, round(used_cake, 2), f'{name} cake usage')
            self.assertEqual(bd['Croissant'].amount, round(used_croissant, 2), f'{name} croissant usage')
