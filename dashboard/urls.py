from django.urls import path
from .views import (
    IndexView, 
    RegisterUserView, 
    RegisterOrganisationView, 
    GetAllUsers,
    UserProfileView,
    ManageCustomItemsView,
    AddCustomItemView,
    AddGroupView,
    NewShoppingListView,
    ListsView,
    ListDetailView,
    GenerateListView
)

urlpatterns = [
    path('', IndexView.as_view(), name='dashboard-index'),
    path('register-user/', RegisterUserView.as_view(), name='dashboard-register-user'),
    path('register-organisation/', RegisterOrganisationView.as_view(), name='dashboard-register-organisation'),
    path('users/', GetAllUsers.as_view(), name='dashboard-get-users'),
    path('users/<int:user_id>', UserProfileView.as_view(), name='dashboard-user-detail'),
    path('manage-custom-items/', ManageCustomItemsView.as_view(), name='dashboard-manage-custom-items'),
    path('add-custom-item/', AddCustomItemView.as_view(), name='dashboard-add-custom-item'),
    path('add-custom-item/<int:item_id>/', AddCustomItemView.as_view(), name='dashboard-edit-custom-item'),
    path('add-group/', AddGroupView.as_view(), name='dashboard-add-group'),
    path('new-shopping-list/', NewShoppingListView.as_view(), name='dashboard-new-shopping-list'),
    path('lists/', ListsView.as_view(), name='dashboard-view-lists'),
    path('lists/<int:list_id>/', ListDetailView.as_view(), name='dashboard-list-detail'),
    path('generate-list/', GenerateListView.as_view(), name='dashboard-generate-list'),
]