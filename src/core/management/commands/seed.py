from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand

from core.models import Ingredient, IngredientOrder, Item, ItemIngredient, ItemSold


class Command(BaseCommand):
    help = 'Seed database with play data including historical price changes'

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
            measurement_amount=Decimal('1.00'), cost=Decimal('3.00'),
        )
        sugar = Ingredient.objects.create(
            name='Sugar', measurement_type='kg',
            measurement_amount=Decimal('1.00'), cost=Decimal('4.00'),
        )
        butter = Ingredient.objects.create(
            name='Butter', measurement_type='g',
            measurement_amount=Decimal('500.00'), cost=Decimal('5.00'),
        )
        eggs = Ingredient.objects.create(
            name='Eggs', measurement_type='units',
            measurement_amount=Decimal('12.00'), cost=Decimal('4.50'),
        )
        cocoa = Ingredient.objects.create(
            name='Cocoa Powder', measurement_type='g',
            measurement_amount=Decimal('250.00'), cost=Decimal('6.00'),
        )
        cream_cheese = Ingredient.objects.create(
            name='Cream Cheese', measurement_type='g',
            measurement_amount=Decimal('250.00'), cost=Decimal('3.50'),
        )
        vanilla = Ingredient.objects.create(
            name='Vanilla Extract', measurement_type='ml',
            measurement_amount=Decimal('100.00'), cost=Decimal('8.00'),
        )

        # --- Items ---
        chocolate_cake = Item.objects.create(
            name='Chocolate Cake', servings_per_unit=8,
            price_per_unit=Decimal('32.00'), price_per_serving=Decimal('4.00'),
        )
        ItemIngredient.objects.bulk_create([
            ItemIngredient(item=chocolate_cake, ingredient=flour, amount=Decimal('0.40'), measurement_type='kg'),
            ItemIngredient(item=chocolate_cake, ingredient=sugar, amount=Decimal('0.30'), measurement_type='kg'),
            ItemIngredient(item=chocolate_cake, ingredient=butter, amount=Decimal('200.00'), measurement_type='g'),
            ItemIngredient(item=chocolate_cake, ingredient=eggs, amount=Decimal('4.00'), measurement_type='units'),
            ItemIngredient(item=chocolate_cake, ingredient=cocoa, amount=Decimal('80.00'), measurement_type='g'),
            ItemIngredient(item=chocolate_cake, ingredient=vanilla, amount=Decimal('10.00'), measurement_type='ml'),
        ])

        cupcake = Item.objects.create(
            name='Cupcake', servings_per_unit=1,
            price_per_unit=Decimal('3.50'), price_per_serving=Decimal('3.50'),
        )
        ItemIngredient.objects.bulk_create([
            ItemIngredient(item=cupcake, ingredient=flour, amount=Decimal('0.05'), measurement_type='kg'),
            ItemIngredient(item=cupcake, ingredient=sugar, amount=Decimal('0.04'), measurement_type='kg'),
            ItemIngredient(item=cupcake, ingredient=butter, amount=Decimal('30.00'), measurement_type='g'),
            ItemIngredient(item=cupcake, ingredient=eggs, amount=Decimal('0.50'), measurement_type='units'),
            ItemIngredient(item=cupcake, ingredient=vanilla, amount=Decimal('2.00'), measurement_type='ml'),
        ])

        cheesecake = Item.objects.create(
            name='Cheesecake', servings_per_unit=10,
            price_per_unit=Decimal('45.00'), price_per_serving=Decimal('4.50'),
        )
        ItemIngredient.objects.bulk_create([
            ItemIngredient(item=cheesecake, ingredient=flour, amount=Decimal('0.15'), measurement_type='kg'),
            ItemIngredient(item=cheesecake, ingredient=sugar, amount=Decimal('0.25'), measurement_type='kg'),
            ItemIngredient(item=cheesecake, ingredient=butter, amount=Decimal('150.00'), measurement_type='g'),
            ItemIngredient(item=cheesecake, ingredient=eggs, amount=Decimal('5.00'), measurement_type='units'),
            ItemIngredient(item=cheesecake, ingredient=cream_cheese, amount=Decimal('500.00'), measurement_type='g'),
            ItemIngredient(item=cheesecake, ingredient=vanilla, amount=Decimal('15.00'), measurement_type='ml'),
        ])

        cookies = Item.objects.create(
            name='Cookie', servings_per_unit=1,
            price_per_unit=Decimal('2.00'), price_per_serving=Decimal('2.00'),
        )
        ItemIngredient.objects.bulk_create([
            ItemIngredient(item=cookies, ingredient=flour, amount=Decimal('0.03'), measurement_type='kg'),
            ItemIngredient(item=cookies, ingredient=sugar, amount=Decimal('0.02'), measurement_type='kg'),
            ItemIngredient(item=cookies, ingredient=butter, amount=Decimal('20.00'), measurement_type='g'),
            ItemIngredient(item=cookies, ingredient=eggs, amount=Decimal('0.25'), measurement_type='units'),
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
