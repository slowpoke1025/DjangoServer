# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.

from datetime import timedelta, datetime
import json
import os, random
from django.db import models
from django.utils import timezone
from accounts.models import User


class Gear(models.Model):
    with open(
        os.path.join(os.path.dirname(__file__), "gear_type.json"), "r", encoding="utf-8"
    ) as file:
        TYPES_INFO = json.load(file)

    ORIENTATION = {
        k: "healthy" if v["type"] in ["hair", "top"] else "workout"
        for k, v in TYPES_INFO.items()
    }

    CONFIG = {
        "healthy": {
            "WORK_MAX": [40, 50, 60],
            "WORK_MIN": [15, 25, 30],
            "GOAL_DAYS": 14,
        },
        "workout": {
            "WORK_MAX": [60, 70, 80],
            "WORK_MIN": [20, 30, 40],
            "GOAL_DAYS": 14 / 2,
        },
    }

    PROB_EPIC = {"regular": 0.01, "advanced": 0.05, "high-tech": 0.1}
    LUCKY_RANGE = {
        "regular": [1, 1],  # regular
        "advanced": [1.01, 1.2],  # advanced
        "high-tech": [1.21, 1.4],  # high-tech
        "epic": [1.41, 1.5],  # epic
    }

    Type = models.TextChoices(
        "Type",
        [(f"{v['type']}/{k}", k) for k, v in TYPES_INFO.items()],  # (display, value)
    )

    class Level(models.IntegerChoices):
        A = (0, "basic")
        B = (1, "intermediate")
        C = (2, "advanced")

    # primary_key = True in production
    token_id = models.PositiveIntegerField()
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, to_field="address")
    level = models.PositiveIntegerField(choices=Level.choices)
    type = models.CharField(max_length=10, choices=Type.choices)
    lucky = models.FloatField(default=1)
    exp = models.FloatField(default=0)
    coupon = models.TextField(blank=True, null=True)
    custom = models.TextField(blank=True, null=True)
    coupon_date = models.DateField(blank=True, null=True)
    # trial = models.BooleanField(default=False)
    

    @property
    def config(self):
        return self.CONFIG.get(self.orientation)

    @property
    def orientation(self):
        return self.ORIENTATION.get(self.type)

    @property
    def work_max(self):
        return self.config.get("WORK_MAX")[self.level]

    @property
    def work_min(self):
        return self.config.get("WORK_MIN")[self.level]

    @property
    def goal_days(self):
        return self.config.get("GOAL_DAYS")

    @property
    def goal_exp(self):
        return self.work_max * 2 * self.goal_days

    @property
    def daily_exp(self):  # 待補
        return 0

    @property
    def max_exp(self):
        return self.goal_exp / self.goal_days

    @property
    def is_exchangeable(self):
        return True or not self.is_redeemed and self.exp >= self.goal_exp  # 上線更新

    @property
    def is_redeemed(self):
        return self.coupon != None

    @property
    def uri(self):
        return f"http://140.117.71.159:8000/api/gears/{self.token_id}"

    @property
    def pos(self):
        return self.TYPES_INFO[self.type].get("type")

    @property
    def isTargeted(self):
        return self.user.wear.target == self

    @property
    def isDressed(self):
        return getattr(self.user.wear, self.pos) == self

    def __str__(self):
        return f"{self.user.username}_{self.token_id}_{self.pos}"

    class Meta:
        managed = True
        db_table = "gear"


# Gear.load_type()


# [Gear.Type.choices.append((k, v["name"])) for k, v in Gear.TYPES.items()]
# print("before", Gear.Type.choices)

class Thing(models.Model):
    # class Type(models.IntegerChoices):
    #     BASIC = (0, "初級小物")
    #     INTERMEDIATE = (1, "中級小物")
    #     HIGH_END = (2, "高級小物")
    probabilities = {
        "dumbbell": 0.5,
        "energy_drink": 0.3,
        "protein_powder": 0.2,
    }

    weights = {
        "dumbbell": 0.25,
        "energy_drink": 0.5,
        "protein_powder": 0.75,
    }

    class Type(models.TextChoices):
        BASIC = ("dumbbell", "初級小物/dumbbell")
        INTERMEDIATE = ("energy_drink", "中級小物/energy_drink")
        HIGH_END = ("protein_powder", "高級小物/protein_powder")

    # type = models.PositiveIntegerField(choices=Type.choices)
    type = models.CharField(max_length=20, choices=Type.choices, default=Type.BASIC)

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # directly record amount, easy to handle
    amount = models.PositiveIntegerField(default=0)

    class Meta:
        managed = True
        db_table = "thing"
        unique_together = (("user", "type"),)

    def __str__(self):
        return f"{self.user.username}_{self.get_type_display()}"
    

class Exercise(models.Model):
    class Type(models.TextChoices):  # Gear.Type.choices
        A = ("bicep_curl", "bicep_curl")
        B = ("push_up", "push_up")
        C = ("squat", "squat")

    user = models.ForeignKey(User, on_delete=models.CASCADE) # transfer issue 
    gear = models.ForeignKey(Gear, on_delete=models.CASCADE, blank=True, null=True) 
    type = models.CharField(max_length=15, choices=Type.choices, default=Type.A)
    timestamp = models.DateTimeField(auto_now_add=False, default=timezone.now)
    count = models.PositiveIntegerField(default=0)  # new
    accuracy = models.FloatField(default=0.0)
    thing = models.CharField(max_length=15, choices=Thing.Type.choices, blank=True, null=True)
    exp = models.FloatField(default=0.0, blank=True, null=True)
    
    class Meta:
        managed = True
        db_table = "exercise"

    def __str__(self):
        return f"{self.user}_{self.timestamp.date()}"

    @property
    def valid_count(self):
        return round(self.accuracy * self.count)




class WeekTask(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, primary_key=True, related_name="task"
    )
    week_start = models.DateField(auto_now=False, default=timezone.now)  # 記錄每周任務開始日期
    count = models.PositiveIntegerField(default=0)  # 記錄每周完成次數
    # last_completed = models.DateField(null=True, blank=True)  # 記錄用戶上次完成日期

    @property
    def last_completed(self):
        return self.week_start + timedelta(days=self.count - 1) if self.count else None

    @property
    def delta(self):
        return datetime.now().date() - self.week_start

    class Meta:
        managed = True

    def __str__(self):
        return f"{self.user.username}_{self.pk}"


class Wear(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, primary_key=True, related_name="wear"
    )
    target = models.OneToOneField(
        Gear, on_delete=models.CASCADE, related_name="target", blank=True, null=True
    )
    hair = models.OneToOneField(
        Gear,
        on_delete=models.CASCADE,
        related_name="hair",
        null=True,
        blank=True,
        default=None,
    )
    top = models.OneToOneField(
        Gear,
        on_delete=models.CASCADE,
        related_name="top",
        null=True,
        blank=True,
        default=None,
    )
    bottom = models.OneToOneField(
        Gear,
        on_delete=models.CASCADE,
        related_name="bottom",
        null=True,
        blank=True,
        default=None,
    )
    shoes = models.OneToOneField(
        Gear,
        on_delete=models.CASCADE,
        related_name="shoes",
        null=True,
        blank=True,
        default=None,
    )

    @property
    def dress(self):
        return [
            {"token_id": obj.token_id, "type": obj.type}
            if (obj := getattr(self, i))
            else obj
            for i in ["hair", "top", "bottom", "shoes"]
        ]

    @property
    def _target(self):
        return (
            {"token_id": self.target.token_id, "type": self.target.type}
            if self.target
            else None
        )

    class Meta:
        managed = True

    def __str__(self):
        return f"{self.user.username}'s wearing"


class Coupon:
    with open(
        os.path.join(os.path.dirname(__file__), "coupon.json"), "r", encoding="utf-8"
    ) as file:
        data = json.load(file)
