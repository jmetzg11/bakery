from django.db import models


MEASUREMENT_CHOICES = [
    ('g', 'grams'),
    ('kg', 'kilograms'),
    ('ml', 'milliliters'),
    ('l', 'liters'),
    ('units', 'units'),
]

BASE_MEASUREMENT_CHOICES = [
    ('g', 'grams'),
    ('ml', 'milliliters'),
    ('units', 'units'),
]

CONVERSION_TO_BASE = {
    'kg': 1000,
    'g': 1,
    'l': 1000,
    'ml': 1,
    'units': 1,
}

BASE_UNIT_MAP = {
    'kg': 'g',
    'g': 'g',
    'l': 'ml',
    'ml': 'ml',
    'units': 'units',
}


class Ingredient(models.Model):
    name = models.CharField(max_length=100)
    measurement_type = models.CharField(max_length=10, choices=MEASUREMENT_CHOICES)
    measurement_amount = models.IntegerField()
    cost = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name


class Item(models.Model):
    name = models.CharField(max_length=100)
    servings_per_unit = models.IntegerField(default=1)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    price_per_serving = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sold_by_slice = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.price_per_serving is None and self.servings_per_unit:
            self.price_per_serving = round(self.price_per_unit / self.servings_per_unit, 2)
        super().save(*args, **kwargs)
    ingredients = models.ManyToManyField(Ingredient, through='ItemIngredient')

    def ingredient_cost_per_unit(self):
        total = sum(
            ii.amount * ii.ingredient.cost / (
                ii.ingredient.measurement_amount
                * CONVERSION_TO_BASE[ii.ingredient.measurement_type]
            )
            for ii in self.itemingredient_set.all()
        )
        return round(total, 2)

    def ingredient_cost_per_serving(self):
        if self.servings_per_unit == 0:
            return 0
        return round(self.ingredient_cost_per_unit() / self.servings_per_unit, 2)

    def __str__(self):
        return self.name


class ItemIngredient(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    measurement_type = models.CharField(max_length=10, choices=BASE_MEASUREMENT_CHOICES)

    def save(self, *args, **kwargs):
        self.measurement_type = BASE_UNIT_MAP.get(
            self.ingredient.measurement_type, self.ingredient.measurement_type
        )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.item.name} - {self.ingredient.name} ({self.amount}{self.measurement_type})"


class IngredientOrder(models.Model):
    date = models.DateField()
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    cost = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.date} - {self.ingredient.name} ({self.quantity} x ${self.cost})"


class ItemSold(models.Model):
    date = models.DateField()
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def total_revenue(self):
        return round(self.quantity * self.price, 2)

    def __str__(self):
        return f"{self.date} - {self.quantity}x {self.item.name}"
