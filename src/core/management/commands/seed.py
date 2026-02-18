from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand

from core.models import Ingredient, IngredientOrder, Item, ItemIngredient, ItemSold


class Command(BaseCommand):
    help = 'Seed database with play data including historical price changes'

    def _create_recipe(self, item, ingredients):
        """Create ItemIngredient records using .create() so save() runs."""
        for ing, amount in ingredients:
            ItemIngredient.objects.create(item=item, ingredient=ing, amount=amount)

    def handle(self, *args, **options):
        self.stdout.write('Clearing existing data...')
        ItemSold.objects.all().delete()
        IngredientOrder.objects.all().delete()
        ItemIngredient.objects.all().delete()
        Item.objects.all().delete()
        Ingredient.objects.all().delete()

        # --- Ingredients (initial prices) ---
        flour = Ingredient.objects.create(
            name='Flour', measurement_type='kg',
            measurement_amount=1, cost=Decimal('3.00'),
        )
        sugar = Ingredient.objects.create(
            name='Sugar', measurement_type='kg',
            measurement_amount=1, cost=Decimal('4.00'),
        )
        butter = Ingredient.objects.create(
            name='Butter', measurement_type='g',
            measurement_amount=500, cost=Decimal('5.00'),
        )
        eggs = Ingredient.objects.create(
            name='Eggs', measurement_type='units',
            measurement_amount=12, cost=Decimal('4.50'),
        )
        cocoa = Ingredient.objects.create(
            name='Cocoa Powder', measurement_type='g',
            measurement_amount=250, cost=Decimal('6.00'),
        )
        cream_cheese = Ingredient.objects.create(
            name='Cream Cheese', measurement_type='g',
            measurement_amount=250, cost=Decimal('3.50'),
        )
        vanilla = Ingredient.objects.create(
            name='Vanilla Extract', measurement_type='ml',
            measurement_amount=100, cost=Decimal('8.00'),
        )

        # --- Items (amounts in base units: g, ml, units) ---
        chocolate_cake = Item.objects.create(
            name='Chocolate Cake', servings_per_unit=8,
            price_per_unit=Decimal('32.00'), price_per_serving=Decimal('5.00'),
            sold_by_slice=True,
        )
        self._create_recipe(chocolate_cake, [
            (flour, Decimal('400')),
            (sugar, Decimal('300')),
            (butter, Decimal('200')),
            (eggs, Decimal('4')),
            (cocoa, Decimal('80')),
            (vanilla, Decimal('10')),
        ])

        cupcake = Item.objects.create(
            name='Cupcake', servings_per_unit=1,
            price_per_unit=Decimal('3.50'),
        )
        self._create_recipe(cupcake, [
            (flour, Decimal('50')),
            (sugar, Decimal('40')),
            (butter, Decimal('30')),
            (eggs, Decimal('0.50')),
            (vanilla, Decimal('2')),
        ])

        cheesecake = Item.objects.create(
            name='Cheesecake', servings_per_unit=10,
            price_per_unit=Decimal('45.00'), price_per_serving=Decimal('4.50'),
            sold_by_slice=True,
        )
        self._create_recipe(cheesecake, [
            (flour, Decimal('150')),
            (sugar, Decimal('250')),
            (butter, Decimal('150')),
            (eggs, Decimal('5')),
            (cream_cheese, Decimal('500')),
            (vanilla, Decimal('15')),
        ])

        cookies = Item.objects.create(
            name='Cookie', servings_per_unit=1,
            price_per_unit=Decimal('2.00'),
        )
        self._create_recipe(cookies, [
            (flour, Decimal('30')),
            (sugar, Decimal('20')),
            (butter, Decimal('20')),
            (eggs, Decimal('0.25')),
        ])

        # --- Ingredient purchases (restocking) ---
        self.stdout.write('Creating ingredient orders...')
        ingredient_orders = [
            # October 2025 - initial stock
            (date(2025, 10, 1), flour, 5, Decimal('3.00')),
            (date(2025, 10, 1), sugar, 3, Decimal('4.00')),
            (date(2025, 10, 1), butter, 10, Decimal('5.00')),
            (date(2025, 10, 1), eggs, 5, Decimal('4.50')),
            (date(2025, 10, 1), cocoa, 4, Decimal('6.00')),
            (date(2025, 10, 1), cream_cheese, 6, Decimal('3.50')),
            (date(2025, 10, 1), vanilla, 3, Decimal('8.00')),
            # November 2025 restock
            (date(2025, 11, 1), flour, 6, Decimal('3.00')),
            (date(2025, 11, 1), sugar, 4, Decimal('4.00')),
            (date(2025, 11, 1), butter, 12, Decimal('5.00')),
            (date(2025, 11, 1), eggs, 6, Decimal('4.50')),
            (date(2025, 11, 1), cocoa, 3, Decimal('6.00')),
            (date(2025, 11, 1), cream_cheese, 8, Decimal('3.50')),
            (date(2025, 11, 1), vanilla, 2, Decimal('8.00')),
            # December 2025 restock (prices went up)
            (date(2025, 12, 1), flour, 8, Decimal('3.50')),
            (date(2025, 12, 1), sugar, 5, Decimal('4.00')),
            (date(2025, 12, 1), butter, 15, Decimal('6.50')),
            (date(2025, 12, 1), eggs, 8, Decimal('5.50')),
            (date(2025, 12, 1), cocoa, 5, Decimal('6.00')),
            (date(2025, 12, 1), cream_cheese, 10, Decimal('3.50')),
            (date(2025, 12, 1), vanilla, 4, Decimal('8.00')),
            # January 2026 restock
            (date(2026, 1, 2), flour, 7, Decimal('3.50')),
            (date(2026, 1, 2), sugar, 4, Decimal('4.00')),
            (date(2026, 1, 2), butter, 12, Decimal('6.50')),
            (date(2026, 1, 2), eggs, 7, Decimal('5.50')),
            (date(2026, 1, 2), cocoa, 4, Decimal('6.00')),
            (date(2026, 1, 2), cream_cheese, 8, Decimal('3.50')),
            (date(2026, 1, 2), vanilla, 3, Decimal('8.00')),
        ]
        for order_date, ingredient, qty, cost in ingredient_orders:
            IngredientOrder.objects.create(
                date=order_date, ingredient=ingredient,
                quantity=qty, cost=cost,
            )

        # --- Items sold ---
        self.stdout.write('Creating items sold...')
        items_sold = [
            # October 2025
            (date(2025, 10, 2), chocolate_cake, 8, Decimal('4.00')),
            (date(2025, 10, 5), cupcake, 12, Decimal('3.50')),
            (date(2025, 10, 8), cheesecake, 10, Decimal('4.50')),
            (date(2025, 10, 12), cookies, 20, Decimal('2.00')),
            (date(2025, 10, 15), chocolate_cake, 16, Decimal('4.00')),
            (date(2025, 10, 20), cupcake, 8, Decimal('3.50')),
            (date(2025, 10, 25), cheesecake, 5, Decimal('4.50')),
            # November 2025
            (date(2025, 11, 1), chocolate_cake, 8, Decimal('4.00')),
            (date(2025, 11, 3), cookies, 30, Decimal('2.00')),
            (date(2025, 11, 8), cupcake, 15, Decimal('3.50')),
            (date(2025, 11, 14), cheesecake, 20, Decimal('4.50')),
            (date(2025, 11, 18), chocolate_cake, 24, Decimal('4.00')),
            (date(2025, 11, 22), cookies, 25, Decimal('2.00')),
            (date(2025, 11, 28), cupcake, 10, Decimal('3.50')),
            # December 2025
            (date(2025, 12, 2), chocolate_cake, 16, Decimal('4.00')),
            (date(2025, 12, 5), cupcake, 20, Decimal('3.50')),
            (date(2025, 12, 10), cheesecake, 15, Decimal('4.50')),
            (date(2025, 12, 14), cookies, 40, Decimal('2.00')),
            (date(2025, 12, 18), chocolate_cake, 24, Decimal('4.00')),
            (date(2025, 12, 22), cheesecake, 10, Decimal('4.50')),
            (date(2025, 12, 28), cupcake, 15, Decimal('3.50')),
            # January 2026
            (date(2026, 1, 3), chocolate_cake, 8, Decimal('4.00')),
            (date(2026, 1, 6), cookies, 35, Decimal('2.00')),
            (date(2026, 1, 10), cupcake, 18, Decimal('3.50')),
            (date(2026, 1, 15), cheesecake, 20, Decimal('4.50')),
            (date(2026, 1, 20), chocolate_cake, 16, Decimal('4.00')),
            (date(2026, 1, 25), cookies, 20, Decimal('2.00')),
            (date(2026, 1, 30), cupcake, 12, Decimal('3.50')),
        ]
        for sale_date, item, qty, price in items_sold:
            ItemSold.objects.create(
                date=sale_date, item=item,
                quantity=qty, price=price,
            )

        self.stdout.write(self.style.SUCCESS(
            f'Seeded: {Ingredient.objects.count()} ingredients, '
            f'{Item.objects.count()} items, '
            f'{IngredientOrder.objects.count()} ingredient orders, '
            f'{ItemSold.objects.count()} items sold'
        ))
