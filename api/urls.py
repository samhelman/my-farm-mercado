from django.urls import path
from .views import (
    GetAllUsers, 
    RegisterUser, 
    RegisterOrganisation, 
    UserIsAdmin,  
    GetCustomItems,
    CustomItems,
    GetGroups,
    AddGroup,
    GetShoppingListItems,
    CreateNewShoppingList,
    GetLists,
    ListDetailView,
    UpdateList,
    GenerateList,
    UserDetail,
    RegisterPayment,
    GetCustomItem
)

urlpatterns = [
    path(GetAllUsers.endpoint_name, GetAllUsers.as_view(), name='api-get-all-users'),
    path(RegisterUser.endpoint_name, RegisterUser.as_view(), name='api-register-user'),
    path(RegisterOrganisation.endpoint_name, RegisterOrganisation.as_view(), name='api-register-organisation'),
    path(UserIsAdmin.endpoint_name, UserIsAdmin.as_view(), name='api-user-is-admin'),
    path(GetCustomItems.endpoint_name, GetCustomItems.as_view(), name='api-get-custom-items'),
    path(CustomItems.endpoint_name, CustomItems.as_view(), name='api-custom-items'),
    path(GetGroups.endpoint_name, GetGroups.as_view(), name='api-get-groups'),
    path(AddGroup.endpoint_name, AddGroup.as_view(), name='api-add-group'),
    path(GetShoppingListItems.endpoint_name, GetShoppingListItems.as_view(), name='api-get-shopping-list-items'),
    path(CreateNewShoppingList.endpoint_name, CreateNewShoppingList.as_view(), name='api-create-new-list'),
    path(GetLists.endpoint_name, GetLists.as_view(), name='api-get-lists'),
    path(ListDetailView.endpoint_name, ListDetailView.as_view(), name='api-list-detail'),
    path(UpdateList.endpoint_name, UpdateList.as_view(), name='api-update-list'),
    path(GenerateList.endpoint_name, GenerateList.as_view(), name='api-generate-list'),
    path(UserDetail.endpoint_name, UserDetail.as_view(), name='api-user-detail'),
    path(RegisterPayment.endpoint_name, RegisterPayment.as_view(), name='api-register-payment'),
    path(GetCustomItem.endpoint_name, GetCustomItem.as_view(), name='api-get-item')
]