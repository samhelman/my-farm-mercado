from django.contrib import admin
from .models import (
    Organisation,
    UserProfile,
    ListStatus,
    ShoppingList,
    ShoppingListItem,
    UserCustomListOption,
    OrganisationCustomListGroup,
    OrganisationCustomListOption,
    Transaction
)

@admin.register(Organisation)
class AdminOrganisation(admin.ModelAdmin):
    pass

@admin.register(UserProfile)
class AdminUserProfile(admin.ModelAdmin):
    pass

@admin.register(ListStatus)
class AdminListStatus(admin.ModelAdmin):
    pass

@admin.register(ShoppingList)
class AdminShoppingList(admin.ModelAdmin):
    pass

@admin.register(ShoppingListItem)
class AdminShoppingListItem(admin.ModelAdmin):
    pass

@admin.register(UserCustomListOption)
class AdminUserCustomListOption(admin.ModelAdmin):
    pass

@admin.register(OrganisationCustomListGroup)
class AdminOrganisationCustomListGroup(admin.ModelAdmin):
    pass

@admin.register(OrganisationCustomListOption)
class AdminOrganisationCustomListOption(admin.ModelAdmin):
    pass

@admin.register(Transaction)
class AdminTransaction(admin.ModelAdmin):
    pass