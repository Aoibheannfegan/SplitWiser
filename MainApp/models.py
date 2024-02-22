from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import F
# from django.utils.functional import SimpleLazyObject


class User(AbstractUser):
    pass

class PaymentGroup(models.Model):
    group_name = models.CharField(max_length=64)
    members = models.ManyToManyField('User', related_name='payment_groups', blank=True)

    def __str__(self):
        return self.group_name

class Friends(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="current_user")
    friends = models.ManyToManyField('User', related_name='friends', blank=True)


class Expense(models.Model):
    CURRENCY_CHOICES = [
        ('CAD', 'CAD - Canadian Dollar'),
        ('GBP', 'GBP - British Pound Sterling'),
        ('AUD', 'AUD - Australian Dollar'),
        ('EUR', 'EUR - Euro'),
        ('USD', 'USD - United States Dollar'),
    ]

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    remaining_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    description = models.CharField(max_length=100)
    date_added = models.DateTimeField(auto_now_add=True)
    payment_group = models.ForeignKey(PaymentGroup, on_delete=models.CASCADE, related_name="expenses",  null=True, blank=True)
    created_by_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_expenses")
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES)
    paid = models.BooleanField(default=False)
    # picture = models.ImageField(upload_to='your_model_pictures/', null=True, blank=True)

    def __str__(self):
        return self.description
    

class Owing(models.Model):
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name="sub_expenses")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="amounts_owed")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid = models.BooleanField(default=False)
    remaining_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return self.expense.description