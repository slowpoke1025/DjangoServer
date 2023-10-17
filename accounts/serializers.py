from .models import User
from rest_framework import serializers
from web3 import Web3


class UserSerializers(serializers.ModelSerializer):
    # password = serializers.CharField(write_only=True)
    nonce = serializers.ReadOnlyField()
    last_login = serializers.ReadOnlyField()
    is_superuser = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()

    # def validate_email(self, value):
    #     if User.objects.filter(email=value).exists():
    #         raise serializers.ValidationError("Email is already in use.")
    #     return value

    # def validate(self, data):
    #     email = data.get("email")
    #     if email and User.objects.filter(email=email).exists():
    #         raise serializers.ValidationError("Email is already in use.")
    #     return data

    def validate_address(self, value):
        print(value)
        if not Web3.is_address(value):
            raise serializers.ValidationError("Enter a valid ethereum address")
        if not Web3.is_checksum_address(value):
            value = Web3.to_checksum_address(value)

        return value

    class Meta:
        model = User
        fields = "__all__"


class ProfileSerializers(serializers.ModelSerializer):
    address = serializers.CharField(read_only=True)
    target = serializers.PrimaryKeyRelatedField(
        source="wear._target", read_only=True, default=None
    )
    dress = serializers.ReadOnlyField(source="wear.dress")

    class Meta:
        model = User
        fields = (
            "address",
            "username",
            "gender",
            "weight",
            "height",
            "birth",
            "email",
            "target",
            "dress",
        )
