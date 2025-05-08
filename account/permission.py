from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password
from django.core.exceptions import ObjectDoesNotExist
from icecream import ic
from rest_framework.exceptions import PermissionDenied, AuthenticationFailed
from rest_framework.response import Response

from .models import CustomUser


class PhoneAuthBackend(BaseBackend):
    def authenticate(self, request, phone=None, password=None):
        print(f"Attempting authentication for phone: {phone}")
        try:
            user = CustomUser.objects.get(phone=phone)

            if user.check_password(password):
                print("Authentication successful")
                return user
            elif user.is_archived:
                return Response({"You can't enter to the system because you are archived!"})

            else:
                print("Invalid password")
        except CustomUser.DoesNotExist:
            print("User does not exist")
        return None

    def get_user(self, user_id):
        try:
            return CustomUser.objects.get(pk=user_id)
        except CustomUser.DoesNotExist:
            return None

