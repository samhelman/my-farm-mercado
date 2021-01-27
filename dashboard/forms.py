from django import forms
import requests
from django.contrib.auth.models import User
from django.urls import reverse
from django.conf import settings
from rest_framework.authtoken.models import Token
from api.models import ListStatus
from django.core.exceptions import ValidationError

def generate_url(request, endpoint):
    prefix = "http://" if settings.DEBUG else "https://"
    url = f"{prefix}{request.get_host()}{reverse(endpoint)}"
    return url

class RegisterUserForm(forms.Form):
    username = forms.CharField(label="Username", max_length=100)
    email = forms.EmailField(label="Email")
    password = forms.CharField(max_length=32, widget=forms.PasswordInput)
    confirm_password = forms.CharField(max_length=32, widget=forms.PasswordInput)
    user_type = forms.BooleanField(
        label="Is Admin?",
        required=False
    )
    
    def clean(self):
        cleaned_data = super(RegisterUserForm, self).clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            self.add_error('confirm_password', "Password does not match")

        email = cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("That email is already in use.")

        return cleaned_data

class RegisterOrganisationForm(forms.Form):
    organisation_name = forms.CharField(label="Organisation Name", max_length=100)
    username = forms.CharField(label="Username", max_length=100)
    email = forms.EmailField(label="Email")
    password = forms.CharField(max_length=32, widget=forms.PasswordInput)
    confirm_password = forms.CharField(max_length=32, widget=forms.PasswordInput)
    
    def clean(self):
        cleaned_data = super(RegisterOrganisationForm, self).clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            self.add_error('confirm_password', "Password does not match")

        email = cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Email exists")

        return cleaned_data

class AddGroupForm(forms.Form):
    group_name = forms.CharField(label="Group Name", max_length=50)

class AddCustomItemForm(forms.Form):
    item_name = forms.CharField(label="Item Name", max_length=50)
    price = forms.DecimalField(required=False, label="Approximate Price:", max_digits=6, decimal_places=2, widget=forms.NumberInput(attrs={'placeholder': "Optional"}))

    def __init__(self, *args, **kwargs):
        request_object = kwargs.pop("request_object")
        super(AddCustomItemForm, self).__init__(*args, **kwargs)
        groups = self.get_groups(request_object)
        if groups:
            self.fields['group'] = forms.ChoiceField(label='Group', choices=[])
            self.fields['group'].choices = groups

    def get_groups(self, request):
        url = generate_url(request, 'api-get-groups')
        json = {
            "user_id": request.user.id
        }
        token, _ = Token.objects.get_or_create(user=request.user)
        headers = {
            'Authorization': f'Token {token}'
        }
        r = requests.post(url, headers=headers, json=json)
        group_tuples = []
        if r.status_code == 200:
            if r.json()['user_type'] == 'admin':
                groups = r.json()['groups']
                for group in groups:
                    group_tuples.append((group, group.capitalize()))
                group_tuples.insert(0, ("",""))
                return group_tuples
            else:
                return False

    def set_initial_values(self, item_name=None, price=None, group=None):
        self.fields['item_name'].initial = item_name.capitalize()
        self.fields['price'].initial = price
        if 'group' in self.fields:
            self.fields['group'].initial = group


class NewShoppingListForm(forms.Form):

    def __init__(self, *args, **kwargs):
        request_object = kwargs.pop("request_object")
        super(NewShoppingListForm, self).__init__()
        groups = self.get_groups(request_object)
        for group, items in groups.items():
            if len(items):
                choices = []
                for item in items:
                    item_name = item['item_name']
                    price = item['price']
                    if price:
                        choices.append(
                            (item_name, f"{item_name.capitalize()} ~${price}")
                        )
                    else:
                        choices.append(
                            (item_name, item_name.capitalize())
                        )
                self.fields[group] = forms.ChoiceField(label=group.upper(), widget=forms.CheckboxSelectMultiple, choices=choices)
        if len(args) > 0:
            post_data = dict(args[0])
            post_data.pop("csrfmiddlewaretoken")
            for group, items in post_data.items():
                self.initial[group] = items

    def get_groups(self, request):
        url = generate_url(request, 'api-get-shopping-list-items')
        json = {
            "user_id": request.user.id
        }
        token, _ = Token.objects.get_or_create(user=request.user)
        headers = {
            'Authorization': f'Token {token}'
        }
        r = requests.post(url, headers=headers, json=json)
        groups = {}
        if r.status_code == 200:
            groups = r.json()
        return groups

class ListDetailForm(forms.Form):
    price = forms.DecimalField(label="Add Price:", max_digits=6, decimal_places=2)
    status = forms.ChoiceField(choices=[], required=False)
    notes = forms.CharField(widget=forms.Textarea(attrs={'placeholder': "Optional"}), required=False)

    def __init__(self, *args, **kwargs):
        super(ListDetailForm, self).__init__(*args, **kwargs)
        self.fields['status'].choices = self._get_choices()
    
    def _get_choices(self):
        statuses = ListStatus.objects.all()
        choices = [ (status.label, status.label) for status in statuses ]
        return choices

class PaymentForm(forms.Form):
    payment = forms.DecimalField(label="Register Payment:", max_digits=6, decimal_places=2)