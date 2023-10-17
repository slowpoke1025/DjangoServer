from django.contrib import admin
from .models import Thing, Gear, Exercise, Wear, WeekTask


# Register your models here.
class GearInline(admin.StackedInline):  # admin.TabularInline
    model = Gear
    extra = 1


class TaskInline(admin.StackedInline):  # admin.TabularInline
    model = WeekTask
    extra = 1


class WearInline(admin.StackedInline):  # admin.TabularInline
    model = Wear
    extra = 1


class GearAdmin(admin.ModelAdmin):
    list_display = [
        # "id",
        "token_id",
        "user",
        "level",
        "type",
        "orientation",
        "lucky",
        "work_max",
        "exp",
        "coupon",
    ]


class ExerciseAdmin(admin.ModelAdmin):
    list_display = ["user", "type", "timestamp", "count", "accuracy", "exp","gear", "thing"]


class ThingAdmin(admin.ModelAdmin):
    list_display = ["user", "type", "amount"]


class TaskAdmin(admin.ModelAdmin):
    list_display = ["user", "week_start", "count", "last_completed"]


class WearAdmin(admin.ModelAdmin):
    list_display = ["user", "target", "hair", "top", "bottom", "shoes"]


admin.site.register(Gear, GearAdmin)
admin.site.register(Exercise, ExerciseAdmin)
admin.site.register(Thing, ThingAdmin)
admin.site.register(WeekTask, TaskAdmin)
admin.site.register(Wear, WearAdmin)
