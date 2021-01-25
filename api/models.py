from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
from datetime import datetime

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)

class Organisation(models.Model):
    organisation_name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.organisation_name

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=10)
    is_first_login = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user} - {self.organisation}"

    def is_admin(self):
        return self.user_type == 'admin'

class ListStatus(models.Model):
    label = models.CharField(max_length=50)
    rank = models.IntegerField()

    def __str__(self):
        return f"{self.rank} - {self.label}"

class ShoppingList(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=6, decimal_places=2, null=True)
    time_created = models.DateTimeField()
    notes = models.TextField(null=True)

    def __str__(self):
        return f"{self.user}'s List: {self.id}"

class ShoppingListItem(models.Model):
    shopping_list = models.ForeignKey(ShoppingList, on_delete=models.CASCADE)
    item_name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.item_name} - {self.shopping_list}"

class UserCustomListOption(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item_name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.item_name} - {self.user}"

class OrganisationCustomListGroup(models.Model):
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE)
    group_name = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.group_name} - {self.organisation}"

class OrganisationCustomListOption(models.Model):
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE)
    item_name = models.CharField(max_length=100)
    group = models.ForeignKey(OrganisationCustomListGroup, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return f"{self.item_name} - {self.organisation}"

class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    transaction_datetime = models.DateTimeField()
    transaction_amount = models.DecimalField(max_digits=6, decimal_places=2, null=True)
    detail = models.CharField(max_length=150)

    def __str__(self):
        return f"{self.user} - {self.transaction_amount} - {self.transaction_datetime}"