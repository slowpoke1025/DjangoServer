from .models import Coupon, Thing, Gear, Exercise, Wear
from rest_framework import serializers


class ThingSerializers(serializers.ModelSerializer):
    # name = serializers.SerializerMethodField()

    class Meta:
        model = Thing
        fields = ["type", "amount"]

    # def get_name(self, obj):
    #     return obj.get_level_display()


class MintSerializers(serializers.ModelSerializer):
    LUCKY_CHOICE = ["regular", "advanced", "high-tech"]
    exp = serializers.ReadOnlyField()
    token_id = serializers.ReadOnlyField()
    coupon = serializers.ReadOnlyField()
    lucky = serializers.ChoiceField(choices=LUCKY_CHOICE)

    class Meta:
        model = Gear
        fields = [
            "token_id",
            "type",
            "level",
            "lucky",
            "exp",
            "goal_exp",
            "max_exp",
            "daily_exp",
            "custom",
            "coupon",
            # "pos",
            "isTargeted",
            "isDressed",
        ]


class CouponSerializers(serializers.ModelSerializer):
    # _CHOICE = list(Coupon.data.keys())
    # coupon = serializers.ChoiceField(choices=_CHOICE, write_only=True)
    coupon = serializers.CharField(write_only=True)
    type = serializers.ReadOnlyField(source="coupon")
    date = serializers.ReadOnlyField(source="coupon_date")
    level = serializers.ReadOnlyField()
    token_id = serializers.ReadOnlyField()

    class Meta:
        model = Gear
        fields = ["coupon", "token_id", "type", "level", "date"]


class GearSerializers(serializers.ModelSerializer):
    # user = serializers.PrimaryKeyRelatedField(read_only=True, source="user.address")
    class Meta:
        model = Gear
        fields = [
            "token_id",
            "type",
            "level",
            "lucky",
            "exp",
            "goal_exp",
            "max_exp",
            "daily_exp",
            "custom",
            "coupon",
            "trial"
        ]
        # exclude = ["user"]
        
class GearExSerializers(serializers.ModelSerializer):
    class Meta:
        model = Gear
        fields = [
            "token_id",
            "type",
        ]

class ExerciseSerializers(serializers.ModelSerializer):
    # timestamp = serializers.SerializerMethodField()
    # thing_level = serializers.IntegerField(write_only=True, required=False)
    thing = serializers.ChoiceField(
        # write_only=True,
        required=False,
        choices=[None, "dumbbell", "energy_drink", "protein_powder"],
    )
    # gear_id = serializers.PrimaryKeyRelatedField(read_only=True, source="gear.token_id")
    # gear_type = serializers.ReadOnlyField(source="gear.type")
    gear = GearExSerializers(read_only=True)
    count = serializers.IntegerField(required=True)
    accuracy = serializers.FloatField(required=True)
    valid_count = serializers.SerializerMethodField()
    
    def get_timestamp(self, obj):
        return obj.timestamp.date()
        
    def get_valid_count(self, obj):
        return round(obj.count * obj.accuracy)
        
    class Meta:
        model = Exercise
        fields = [
            "type",
            "count",
            "accuracy",
            "valid_count",
            "thing",
            "gear"
            # "timestamp"
        ]

    def validate_accuracy(self, value):
        if value > 1 or value < 0:
            raise serializers.ValidationError("accuracy must be between 0 and 1")
        return value

    # def create(self, validated_data):
    #     thing = validated_data.pop("thing", None)
    #     exercise = Exercise.objects.create(**validated_data)

    #     return exercise


class WearSerializers(serializers.ModelSerializer):
    # user = serializers.PrimaryKeyRelatedField(read_only=True, source="user.address")
    class Meta:
        model = Wear
        fields = ["dress", "target"]


class WearUpdateSerializers(serializers.ModelSerializer):
    class Meta:
        model = Gear
        fields = ["token_id"]
