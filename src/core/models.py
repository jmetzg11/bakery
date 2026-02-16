from django.db import models


MEASUREMENT_CHOICES = [
    ('g', 'grams'),
    ('kg', 'kilograms'),
    ('ml', 'milliliters'),
    ('l', 'liters'),
    ('cups', 'cups'),
    ('oz', 'ounces'),
    ('units', 'units'),
]


class Ingredient(models.Model):
    name = models.CharField(max_length=100)
    measurement_type = models.CharField(max_length=10, choices=MEASUREMENT_CHOICES)
    measurement_amount = models.DecimalField(max_digits=10, decimal_places=2)
    cost = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name


class Item(models.Model):
    name = models.CharField(max_length=100)
    servings_per_unit = models.IntegerField(default=1)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    price_per_serving = models.DecimalField(max_digits=10, decimal_places=2)
    ingredients = models.ManyToManyField(Ingredient, through='ItemIngredient')

    def ingredient_cost_per_unit(self):
        total = sum(
            (ii.amount / ii.ingredient.measurement_amount) * ii.ingredient.cost
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
    measurement_type = models.CharField(max_length=10, choices=MEASUREMENT_CHOICES)

    def __str__(self):
        return f"{self.item.name} - {self.ingredient.name} ({self.amount}{self.measurement_type})"


class IngredientOrder(models.Model):
    date = models.DateField()
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
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
