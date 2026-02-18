from datetime import date

from django import forms


class OrderDateForm(forms.Form):
    order_date = forms.DateField(required=False)

    def clean_order_date(self):
        return self.cleaned_data.get('order_date') or date.today()


class SaleDateForm(forms.Form):
    sale_date = forms.DateField(required=False)

    def clean_sale_date(self):
        return self.cleaned_data.get('sale_date') or date.today()


class ReportDateForm(forms.Form):
    ing_start_date = forms.DateField(required=False)
    ing_end_date = forms.DateField(required=False)
    sales_start_date = forms.DateField(required=False)
    sales_end_date = forms.DateField(required=False)

    def clean_ing_start_date(self):
        return self.cleaned_data.get('ing_start_date') or date.today().replace(day=1)

    def clean_ing_end_date(self):
        return self.cleaned_data.get('ing_end_date') or date.today()

    def clean_sales_start_date(self):
        return self.cleaned_data.get('sales_start_date') or date.today().replace(day=1)

    def clean_sales_end_date(self):
        return self.cleaned_data.get('sales_end_date') or date.today()
