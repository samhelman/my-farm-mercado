import requests
from django.urls import reverse
from django.conf import settings
from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.contrib.auth.forms import UserCreationForm
from .forms import (
    RegisterUserForm, 
    RegisterOrganisationForm, 
    AddCustomItemForm, 
    AddGroupForm, 
    NewShoppingListForm,
    ListDetailForm,
    PaymentForm
)
from django.contrib.auth.models import User
from api.models import UserProfile
from rest_framework.authtoken.models import Token

"""
    - Base template view class that defines some shared methods
"""
class BaseView(TemplateView):

    # generate a url to make a request on the api endpoint
    def generate_url(self, request, endpoint):
        prefix = "http://" if settings.DEBUG else "https://"
        url = f"{prefix}{request.get_host()}{reverse(endpoint)}"
        return url

    # get the user type of the user making the request
    def get_user_type(self, request):
        user_id = request.user.id
        user = User.objects.filter(id=user_id).first()
        user_profile = UserProfile.objects.filter(user=user).first()
        user_type = user_profile.user_type
        return user_type

    # make a request of the given type to the api endpoint
    # **kwargs are the json payload of the request
    def make_request(self, request, endpoint, request_type, **kwargs):
        url = self.generate_url(request, endpoint)
        token, _ = Token.objects.get_or_create(user=request.user)
        headers = {
            'Authorization': f'Token {token}'
        }
        if request_type == 'POST':
            return requests.post(url, headers=headers, json=kwargs)
        else:
            return requests.get(url, headers=headers)

    # a decorator function that makes a request to the api to determine if a user has admin status
    # redirects non admin users to the dashboard home page
    def admin_status_required(func):
        def inner(*args):
            self = args[0]
            request = args[1]
            if not request.user.is_authenticated:
                return redirect('dashboard-login')
            else:
                url = self.generate_url(request, 'api-user-is-admin')
                json = {

                }
                token, _ = Token.objects.get_or_create(user=request.user)
                headers = {
                    'Authorization': f'Token {token}'
                }
                r = requests.post(url, headers=headers, json=json)
                if r.status_code == 200 and r.json()['is_admin']:
                    return func(self, request)
                else:
                    return redirect('dashboard-index')
        return inner

    # a decorator function that makes a request to the api to determine if a user has 'user status
    # redirects non 'user' users to the dashboard home page
    def user_status_required(func):
        def inner(*args):
            self = args[0]
            request = args[1]
            if not request.user.is_authenticated:
                return redirect('login')
            else:
                url = self.generate_url(request, 'api-user-is-admin')
                json = {

                }
                token, _ = Token.objects.get_or_create(user=request.user)
                headers = {
                    'Authorization': f'Token {token}'
                }
                r = requests.post(url, headers=headers, json=json)
                if r.status_code == 200 and r.json()['is_admin'] == False:
                    return func(self, request)
                else:
                    return redirect('dashboard-index')
        return inner

class IndexView(BaseView):
    template_name = 'dashboard/index.html'

    def get(self, request):
        
        if not request.user.is_authenticated:
            return redirect('login')
        user_profile = UserProfile.objects.get(user=request.user)
        context = {
            'main_selected': 'dashboard',
            'user_type': self.get_user_type(request)
        }
        return render(request, self.template_name, context=context)

class RegisterUserView(BaseView):
    template_name = 'dashboard/register-user.html'

    @BaseView.admin_status_required
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')
        context = {
            'main_selected': 'dashboard',
            'minor_selected': 'register_user',
            "form": RegisterUserForm,
            "user_type": self.get_user_type(request)
        }   
        return render(request, self.template_name, context=context)

    def post(self, request):
        form =  RegisterUserForm(request.POST)
        context = {
            'main_selected': 'dashboard',
            'minor_selected': 'register_user',
            "form": form,
            "user_type": self.get_user_type(request)
        }
    
        if form.is_valid():
            if form.cleaned_data['user_type']:
                user_type = 'admin'
            else:
                user_type = 'user'
            r = self.make_request(
                request,
                'api-register-user',
                'POST',
                admin_id=request.user.id,
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
                user_type=user_type
            )
            if r.status_code == 200:
                return redirect('dashboard-get-users')
            if r.status_code == 409:
                context['error'] = "A user with that username already exists."
            elif r.status_code == 400:
                context['error'] = "Something went wrong, please try again."
        elif form.errors:
            if '__all__' in dict(form.errors):
                context['error'] = dict(form.errors)['__all__'][0]
        return render(request, self.template_name, context=context)

class RegisterOrganisationView(BaseView):
    template_name = 'dashboard/register-organisation.html'

    def get(self, request):
        context = {
            'main_selected': 'register_organisation',
            "form": RegisterOrganisationForm,
        }   
        return render(request, self.template_name, context=context)

    def post(self, request):
        form =  RegisterOrganisationForm(request.POST)
        context = {
            'main_selected': 'register_organisation',
            "form": form,
        }
    
        if form.is_valid():
            r = self.make_request(
                request,
                'api-register-organisation',
                'POST',
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
                organisation_name=form.cleaned_data['organisation_name']
            )
            if r.status_code == 200:
                return redirect('dashboard-index')
            if r.status_code == 409:
                data = r.json()
                error_messages = []
                if data['user_exists']:
                    error_messages.append("A user with that username already exists.")
                if data['organisation_exists']:
                    error_messages.append("An organisation with that name already exists.")
                context['error'] = error_messages
            elif r.status_code == 400:
                context['error'] = ["Something went wrong, please try again."]
        elif form.errors:
            # get the first error to display
            if '__all__' in dict(form.errors):
                context['error'] = dict(form.errors)['__all__'][0]
        return render(request, self.template_name, context=context)

class GetAllUsers(BaseView):
    template_name = 'dashboard/users.html'

    def get(self, request):
        user_type = self.get_user_type(request)
        if user_type != 'admin':
            return redirect('dashboard-index')
        context = {
            'main_selected': 'dashboard',
            'minor_selected': 'view_users',
            'user_type': self.get_user_type(request)
        }
        r = self.make_request(
            request,
            'api-get-all-users',
            'GET'
        )
        if r.status_code == 200:
            users = r.json()['user_profiles']
            context['users'] = users
        elif r.status_code == 401:
            context['errors'] = r.json()['detail']
        else:
            context['errors'] = r.json()['detail']
        return render(request, self.template_name, context=context)

class ManageCustomItemsView(BaseView):
    template_name = 'dashboard/manage-custom-items.html'

    def get(self, request):
        context = {
            'main_selected': 'dashboard',
            'minor_selected': 'custom_items',
            'user_type': self.get_user_type(request)
        }
        r = self.make_request(
            request,
            'api-get-custom-items',
            'POST',
        )
        if r.status_code == 200:
            for group, items in r.json()['groups'].items():
                print(group)
            context["groups"] = r.json()['groups']
        elif r.status_code == 401:
            context['errors'] = r.json()['detail']
        else: 
            return redirect('dashboard-index')
        return render(request, self.template_name, context=context)

class AddCustomItemView(BaseView):
    template_name = 'dashboard/add-custom-item.html'

    def get(self, request):
        context = {
            'main_selected': 'dashboard',
            'minor_selected': 'custom_items',
            'user_type': self.get_user_type(request),
            'form': AddCustomItemForm(request_object=request)
        }
        return render(request, self.template_name, context=context)

    def post(self, request):
        form = AddCustomItemForm(request.POST, request_object=request)
        context = {
            'main_selected': 'dashboard',
            'minor_selected': 'custom_items',
            'form': form,
            "user_type": self.get_user_type(request)
        }
        if form.is_valid:
            r = self.make_request(
                request,
                'api-custom-items',
                'POST',
                item_name=form.data['item_name'],
                group_name=form.data['group'] if 'group' in form.data else None
            )
            if r.status_code == 200:
                return redirect('dashboard-manage-custom-items')
            elif r.status_code == 401:
                context['error'] = r.json()['detail']
            elif r.status_code == 409:
                context['error'] = r.json()['errors']
        return render(request, self.template_name, context=context)

class AddGroupView(BaseView):
    template_name = 'dashboard/add-custom-group.html'

    def get(self, request):
        form = AddGroupForm()
        context = {
            'main_selected': 'dashboard',
            'minor_selected': 'custom_items',
            'user_type': self.get_user_type(request),
            'form': form
        }
        return render(request, self.template_name, context=context)

    def post(self, request):
        form = AddGroupForm(request.POST)
        context = {
            'main_selected': 'dashboard',
            'minor_selected': 'custom_items',
            'form': form,
            "user_type": self.get_user_type(request)
        }

        if form.is_valid:
            r = self.make_request(
                request,
                'api-add-group',
                'POST',
                group_name=form.data['group_name']
            )
            if r.status_code == 200:
                return redirect('dashboard-manage-custom-items')
            elif r.status_code == 401:
                context['error'] = r.json()['detail']
            elif r.status_code == 409:
                context['error'] = r.json()['errors']
        return render(request, self.template_name, context=context)

class NewShoppingListView(BaseView):
    template_name = 'dashboard/new-shopping-list.html'

    @BaseView.user_status_required
    def get(self, request):
        context = {
            'main_selected': 'dashboard',
            'minor_selected': 'new_list',
            'form': NewShoppingListForm(request_object=request),
            'user_type': self.get_user_type(request)
        }
        for group, choices in context['form'].fields.items():
            print(group)
            print(choices.choices)
            for choice in choices.choices:
                print(choice)
            print('')
        return render(request, self.template_name, context=context)

    @BaseView.user_status_required
    def post(self, request):
        form = NewShoppingListForm(request.POST, request_object=request)
        context = {
            'main_selected': 'dashboard',
            'minor_selected': 'new_list',
            'form': form,
            'user_type': self.get_user_type(request)
        }
        form_data = dict(request.POST)
        form_data.pop('csrfmiddlewaretoken')
        if not form_data:
            context['error'] = "You must select at least one item before submitting."
            return render(request, self.template_name, context=context)
        if form.is_valid:
            r = self.make_request(
                request,
                'api-create-new-list',
                'POST',
                form_data=form_data
            )
            if r.status_code == 200:
                return redirect('dashboard-view-lists')
            elif r.status_code == 400:
                context['error'] = r.json()['detail']
            elif r.status_code == 401:
                context['error'] = r.json()['detail']
        return render(request, self.template_name, context=context)

class ListsView(BaseView):
    template_name = 'dashboard/view-lists.html'

    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')
        context = {
            'main_selected': 'dashboard',
            'minor_selected': 'view_lists',
            'user_type': self.get_user_type(request)
        }
        r = self.make_request(
            request,
            'api-get-lists',
            'POST'
        )
        if r.status_code == 200:
            data = r.json()['lists']
            context['data'] = data
        elif r.status_code == 400:
            context['errors'] = r.json()['detail']
        elif r.status_code == 401:
            context['errors'] = r.json()['detail']
        return render(request, self.template_name, context=context)

class ListDetailView(BaseView):
    template_name = 'dashboard/list-detail.html'

    def get(self, request, list_id, errors=False):
        if not request.user.is_authenticated:
            return redirect('login')
        user_type = self.get_user_type(request)
        context = {
            'main_selected': 'dashboard',
            'minor_selected': 'view_lists',
            'user_type': user_type
        }
        r = self.make_request(
            request,
            'api-list-detail',
            'POST',
            list_id=list_id
        )
        if r.status_code == 200:
            data = r.json()['list']
            context['data'] = data
            if user_type == 'admin':
                initial = {
                    'price': data['list_price'],
                    'status': data['list_status'],
                    'notes': data['list_notes']
                }
                form = ListDetailForm(initial=initial)
                context['form'] = form
                if errors:
                    context['errors'] = errors
        elif r.status_code == 400:
            context['errors'] = r.json()['detail']
        elif r.status_code == 401:
            context['errors'] = r.json()['detail']
        return render(request, self.template_name, context=context)

    def post(self, request, list_id):
        # update the shopping list
        user_type = self.get_user_type(request)
        context = {
            'main_selected': 'dashboard',
            'minor_selected': 'view_lists',
            'user_type': user_type
        }
        price = dict(request.POST)['price'][0]
        status = dict(request.POST)['status'][0]
        notes = dict(request.POST)['notes'][0]
        r = self.make_request(
            request,
            'api-update-list',
            'POST',
            list_id=list_id,
            price=price,
            status=status,
            notes=notes
        )
        errors = False
        if r.status_code == 200:
            pass
        elif r.status_code == 400:
            errors = r.json()['detail']
        elif r.status_code == 401:
            errors = r.json()['detail']
        return redirect('dashboard-list-detail', list_id=list_id)

class GenerateListView(BaseView):
    template_name = "dashboard/generate-list.html"

    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')
        user_type = self.get_user_type(request)
        context = {
            'main_selected': 'dashboard',
            'minor_selected': 'generate_list',
            'user_type': user_type
        }
        r = self.make_request(
            request,
            'api-generate-list',
            'POST',
        )
        if r.status_code == 200:
            list_items = r.json()['list_items']
            context['list_items'] = list_items
        elif r.status_code == 400:
            errors = r.json()['detail']
        elif r.status_code == 401:
            errors = r.json()['detail']
        return render(request, self.template_name, context=context)

class UserProfileView(BaseView):
    template_name = 'dashboard/user-profile.html'

    def get(self, request, user_id):
        if not request.user.is_authenticated:
            return redirect('login')
        user_type = self.get_user_type(request)
        context = {
            'main_selected': 'dashboard',
            'minor_selected': 'profile',
            'user_type': user_type,
            'form': PaymentForm() if user_type == 'admin' else None
        }
        r = self.make_request(
            request,
            'api-user-detail',
            'POST',
            user_id=user_id
        )
        if r.status_code == 200:
            profile = r.json()['profile']
            context['profile'] = profile
        elif r.status_code == 400:
            errors = r.json()['detail']
        elif r.status_code == 401:
            errors = r.json()['detail']
        return render(request, self.template_name, context=context)

    def post(self, request, user_id):
        payment = dict(request.POST)['payment'][0]
        r = self.make_request(
            request,
            'api-register-payment',
            'POST',
            user_id=user_id,
            payment=payment
        )
        if r.status_code == 200:
            pass
        elif r.status_code == 400:
            errors = r.json()['detail']
        elif r.status_code == 401:
            errors = r.json()['detail']
        return redirect('dashboard-user-detail', user_id=user_id)