# from django.db.models import Sum
# from icecream import ic
# from rest_framework import serializers
# from rest_framework.serializers import ModelSerializer
#
# from .models import CustomUser
# from account.permission import PhoneAuthBackend
# from upload.models import File
# from upload.serializers import FileUploadSerializer
#
#
# class UserCreateSerializer(serializers.ModelSerializer):
#     password = serializers.CharField(write_only=True)
#
#     class Meta:
#         model = CustomUser
#         fields = (
#             "id", "full_name", "first_name", "last_name", "phone", "role", "password",
#         )
#         # We don't need to add extra_kwargs for password
#
#     def create(self, validated_data):
#         # Ensure password is provided in the request
#         password = validated_data.pop('password', None)
#         print(password)
#         if not password:
#             raise serializers.ValidationError({"password": "Password is required."})
#
#         files = validated_data.pop('files', [])
#         filial = validated_data.pop('filial', None)
#
#         user = CustomUser(**validated_data)
#         user.set_password(password)  # Hash the password
#         user.full_name = f"{user.first_name} {user.last_name}"
#         user.save()
#         user.filial.set(filial)
#         user.files.set(files)
#         user.save()
#         return user
#
#
# # class ConfirmationCodeSerializer(serializers.Serializer):
# #     phone = serializers.EmailField()
# #     confirmation_code = serializers.IntegerField()
# #
# #
# # class PasswordResetRequestSerializer(serializers.Serializer):
# #     phone = serializers.EmailField()
# #
# #
# # class PasswordResetLoginSerializer(serializers.Serializer):
# #     new_password = serializers.CharField()
#
# class UserLoginSerializer(serializers.Serializer):
#     phone = serializers.CharField(max_length=30, required=True)
#     password = serializers.CharField(max_length=128, required=True, write_only=True)
#
#     def validate(self, attrs):
#         phone = attrs.get('phone')
#         password = attrs.get('password')
#
#         if phone and password:
#             backend = PhoneAuthBackend()
#             user = backend.authenticate(
#                 request=self.context.get('request'),
#                 phone=phone,
#                 password=password,
#             )
#             ic(user)
#
#             if not user:
#                 raise serializers.ValidationError(
#                     "Unable to log in with provided credentials.",
#                     code="authorization"
#                 )
#         else:
#             raise serializers.ValidationError(
#                 "Must include 'phone' and 'password'.",
#                 code="authorization"
#             )
#
#         attrs['user'] = user
#         return attrs
#
#
# class UserUpdateSerializer(serializers.ModelSerializer):
#     phone = serializers.CharField(max_length=15, required=False)
#     photo = serializers.PrimaryKeyRelatedField(queryset=File.objects.all(), allow_null=True, required=False)
#     password = serializers.CharField(max_length=128, write_only=True, required=False)
#     files = serializers.PrimaryKeyRelatedField(queryset=File.objects.all(), many=True, required=False)
#
#     class Meta:
#         model = CustomUser
#         fields = [
#             "id", "phone", "full_name", "first_name", "last_name", "password","is_archived", "photo",
#             "date_of_birth"
#             ]
#
#     def update(self, instance, validated_data):
#         password = validated_data.pop("password", None)
#         if password:
#             instance.set_password(password)
#
#         phone = validated_data.get("phone")
#         if phone and phone != instance.phone:
#             if CustomUser.objects.exclude(id=instance.id).filter(phone=phone).exists():
#                 raise serializers.ValidationError({"phone": "already_used_number"})
#             instance.phone = phone
#
#         # Update `photo` field manually
#         if "photo" in validated_data:
#             instance.photo = validated_data["photo"]
#
#         # Update other fields except many-to-many
#         for attr, value in validated_data.items():
#             if attr not in [ "files","filial"]:
#                 setattr(instance, attr, value)
#
#         if "first_name" or "last_name" in validated_data:
#             instance.full_name = f"{instance.first_name} {instance.last_name}"
#
#         instance.save()
#         return instance
#
#     def to_representation(self, instance):
#         # Get the base URL for media
#         representation = super().to_representation(instance)
#         if instance.photo:
#             representation['photo'] = FileUploadSerializer(instance.photo, context=self.context).data
#         return representation
#
#
# class UserListSerializer(ModelSerializer):
#     photo = serializers.PrimaryKeyRelatedField(queryset=File.objects.all())
#
#     class Meta:
#         model = CustomUser
#         fields = ['id', 'phone', "full_name", "first_name", "last_name", 'role',"balance","is_archived",
#                   "photo", "created_at" ]
#
#     def to_representation(self, instance):
#         rep = super().to_representation(instance)
#         rep['photo'] = FileUploadSerializer(instance.photo, context=self.context).data
#         return rep
#
#
# class UserSerializer(serializers.ModelSerializer):
#     photo = serializers.PrimaryKeyRelatedField(queryset=File.objects.all(), allow_null=True)
#
#     class Meta:
#         model = CustomUser
#         fields = (
#             "id", "full_name", "first_name", "last_name","phone", "role",
#             "photo", "balance", "date_of_birth", "created_at","updated_at","is_archived"
#         )
#
#     def to_representation(self, instance):
#         rep = super().to_representation(instance)
#         rep['photo'] = FileUploadSerializer(instance.photo, context=self.context).data
#         rep['files'] = FileUploadSerializer(instance.files.all(), many=True, context=self.context).data
#         return rep
#
#     def create(self, validated_data):
#         user = CustomUser.objects.create(**validated_data)
#         return user
#
# class CheckNumberSerializer(serializers.Serializer):
#     phone = serializers.CharField()
#
