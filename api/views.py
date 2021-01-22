import requests
from time import sleep
from django.http import JsonResponse
from django.db import IntegrityError
from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from .models import Organisation
from django.forms.models import model_to_dict
from decimal import Decimal
from .models import (
    UserProfile,
    OrganisationCustomListGroup,
    OrganisationCustomListOption,
    UserCustomListOption,
    ListStatus,
    ShoppingList,
    ShoppingListItem,
    Transaction
)
from transmission.helpers import log_api_error
from rest_framework.authtoken.models import Token
from datetime import datetime

class GetAllUsers(APIView):
    endpoint_name = "get-all-users/"

    def get(self, request):
        try:
            request_user = User.objects.filter(auth_token=request.auth).first()
            request_user_profile = UserProfile.objects.filter(user=request_user).first()
            request_user_type = request_user_profile.user_type
            request_user_organisation = request_user_profile.organisation
            if not request_user_type == 'admin':
                response_content = {
                    'detail': "You are not authorised to view this page."
                }
                return Response(response_content, status=status.HTTP_401_UNAUTHORIZED)
            data = {
                "user_profiles": []
            }
            user_profiles = UserProfile.objects.all()
            for user_profile in user_profiles:
                if request_user_organisation == user_profile.organisation:
                    user = User.objects.filter(username=user_profile.user).first()
                    user_data = {
                        "auth_info": {
                            "user_id": user.id,
                            "username": user.username,
                            "email": user.email
                        },
                        "organisation": str(user_profile.organisation),
                        "user_type": str(user_profile.user_type)
                    }
                    data["user_profiles"].append(user_data)
            return JsonResponse(data)
        
        except Exception as e:
            log_api_error(
                error=str(e),
                endpoint=self.endpoint_name,
            )
            content = {
                'error': str(e),
                'detail': "Something went wrong processing your request."
            }
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

class RegisterUser(APIView):
    endpoint_name = "register-user/"

    def post(self, request):
        try:
            username = request.data['username']
            email = request.data['email']
            password = request.data['password']
            admin_id = request.data['admin_id']
            organisation = UserProfile.objects.get(id=admin_id).organisation
            user_type = request.data['user_type']

            user = User.objects.create_user(
                username=username,
                password=password,
                email=email
            )
            
            user_profile = UserProfile.objects.create(
                user=user,
                organisation=organisation,
                user_type=user_type
            )
            user.save()
            user_profile.save()
            json_response = {
                "success": True,
                "user": model_to_dict(user_profile)
            }
            return JsonResponse(json_response)
        except IntegrityError as e:
            log_api_error(
                error=str(e),
                endpoint=self.endpoint_name,
            )
            content = {
                "success": False,
                "error": str(e),
            }
            return Response(content, status=status.HTTP_409_CONFLICT)
        except Exception as e:
            log_api_error(
                error=str(e),
                endpoint=self.endpoint_name,
            )

            content = {
                "success": False,
                "error": str(e)
            }
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

class RegisterOrganisation(APIView):
    endpoint_name = "register-organisation/"

    def generate_organisation_defaults(self, organisation):
        default_groups = {
            'Fruit': [
                'Bananas',
                'Apples',
                'Oranges',
            ],
            'Vegetables': [
                'Peppers',
                'Onion',
                'Tomato',
                'Lettuce'
            ],
            'Beans': [
                'Black Beans',
                'Navy Beans'
            ],
            'Bread': [
                'White Bread',
                'Whole Wheat Bread',
            ],
            'Grains': [
                'White Rice',
                'Brown Rice'
                'Pasta'
                'Whole Wheat Pasta'
            ],
            'Meat': [
                'Pork',
                'Chicken',
                'Rotisserie Chicken',
                'Ground Beef'
            ],
            'Dairy': [
                'Cheese',
                'Milk',
                'Eggs'
            ],
            'Drinks': [
                'Coke',
                'Sprite',
                'Water'
            ],
            'Cleaning Supplies': [
                'Soap',
                'Laundry Detergent'
            ],
            'Other': [
                'Sugar'
            ]
        }
        for group_name, group_items in default_groups.items():
            OrganisationCustomListGroup.objects.create(organisation=organisation, group_name=group_name)
            group = OrganisationCustomListGroup.objects.get(organisation=organisation, group_name=group_name)
            for item_name in group_items:
                OrganisationCustomListOption.objects.create(organisation=organisation, group=group, item_name=item_name)

    def post(self, request):
        try:
            username = request.data['username']
            email = request.data['email']
            password = request.data['password']
            organisation_name = request.data['organisation_name']

            user = User(username=username, email=email)
            user.set_password(password)

            organisation = Organisation(organisation_name=organisation_name)

            user_profile = UserProfile(user=user, organisation=organisation, user_type='admin')

            # check if user or organisation already exist in db
            user_exists = len(User.objects.filter(username=username)) > 0
            organisation_exists = len(Organisation.objects.filter(organisation_name=organisation_name)) > 0
            
            if user_exists or organisation_exists:
                content = {
                    "success": False,
                    'user_exists': True if user_exists else False,
                    'organisation_exists': True if organisation_exists else False,
                }
                return Response(content, status=status.HTTP_409_CONFLICT)
            else:
                # save changes and create default organisation settings            
                user.save()
                organisation.save()
                user_profile.save()
                self.generate_organisation_defaults(organisation)

            json_response = {
                "success": True,
                "user": model_to_dict(user_profile),
                "organisation": model_to_dict(organisation)
            }
            return JsonResponse(json_response)
        except Exception as e:
            log_api_error(
                error=str(e),
                endpoint=self.endpoint_name,
            )
            content = {
                "success": False,
                "error": str(e)
            }
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

class UserIsAdmin(APIView):
    endpoint_name = "user-is-admin/"

    def post(self, request):
        try:
            content = {
                "is_admin": False,
            }
            user = User.objects.filter(auth_token=request.auth).first()
            user_profile = UserProfile.objects.filter(user=user).first()
            if user_profile.is_admin():
                content['is_admin'] = True
            return JsonResponse(content)
        except Exception as e:
            log_api_error(
                error=str(e),
                endpoint=self.endpoint_name,
            )
            
            content = {
                'error': str(e),
                'detail': "Something went wrong processing your request."
            }
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

class GetUserType(APIView):
    endpoint_name = "get-user-type/"

    def post(self, request):
        try:
            user = User.objects.filter(username=username).first()
            user_profile = UserProfile.objects.filter(user=user).first()
            user_type = user_profile.user_type
            content = {
                'user_type': user_type
            }
            return JsonResponse(content)
        except Exception as e:
            log_api_error(
                error=str(e),
                endpoint=self.endpoint_name,
            )
            
            content = {
                'error': str(e),
                'detail': "Something went wrong processing your request."
            }
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

class GetCustomItems(APIView):
    endpoint_name = "get-custom-items/"

    def post(self, request):
        try:
            user = User.objects.filter(auth_token=request.auth).first()
            user_profile = UserProfile.objects.filter(user=user).first()
            user_type = user_profile.user_type
            organisation = user_profile.organisation
            
            return_data = {}
            if user_type == 'admin':
                groups = OrganisationCustomListGroup.objects.filter(organisation=organisation)
                for group in groups:
                    group_data = []
                    items = OrganisationCustomListOption.objects.filter(organisation=organisation, group=group)
                    for item in items:
                        data = {
                            'item_name': item.item_name
                        }
                        group_data.append(data)
                    return_data[group.group_name] = group_data
            elif user_type == 'user':
                items = UserCustomListOption.objects.filter(user=user)
                group_data = []
                for item in items:
                    data = {
                        'item_name': item.item_name
                    }
                    group_data.append(data)
                return_data['Custom Items'] = group_data

            content = {
                "groups": return_data
            }
            return JsonResponse(content)
        
        except Exception as e:
            log_api_error(
                error=str(e),
                endpoint=self.endpoint_name,
            )
            
            content = {
                'error': str(e),
                'detail': "Something went wrong processing your request."
            }
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

class CustomItems(APIView):
    endpoint_name = "custom-items/"

    def post(self, request):
        try:
            item_name = request.data['item_name'].lower()
            user = User.objects.filter(auth_token=request.auth).first()
            user_profile = UserProfile.objects.filter(user=user).first()
            user_type = user_profile.user_type
            organisation = user_profile.organisation
            
            if user_type == 'admin':
                # check all organisation custom items for existing item with the same item name
                is_duplicate = len(OrganisationCustomListOption.objects.filter(item_name=item_name, organisation=organisation)) > 0

                group_name = request.data['group_name'].lower()
                group = OrganisationCustomListGroup.objects.filter(group_name=group_name, organisation=organisation).first()
                # create organisation custom item
                item = OrganisationCustomListOption(item_name=item_name, organisation=organisation, group=group)
            elif user_type == 'user':
                # check all user custom items for existing item with the same item name
                is_duplicate = len(UserCustomListOption.objects.filter(item_name=item_name, user=user)) > 0

                # create user custom item
                item = UserCustomListOption(item_name=item_name, user=user)
            if is_duplicate:
                content = {
                    "success": False,
                    "errors": "An item with this name already exists."
                }
                return Response(content, status=status.HTTP_409_CONFLICT)
            item.save()
            content = {
                "item_name": item_name
            }
            return JsonResponse(content)

        except Exception as e:
            log_api_error(
                error=str(e),
                endpoint=self.endpoint_name,
            )
            
            content = {
                'error': str(e),
                'detail': "Something went wrong processing your request."
            }
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

class AddGroup(APIView):
    endpoint_name = "add-group/"

    def post(self, request):
        try:
            group_name = request.data['group_name'].lower()
            user = User.objects.filter(auth_token=request.auth).first()
            user_profile = UserProfile.objects.filter(user=user).first()
            user_type = user_profile.user_type
            organisation = user_profile.organisation
            
            if user_type == 'admin':
                # check all organisation custom groups for existing group with the same group name
                is_duplicate = len(OrganisationCustomListGroup.objects.filter(group_name=group_name, organisation=organisation)) > 0

                # create organisation custom group
                group = OrganisationCustomListGroup(group_name=group_name, organisation=organisation)
            if is_duplicate:
                content = {
                    "success": False,
                    "errors": "An group with this name already exists."
                }
                return Response(content, status=status.HTTP_409_CONFLICT)
            group.save()
            content = {
                "group_name": group_name
            }
            return JsonResponse(content)

        except Exception as e:
            log_api_error(
                error=str(e),
                endpoint=self.endpoint_name,
            )
            
            content = {
                'error': str(e),
                'detail': "Something went wrong processing your request."
            }
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

class GetGroups(APIView):
    endpoint_name = "get-groups/"

    def post(self, request):
        try:
            user = User.objects.filter(auth_token=request.auth).first()
            user_profile = UserProfile.objects.filter(user=user).first()
            user_type = user_profile.user_type

            content = {}
            if user_type == 'admin':

                organisation = user_profile.organisation

                groups = OrganisationCustomListGroup.objects.filter(organisation=organisation)

                return_groups = []
                for group in groups:
                    return_groups.append(group.group_name)
                content['groups'] = return_groups

            content['user_type'] = user_type
            return JsonResponse(content)
        
        except Exception as e:
            log_api_error(
                error=str(e),
                endpoint=self.endpoint_name,
            )
            
            content = {
                'error': str(e),
                'detail': "Something went wrong processing your request."
            }
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

class GetShoppingListItems(APIView):
    endpoint_name = "get-shopping-list-items/"

    def post(self, request):
        try:
            user = User.objects.filter(auth_token=request.auth).first()
            user_profile = UserProfile.objects.filter(user=user).first()
            organisation = user_profile.organisation

            content = {}

            organisation_groups = OrganisationCustomListGroup.objects.filter(organisation=organisation)
            for group in organisation_groups:
                query = OrganisationCustomListOption.objects.filter(group=group)
                group_custom_items = [{'item_name': item.item_name} for item in query]
                content[group.group_name] = group_custom_items
            
            user_custom_items_query = UserCustomListOption.objects.filter(user=user)
            user_custom_items = [{'item_name': item.item_name} for item in user_custom_items_query]
            content['user custom items'] = user_custom_items

            return JsonResponse(content)
        
        except Exception as e:
            log_api_error(
                error=str(e),
                endpoint=self.endpoint_name,
            )
            
            content = {
                'error': str(e),
                'detail': "Something went wrong processing your request."
            }
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

class CreateNewShoppingList(APIView):
    endpoint_name = "create-new-list/"

    def post(self, request):
        try:
            form_data = request.data['form_data']
            user = User.objects.filter(auth_token=request.auth).first()
            user_profile = UserProfile.objects.filter(user=user).first()
            organisation = user_profile.organisation
            
            shopping_list = ShoppingList(user=user, status=ListStatus.objects.get(rank=0).label, time_created=datetime.now())
            shopping_list_items = []
            for group, items in form_data.items():
                for item_name in items:
                    shopping_list_item = ShoppingListItem(shopping_list=shopping_list, item_name=item_name)
                    shopping_list_items.append(shopping_list_item)

            shopping_list.save()
            for shopping_list_item in shopping_list_items:
                shopping_list_item.save()
            response_content = {
                "success": True
            }
            return JsonResponse(response_content)

        except Exception as e:
            log_api_error(
                error=str(e),
                endpoint=self.endpoint_name,
            )
            
            content = {
                'error': str(e),
                'detail': "Something went wrong processing your request."
            }
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

class GetLists(APIView):
    endpoint_name = 'get-lists/'

    def post(self, request):
        try:
            user = User.objects.filter(auth_token=request.auth).first()
            user_profile = UserProfile.objects.filter(user=user).first()
            user_type = user_profile.user_type
            organisation = user_profile.organisation

            response_content = {
                'lists': {}
            }
            if user_type == 'admin':
                # users = list of all users at the admin's organisation
                users = []
                user_query = User.objects.all()
                for _user in user_query:
                    _user_profile = UserProfile.objects.filter(user=_user).first()
                    if _user_profile.organisation == organisation:
                        users.append(_user)
            elif user_type == 'user':
                users = [user]
            for user in users:
                username = user.username
                user_list_data = []
                shopping_lists = ShoppingList.objects.order_by('-time_created').filter(user=user)
                for shopping_list in shopping_lists:
                    list_id = shopping_list.id
                    list_name = str(shopping_list)
                    list_price = shopping_list.price if shopping_list.price else None
                    list_status = shopping_list.status if shopping_list.status else None
                    data = {
                        'list_id': list_id,
                        'list_name': list_name,
                        'list_price': list_price,
                        'list_status': list_status
                    }
                    user_list_data.append(data)
                response_content['lists'][username] = user_list_data

            return JsonResponse(response_content)
        except Exception as e:
            log_api_error(
                error=str(e),
                endpoint=self.endpoint_name,
            )
            
            content = {
                'error': str(e),
                'detail': "Something went wrong processing your request."
            }
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

class ListDetailView(APIView):
    endpoint_name = "list-detail/"

    def post(self, request):
        try:
            list_id = request.data['list_id']
            user = User.objects.filter(auth_token=request.auth).first()
            user_profile = UserProfile.objects.filter(user=user).first()
            user_type = user_profile.user_type
            organisation = user_profile.organisation

            shopping_list = ShoppingList.objects.filter(id=list_id).first()
            shopping_list_owner = shopping_list.user
            shopping_list_owner_profile = UserProfile.objects.filter(user=shopping_list_owner).first()
            shopping_list_owner_organisation = shopping_list_owner_profile.organisation
            authorised = False # default to unauthorised
            if user_type == 'admin' and shopping_list_owner_organisation == organisation:
                authorised = True
            elif user_type == 'user' and shopping_list_owner == user:
                authorised = True

            if authorised:
                shopping_list_items = ShoppingListItem.objects.filter(shopping_list=shopping_list)
                
                list_id = shopping_list.id
                list_name = str(shopping_list)
                list_price = shopping_list.price if shopping_list.price else None
                list_status = shopping_list.status if shopping_list.status else None
                
                list_items = []
                for item in shopping_list_items:
                    list_items.append(item.item_name)

                list_notes = shopping_list.notes if shopping_list.notes else None

                list_data = {
                    'list_id': list_id,
                    'list_name': list_name,
                    'list_price': list_price,
                    'list_status': list_status,
                    'list_items': list_items,
                    'list_notes': list_notes
                }

                response_content = {
                    'list': list_data
                }
                
                return JsonResponse(response_content)
            else:
                response_content = {
                    'detail': "You are not authorised to view this page."
                }
                return Response(response_content, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            log_api_error(
                error=str(e),
                endpoint=self.endpoint_name,
            )
            
            content = {
                'error': str(e),
                'detail': "Something went wrong processing your request."
            }
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

class UpdateList(APIView):
    endpoint_name = "update-list/"

    def post(self, request):
        try:
            user = User.objects.filter(auth_token=request.auth).first()
            user_profile = UserProfile.objects.filter(user=user).first()
            user_type = user_profile.user_type
            organisation = user_profile.organisation
            return_content = {}
            list_id = request.data['list_id']
            price = request.data['price']
            list_status = request.data['status']
            notes = request.data['notes']
            shopping_list = ShoppingList.objects.filter(id=list_id).first()
            shopping_list_user = shopping_list.user
            shopping_list_user_profile = UserProfile.objects.filter(user=shopping_list_user).first()
            shopping_list_user_organisation = shopping_list_user_profile.organisation
            if user_type == 'admin' and organisation == shopping_list_user_organisation:
                transaction = None
                if shopping_list.price == None:
                    transaction = Transaction(
                        user=shopping_list_user, 
                        transaction_amount=Decimal(price), 
                        transaction_datetime=datetime.now(),
                        detail="List price added."
                    )
                elif shopping_list.price != Decimal(price):
                    difference = Decimal(price) - shopping_list.price
                    transaction = Transaction(
                        user=shopping_list_user, 
                        transaction_amount=difference, 
                        transaction_datetime=datetime.now(),
                        detail=f"List price updated. Old price: ${shopping_list.price}, New price: ${Decimal(price)}, Difference: ${difference}"
                    )
                shopping_list.price = Decimal(price)
                shopping_list.notes = notes
                db_rank = ListStatus.objects.get(label=shopping_list.status).rank
                list_rank = ListStatus.objects.get(label=list_status).rank
                if db_rank < list_rank:
                    shopping_list.status = list_status
                if transaction:
                    transaction.save()
                shopping_list.save()
                return JsonResponse(return_content)
            else:
                response_content = {
                    'detail': "You are not authorised to view this page."
                }
                return Response(response_content, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            log_api_error(
                error=str(e),
                endpoint=self.endpoint_name,
            )
            
            content = {
                'error': str(e),
                'detail': "Something went wrong processing your request."
            }
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

class GenerateList(APIView):
    endpoint_name = "generate-list/"

    def post(self, request):
        try:
            user = User.objects.filter(auth_token=request.auth).first()
            user_profile = UserProfile.objects.filter(user=user).first()
            user_organisation = user_profile.organisation
            user_type = user_profile.user_type
            if user_type != 'admin':
                response_content = {
                    'detail': "You are not authorised to view this page."
                }
                return Response(response_content, status=status.HTTP_401_UNAUTHORIZED)
            response_content = {
                'list_items': {}
            }
            shopping_lists = ShoppingList.objects.filter(status=ListStatus.objects.get(rank=0).label)
            for shopping_list in shopping_lists:
                
                shopping_list_owner = shopping_list.user
                shopping_list_owner_profile = UserProfile.objects.filter(user=shopping_list_owner).first()
                shopping_list_owner_organisation = shopping_list_owner_profile.organisation
                if user_organisation == shopping_list_owner_organisation:
                    list_items = [item.item_name for item in ShoppingListItem.objects.filter(shopping_list=shopping_list)]
                    list_items = list(dict.fromkeys(list_items)) # remove duplicates
                    for item in list_items:
                        if item not in response_content['list_items'].keys():
                            response_content['list_items'][item] = 0
                        response_content['list_items'][item] += 1
            return JsonResponse(response_content)
        except Exception as e:
            log_api_error(
                error=str(e),
                endpoint=self.endpoint_name,
            )
            
            content = {
                'error': str(e),
                'detail': "Something went wrong processing your request."
            }
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

class UserDetail(APIView):
    endpoint_name = 'user-detail/'

    def post(self, request):
        try:
            user = User.objects.get(auth_token=request.auth)
            user_profile = UserProfile.objects.filter(user=user).first()
            user_organisation = user_profile.organisation
            user_type = user_profile.user_type

            user_id = request.data['user_id']
            user_detail_user = User.objects.get(id=user_id)
            user_detail_profile = UserProfile.objects.get(user=user_detail_user)
            user_detail_organisation = user_detail_profile.organisation

            authorised = False
            if user_type == 'admin' and user_organisation == user_detail_organisation:
                authorised = True
            if user_type == 'user' and user_profile == user_detail_profile:
                authorised = True
            if not authorised:
                response_content = {
                    'detail': "You are not authorised to view this page."
                }
                return Response(response_content, status=status.HTTP_401_UNAUTHORIZED)

            user_info = {
                'user_id': user_detail_user.id,
                'username': user_detail_user.username,
                'email': user_detail_user.email or "n/a"
            }
            user_lists = ShoppingList.objects.filter(user=user_detail_user)
            list_data = [
                {
                    'list_name': str(user_list), 
                    'list_id': user_list.id,
                    'status': user_list.status
                } 
                for user_list in user_lists
            ]
            transactions = Transaction.objects.filter(user=user_detail_user).order_by('-transaction_datetime')
            transaction_history = [
                {
                    'user': transaction.user.username,
                    'datetime': transaction.transaction_datetime.strftime("%Y-%m-%d %H:%M"),
                    'amount': transaction.transaction_amount,
                    'detail': transaction.detail
                }
                for transaction in transactions
            ]
            balance = 0
            for transaction in transactions:
                balance += transaction.transaction_amount
            user_info['balance'] = balance
            response_content = {
                'profile': {
                    'user_info': user_info,
                    'list_data': list_data,
                    'transaction_history': transaction_history
                }
            }
            return JsonResponse(response_content)
        except Exception as e:
            log_api_error(
                error=str(e),
                endpoint=self.endpoint_name,
            )
            
            content = {
                'error': str(e),
                'detail': "Something went wrong processing your request."
            }
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

class RegisterPayment(APIView):
    endpoint_name = 'register-payment/'

    def post(self, request):
        try:
            admin_user = User.objects.get(auth_token=request.auth)
            admin_user_profile = UserProfile.objects.filter(user=admin_user).first()
            admin_user_organisation = admin_user_profile.organisation
            admin_user_type = admin_user_profile.user_type

            list_user = User.objects.get(id=request.data['user_id'])
            list_user_profile = UserProfile.objects.filter(user=list_user).first()
            list_user_organisation = list_user_profile.organisation

            if admin_user_type == 'admin' and admin_user_organisation == list_user_organisation:
                payment = request.data['payment']
                transaction = Transaction(
                    user=list_user, 
                    transaction_amount=-Decimal(payment), 
                    transaction_datetime=datetime.now(),
                    detail="Payment made."
                )
                transaction.save()
                response_content = {

                }
                return JsonResponse(response_content)
            else:
                content = {
                    'detail': "You are not authorised to view this page."
                }
                return Response(content, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            log_api_error(
                error=str(e),
                endpoint=self.endpoint_name,
            )
            
            content = {
                'error': str(e),
                'detail': "Something went wrong processing your request."
            }
            return Response(content, status=status.HTTP_400_BAD_REQUEST)