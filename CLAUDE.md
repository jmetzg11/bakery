# Bakery Management App

A Django app for a Croatian bakery to track ingredient purchases, item sales, and generate profit reports.

## Tech Stack
- **Backend**: Django 6.0, Python 3.14, PostgreSQL 17
- **Frontend**: Django templates + Tailwind CSS (CDN) + htmx
- **Package manager**: uv
- **DB**: PostgreSQL via Docker Compose

## Running the App
- `make run` — starts Postgres (Docker), runs migrations, creates admin superuser (admin/admin), starts dev server
- `make seed` — populates DB with sample bakery data (ingredients, items, orders, sales)
- `make stop` — tears down Docker containers

## Project Structure
```
src/
  bakery/          # Django project config (settings, root urls)
  core/            # Main app
    models.py      # Ingredient, Item, ItemIngredient, IngredientOrder, ItemSold
    views.py       # Class-based views (HomeView, IngredientsView, SalesView, ReportsView)
    urls.py        # Routes: /, /ingredients/, /sales/, /reports/
    admin.py       # Custom admin with inline ItemIngredient, dynamic unit display
    templates/core/ # base.html, home.html, ingredients.html, sales.html, reports.html
    management/commands/seed.py  # Seed data command
  templates/admin/  # Admin template overrides (index.html, item change_form.html)
```

## Data Model
- **Ingredient** — name, measurement_type (g/kg/ml/l/units), measurement_amount (int), cost
- **Item** — name, servings_per_unit, price_per_unit, price_per_serving (optional, auto-calculates if blank)
- **ItemIngredient** — links Item to Ingredient with amount; measurement_type auto-set on save (kg→g, l→ml, units→units)
- **IngredientOrder** — date, ingredient, quantity (int), cost (snapshot from ingredient at time of order)
- **ItemSold** — date, item, quantity (int), price (snapshot from item.price_per_serving at time of sale)

## Key Design Decisions
- **Measurement units**: only g, kg, ml, l, units. ItemIngredient always stores in base units (g, ml, units)
- **Currency**: Euros (€), this is a Croatian bakery
- **Color scheme**: Red/white/blue (Croatian flag colors), not brown/amber
- **Auth**: POST endpoints (submit orders, record sales) require login. Forms are hidden from anonymous users. Admin link only visible when logged in.
- **Reports**: Separate date ranges for ingredient orders and sales (ingredients may be ordered days before sales)
- **Tables**: Sortable columns via client-side JS (handles dates, numbers, strings)
- **History tables**: Limited to 20 most recent entries
- **Home page**: Shows latest order per ingredient and latest sale per item (one row each, not full history)
- **price_per_serving**: Optional field on Item. If left blank, auto-calculates as price_per_unit / servings_per_unit on save. Can be overridden (e.g. cake slices sold at markup).
- **Admin**: Auth section hidden. "Back to Bakery Site" link on admin index. Item inline shows dynamic Unit column via JS.

## Pages
- **/** — Home: two tables showing most recent order per ingredient and most recent sale per item, with totals
- **/ingredients/** — Order form (auth only) + recent purchases table
- **/sales/** — Sales recording form (auth only) + recent sales table
- **/reports/** — Date range picker (separate for ingredients/sales), generates profit report with revenue, costs, ingredient balance (ordered vs used vs remaining)
- **/admin/** — Django admin for managing Ingredients, Items, IngredientOrders, ItemsSold
