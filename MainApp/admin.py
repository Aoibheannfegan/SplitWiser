from django.contrib import admin
from .models import Friends, PaymentGroup, Expense, Owing

# # Register your models here.
admin.site.register(PaymentGroup)
admin.site.register(Expense)
admin.site.register(Owing)
admin.site.register(Friends)