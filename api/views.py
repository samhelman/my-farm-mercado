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

"""
    - Endpoint gets a list of all users and returns them
    - Only admin users can access this data
    - They can only access the information for users at their organisation
"""
class GetAllUsers(APIView):
    endpoint_name = "get-all-users/"

    def get(self, request):
        try:
            # get user profile information of the user making the request
            request_user = User.objects.filter(auth_token=request.auth).first()
            request_user_profile = UserProfile.objects.filter(user=request_user).first()
            request_user_type = request_user_profile.user_type
            request_user_organisation = request_user_profile.organisation

            # only admin users are authourised to view this information
            if not request_user_type == 'admin':
                response_content = {
                    'detail': "You are not authorised to view this page."
                }
                return Response(response_content, status=status.HTTP_401_UNAUTHORIZED)
            
            data = {
                "user_profiles": []
            }
            # get all user profiles
            user_profiles = UserProfile.objects.all()
            for user_profile in user_profiles:
                # filter out users based on the request user's profile organisation
                if request_user_organisation == user_profile.organisation:
                    # get user information and add to return content data
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

"""
    - Create a user object
    - Create a user profile
"""
class RegisterUser(APIView):
    endpoint_name = "register-user/"

    def post(self, request):
        try:
            # get registration data from json
            username = request.data['username']
            email = request.data['email']
            password = request.data['password']
            admin_id = request.data['admin_id']
            user_type = request.data['user_type']

            # get the organisation object from the requesting user's admin id
            organisation = UserProfile.objects.get(id=admin_id).organisation

            # create user object
            user = User(
                username=username,
                email=email
            )
            user.set_password(password)
            
            # create user profile
            user_profile = UserProfile(
                user=user,
                organisation=organisation,
                user_type=user_type
            )

            # save user and user_profile
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

"""
    - Create a new organisation
    - Create the first admin user for the organisation
    - Set the default organisation custom groups and items
"""
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
                'Brown Rice',
                'Pasta',
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
        # create a list of default list items when the new organisation is created
        for group_name, group_items in default_groups.items():
            OrganisationCustomListGroup.objects.create(organisation=organisation, group_name=group_name)
            group = OrganisationCustomListGroup.objects.get(organisation=organisation, group_name=group_name)
            for item_name in group_items:
                OrganisationCustomListOption.objects.create(organisation=organisation, group=group, item_name=item_name)

    def post(self, request):
        try:
            # get registartion information from json
            username = request.data['username']
            email = request.data['email']
            password = request.data['password']
            organisation_name = request.data['organisation_name']

            # create new admin user
            user = User(username=username, email=email)
            user.set_password(password)

            # create new organisation
            organisation = Organisation(organisation_name=organisation_name)
            
            # create new user profile
            user_profile = UserProfile(user=user, organisation=organisation, user_type='admin')

            # check if user or organisation already exist in db
            user_exists = len(User.objects.filter(username=username)) > 0
            organisation_exists = len(Organisation.objects.filter(organisation_name=organisation_name)) > 0
            
            if user_exists or organisation_exists:
                # return 409 if user or organisation already exists
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

"""
    - Check if the requesting user is an admin user
"""
class UserIsAdmin(APIView):
    endpoint_name = "user-is-admin/"

    def post(self, request):
        try:
            # default to false
            content = {
                "is_admin": False,
            }
            # get user and user_profile objects from auth token
            user = User.objects.filter(auth_token=request.auth).first()
            user_profile = UserProfile.objects.filter(user=user).first()
            if user_profile.is_admin():
                # if user is an admin user return true
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

"""
    - Get a list of all custom items:
    - If the user is an admin user, get the organisation's items
    - If the user is a user user, get their personal custom items
"""
class GetCustomItems(APIView):
    endpoint_name = "get-custom-items/"

    def post(self, request):
        try:
            # get user profile information using auth token
            user = User.objects.filter(auth_token=request.auth).first()
            user_profile = UserProfile.objects.filter(user=user).first()
            user_type = user_profile.user_type
            organisation = user_profile.organisation
            
            return_data = {}
            if user_type == 'admin':
                # get all of this user's organisation's custom item groups
                groups = OrganisationCustomListGroup.objects.filter(organisation=organisation)
                for group in groups:
                    group_data = []
                    # get all custom items for this organisation's group and add to return content
                    items = OrganisationCustomListOption.objects.filter(organisation=organisation, group=group)
                    for item in items:
                        data = {
                            'item_id': item.id,
                            'item_name': item.item_name,
                            'price': item.price
                        }
                        group_data.append(data)
                    # add the group and child items to return data
                    return_data[group.group_name] = group_data
            elif user_type == 'user':
                # get all this user's custom items and add to return data
                items = UserCustomListOption.objects.filter(user=user)
                group_data = []
                for item in items:
                    data = {
                        'item_id': item.id,
                        'item_name': item.item_name,
                        'price': item.price
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

"""
    - Create a new custom item
"""
class CustomItems(APIView):
    endpoint_name = "custom-items/"

    def post(self, request):
        # try:
            # get item name and price from request data and convert to lower case
            item_id = request.data['item_id']
            item_name = request.data['item_name'].lower()
            price = request.data['price']

            # get user profile information using auth token
            user = User.objects.filter(auth_token=request.auth).first()
            user_profile = UserProfile.objects.filter(user=user).first()
            user_type = user_profile.user_type
            organisation = user_profile.organisation
            
            if user_type == 'admin':
                group_name = request.data['group_name'].lower()
                group = OrganisationCustomListGroup.objects.filter(group_name=group_name, organisation=organisation).first()
                if item_id:
                    # updating so is not a duplicate creation
                    is_duplicate = False

                    # update an existing item
                    existing_item = OrganisationCustomListOption.objects.get(id=item_id)
                    if item_name:
                        existing_item.item_name = item_name
                    if price:
                        existing_item.price = price
                    if group:
                        existing_item.group = group
                    
                    existing_item.save()
                else:
                    # check all organisation custom items for existing item with the same item name
                    is_duplicate = len(OrganisationCustomListOption.objects.filter(item_name=item_name, organisation=organisation)) > 0

                    # create organisation custom item
                    item = OrganisationCustomListOption(item_name=item_name, organisation=organisation, group=group)
                    if price:
                        item.price = Decimal(price)
                    item.save()
            elif user_type == 'user':
                if item_id:
                    # updating so is not a duplicate creation
                    is_duplicate = False

                    # update an existing item
                    existing_item = UserCustomListOption.objects.get(id=item_id)
                    if item_name:
                        existing_item.item_name = item_name
                    if price:
                        existing_item.price = price
                    existing_item.save()
                else:
                    # check all user custom items for existing item with the same item name
                    is_duplicate = len(UserCustomListOption.objects.filter(item_name=item_name, user=user)) > 0

                    # create user custom item
                    item = UserCustomListOption(item_name=item_name, user=user)
                    if price:
                        item.price = Decimal(price)
                    item.save()
            if is_duplicate:
                content = {
                    "success": False,
                    "errors": "An item with this name already exists."
                }
                return Response(content, status=status.HTTP_409_CONFLICT)
            content = {
                "item_name": item_name
            }
            return JsonResponse(content)

        # except Exception as e:
        #     log_api_error(
        #         error=str(e),
        #         endpoint=self.endpoint_name,
        #     )
            
        #     content = {
        #         'error': str(e),
        #         'detail': "Something went wrong processing your request."
        #     }
        #     return Response(content, status=status.HTTP_400_BAD_REQUEST)

"""
    - Add a new custom group to the organisation's custom items
"""
class AddGroup(APIView):
    endpoint_name = "add-group/"

    def post(self, request):
        try:
            # get group name from request data and convert to lowercase
            group_name = request.data['group_name'].lower()

            # get user profile information using auth token.
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

"""
    - Endpoint to help build the add group form for admin users.
"""
class GetGroups(APIView):
    endpoint_name = "get-groups/"

    def post(self, request):
        try:
            # get request user profile information from auth token
            user = User.objects.filter(auth_token=request.auth).first()
            user_profile = UserProfile.objects.filter(user=user).first()
            user_type = user_profile.user_type

            content = {}
            if user_type == 'admin':

                organisation = user_profile.organisation

                # get all groups for the request user's organisation and add to response data
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

"""
    - Get a list of all shopping list items available to a user for the purpose of populating the new list form
"""
class GetShoppingListItems(APIView):
    endpoint_name = "get-shopping-list-items/"

    def post(self, request):
        try:
            # get request user's profile from auth token
            user = User.objects.filter(auth_token=request.auth).first()
            user_profile = UserProfile.objects.filter(user=user).first()
            organisation = user_profile.organisation
            
            # initialise response json
            content = {}

            # get all groups from the request user's organisation
            organisation_groups = OrganisationCustomListGroup.objects.filter(organisation=organisation)
            for group in organisation_groups:
                # get all the custom items for each group and add them to the response content
                query = OrganisationCustomListOption.objects.filter(group=group)
                group_custom_items = [{'item_name': item.item_name, 'price': item.price} for item in query]
                content[group.group_name] = group_custom_items
            
            # get all request user's custom items and add to response content
            user_custom_items_query = UserCustomListOption.objects.filter(user=user)
            user_custom_items = [{'item_name': item.item_name, 'price': item.price} for item in user_custom_items_query]
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

"""
    - Create a new shopping list
"""
class CreateNewShoppingList(APIView):
    endpoint_name = "create-new-list/"

    def post(self, request):
        try:
            # get shopping list data from request
            form_data = request.data['form_data']

            # get request user's profile information using auth token
            user = User.objects.filter(auth_token=request.auth).first()
            user_profile = UserProfile.objects.filter(user=user).first()
            organisation = user_profile.organisation
            
            # create a new shopping list object
            shopping_list = ShoppingList(user=user, status=ListStatus.objects.get(rank=0).label, time_created=datetime.now())

            # create new objects for each list item
            shopping_list_items = []
            for group, items in form_data.items():
                for item_name in items:
                    shopping_list_item = ShoppingListItem(shopping_list=shopping_list, item_name=item_name)
                    shopping_list_items.append(shopping_list_item)

            # save shopping list and items
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

"""
    - Get all shopping lists a user is authorised to view
"""
class GetLists(APIView):
    endpoint_name = 'get-lists/'

    def post(self, request):
        try:
            # get request user profile info using auth token
            user = User.objects.filter(auth_token=request.auth).first()
            user_profile = UserProfile.objects.filter(user=user).first()
            user_type = user_profile.user_type
            organisation = user_profile.organisation

            # initialise respose json
            response_content = {
                'lists': {}
            }
            if user_type == 'admin':
                # users = list of all users at the requesting admin's organisation
                users = []
                # get all user objects
                user_query = User.objects.all()
                for _user in user_query:
                    # get the user's profile and add them to the users list if their organisation matches the requesting admin's
                    _user_profile = UserProfile.objects.filter(user=_user).first()
                    if _user_profile.organisation == organisation:
                        users.append(_user)
            elif user_type == 'user':
                # if the requesting user is not 'admin', they are only authorized to view their own information.
                users = [user]
            for user in users:
                username = user.username
                user_list_data = []
                # get all a user's shopping lists
                shopping_lists = ShoppingList.objects.order_by('-time_created').filter(user=user)
                for shopping_list in shopping_lists:
                    # get the list information and append the list dictionary to the user list data list
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
                # add the list of user's shopping lists to the response object using their username as a key
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

"""
    - Get the data for one list if user is authorised
"""
class ListDetailView(APIView):
    endpoint_name = "list-detail/"

    def post(self, request):
        try:
            # get list id from the request data
            list_id = request.data['list_id']

            # get the request user's profile info using auth token
            user = User.objects.filter(auth_token=request.auth).first()
            user_profile = UserProfile.objects.filter(user=user).first()
            user_type = user_profile.user_type
            organisation = user_profile.organisation

            # get the shopping list using the list id
            shopping_list = ShoppingList.objects.filter(id=list_id).first()
            # identify the user that is the author of the shoppig list
            shopping_list_owner = shopping_list.user
            # get that user's profile
            shopping_list_owner_profile = UserProfile.objects.filter(user=shopping_list_owner).first()
            shopping_list_owner_organisation = shopping_list_owner_profile.organisation
            authorised = False # default to unauthorised
            if user_type == 'admin' and shopping_list_owner_organisation == organisation:
                # an admin user is only authorised to see the lists of users at their own organisation
                authorised = True
            elif user_type == 'user' and shopping_list_owner == user:
                # a 'user' user can only view their own list
                authorised = True

            if authorised:
                # get all the items from the shopping list
                shopping_list_items = ShoppingListItem.objects.filter(shopping_list=shopping_list)
                
                # get the list data and append it to the response json
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

"""
    - Admin users can update the price, status and add notes to a list
"""
class UpdateList(APIView):
    endpoint_name = "update-list/"

    def post(self, request):
        try:
            # get the request user's profile info using auth token
            user = User.objects.filter(auth_token=request.auth).first()
            user_profile = UserProfile.objects.filter(user=user).first()
            user_type = user_profile.user_type
            organisation = user_profile.organisation

            # initialise response content json
            return_content = {}

            # pull info from request data
            list_id = request.data['list_id']
            price = request.data['price']
            list_status = request.data['status']
            notes = request.data['notes']

            # get the shopping list using list id
            shopping_list = ShoppingList.objects.filter(id=list_id).first()
            # identify the user that is the author of the list
            shopping_list_user = shopping_list.user
            shopping_list_user_profile = UserProfile.objects.filter(user=shopping_list_user).first()
            shopping_list_user_organisation = shopping_list_user_profile.organisation
            if user_type == 'admin' and organisation == shopping_list_user_organisation:
                transaction = None
                if shopping_list.price == None:
                    # if the db price value is not set, add a price
                    transaction = Transaction(
                        user=shopping_list_user, 
                        transaction_amount=Decimal(price), 
                        transaction_datetime=datetime.now(),
                        detail="List price added."
                    )
                elif shopping_list.price != Decimal(price):
                    # if the db list price is different than the form price, register the difference
                    difference = Decimal(price) - shopping_list.price
                    transaction = Transaction(
                        user=shopping_list_user, 
                        transaction_amount=difference, 
                        transaction_datetime=datetime.now(),
                        detail=f"List price updated. Old price: ${shopping_list.price}, New price: ${Decimal(price)}, Difference: ${difference}"
                    )
                # set the new price data
                shopping_list.price = Decimal(price)
                shopping_list.notes = notes

                # only allow updates in a 'forwards' direction. ie. A COMPLETE list cannot go back to CREATED.
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

"""
    - Generates and returns a list by collating all the items for all users in an organisation
    - Do not include lists that have already been shopped for
"""
class GenerateList(APIView):
    endpoint_name = "generate-list/"

    def post(self, request):
        try:
            # get request user profile info using auth token
            user = User.objects.filter(auth_token=request.auth).first()
            user_profile = UserProfile.objects.filter(user=user).first()
            user_organisation = user_profile.organisation
            user_type = user_profile.user_type
            if user_type != 'admin':
                # only admin users are authorised to see this info
                response_content = {
                    'detail': "You are not authorised to view this page."
                }
                return Response(response_content, status=status.HTTP_401_UNAUTHORIZED)
            response_content = {
                'list_items': {}
            }

            # get all lists that are in their initial 'CREATED' state
            shopping_lists = ShoppingList.objects.filter(status=ListStatus.objects.get(rank=0).label)
            for shopping_list in shopping_lists:
                # get the profile of the author of the shopping list
                shopping_list_owner = shopping_list.user
                shopping_list_owner_profile = UserProfile.objects.filter(user=shopping_list_owner).first()
                shopping_list_owner_organisation = shopping_list_owner_profile.organisation
                if user_organisation == shopping_list_owner_organisation:
                    # get list of item names from the shopping list
                    list_items = [item.item_name for item in ShoppingListItem.objects.filter(shopping_list=shopping_list)]
                    list_items = list(dict.fromkeys(list_items)) # remove duplicates
                    for item in list_items:
                        if item not in response_content['list_items'].keys():
                            # if the item doesn't exist in the response, initialise it
                            response_content['list_items'][item] = 0
                        # increment the item count
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

"""
    - Get user profile information
"""
class UserDetail(APIView):
    endpoint_name = 'user-detail/'

    def post(self, request):
        try:
            # get the request user profile using auth token
            user = User.objects.get(auth_token=request.auth)
            user_profile = UserProfile.objects.filter(user=user).first()
            user_organisation = user_profile.organisation
            user_type = user_profile.user_type

            # get user id from request data
            user_id = request.data['user_id']

            # get the user object we want to return
            user_detail_user = User.objects.get(id=user_id)
            user_detail_profile = UserProfile.objects.get(user=user_detail_user)
            user_detail_organisation = user_detail_profile.organisation

            authorised = False
            if user_type == 'admin' and user_organisation == user_detail_organisation:
                # an admin user can only view users at their own organisation
                authorised = True
            if user_type == 'user' and user_profile == user_detail_profile:
                # a user user can only view their own profile
                authorised = True
            if not authorised:
                response_content = {
                    'detail': "You are not authorised to view this page."
                }
                return Response(response_content, status=status.HTTP_401_UNAUTHORIZED)

            # get user auth info
            user_info = {
                'user_id': user_detail_user.id,
                'username': user_detail_user.username,
                'email': user_detail_user.email or "n/a"
            }
            # get a list of all the user's lists
            user_lists = ShoppingList.objects.filter(user=user_detail_user)
            # generate a list of list data from all user's lists
            list_data = [
                {
                    'list_name': str(user_list), 
                    'list_id': user_list.id,
                    'status': user_list.status
                } 
                for user_list in user_lists
            ]

            # get all the transactions on the user's account
            transactions = Transaction.objects.filter(user=user_detail_user).order_by('-transaction_datetime')
            # generate a list of transactions from all transaction models
            transaction_history = [
                {
                    'user': transaction.user.username,
                    'datetime': transaction.transaction_datetime.strftime("%Y-%m-%d %H:%M"),
                    'amount': transaction.transaction_amount,
                    'detail': transaction.detail
                }
                for transaction in transactions
            ]

            # calculate the current user's account balance
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

"""
    - An admin user can register a payment against a user at their organisation
"""
class RegisterPayment(APIView):
    endpoint_name = 'register-payment/'

    def post(self, request):
        try:
            # get the request user's profile info using auth token
            admin_user = User.objects.get(auth_token=request.auth)
            admin_user_profile = UserProfile.objects.filter(user=admin_user).first()
            admin_user_organisation = admin_user_profile.organisation
            admin_user_type = admin_user_profile.user_type

            # pull form data from the request
            user_id = request.data['user_id']
            payment = request.data['payment']
            
            # get the user object that the payment should be applied to
            list_user = User.objects.get(id=user_ud)
            list_user_profile = UserProfile.objects.filter(user=list_user).first()
            list_user_organisation = list_user_profile.organisation

            if admin_user_type == 'admin' and admin_user_organisation == list_user_organisation:
                # only admin users can register transactions
                # they can only register transactions against users at their own organisation

                # make the transaction
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

class GetCustomItem(APIView):
    endpoint_name = 'get-item/'

    def post(self, request):
        try:
            # get the item id from the request data
            item_id = request.data['item_id']

            # get the request user's profile info using auth token
            user = User.objects.get(auth_token=request.auth)
            user_profile = UserProfile.objects.filter(user=user).first()
            user_organisation = user_profile.organisation
            user_type = user_profile.user_type

            authorised = False # default to false
            if user_type == 'admin':
                # get the item by item id
                item = OrganisationCustomListOption.objects.get(id=item_id)

                # verify that the item belongs to the user's organisation
                if item.organisation == user_organisation:
                    authorised = True
            else:
                # get the item by item id
                item = UserCustomListOption.objects.get(id=item_id)

                # verify that the item belongs to the user
                if item.user == user:
                    authorised = True
            
            if authorised:
                response = {
                    'item': {
                        'id': item.id,
                        'item_name': item.item_name,
                        'price': item.price
                    }
                }
                if user_type == 'admin':
                    response['item']['group'] = OrganisationCustomListGroup.objects.get(id=item.group.id).group_name,
                return JsonResponse(response)
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
