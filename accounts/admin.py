from django.contrib import admin

from api.admin import GearInline, TaskInline, WearInline
from .models import User
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

# Register your models here.

PROFILE_FIELDS = ("weight", "height", "gender", "birth", "email", "address")
PERMISSION_FIELDS = ("is_superuser", "is_active")


class CustomUserAdmin(UserAdmin):
    inlines = [  # 在 user admin site 展開
        # GearInline,
        TaskInline,
        WearInline,
    ]

    list_display = (
        "username","id",
        *PROFILE_FIELDS,
        *PERMISSION_FIELDS,
    )
    list_filter = PERMISSION_FIELDS
    filter_horizontal = []  # disable groups and user_permissions from PermissionsMixin
    fieldsets = (
        ("Account", {"fields": ("username",)}),
        ("Profile", {"fields": PROFILE_FIELDS}),
        ("Permissions", {"fields": PERMISSION_FIELDS}),
    )

    add_fieldsets = (
        (
            "Account",
            # {"classes": ("wide",), "fields": ("username", "password1", "password2")},
            {"classes": ("wide",), "fields": ("username", "password1", "password2")},
        ),
        (
            "Profile",
            {"classes": ("wide",), "fields": PROFILE_FIELDS},
        ),
        (
            "Permissions",
            {"classes": ("wide",), "fields": PERMISSION_FIELDS},
        ),
    )


admin.site.register(User, CustomUserAdmin)
admin.site.unregister(Group)


# print(
#     "-----------",
#     # list(UserAdmin.fieldsets),
#     "-----------",
#     # list(UserAdmin.add_fieldsets),
#     sep="\n",
# )


# [
#     (None, {"fields": ("username", "password")}),
#     ("Personal info", {"fields": ("first_name", "last_name", "email")}),
#     (
#         "Permissions",
#         {
#             "fields": (
#                 "is_active",
#                 "is_staff",
#                 "is_superuser",
#                 "groups",
#                 "user_permissions",
#             )
#         },
#     ),
#     ("Important dates", {"fields": ("last_login", "date_joined")}),
# ]


# fieldset = UserAdmin.fieldsets[1][1]
# fieldset["fields"] = ("email", "weight", "height", "sex", "birth")


# ADDITIONAL_USER_FIELDS = (
#     (
#         "Profile",
#         {
#             "fields": (
#                 # "address", # in production
#                 "username",
#                 "weight",
#                 "height",
#                 "gender",
#                 "birth",
#                 "created_date",
#             )
#         },
#     ),
# )

# class MyUserAdmin(UserAdmin):
#     model = User

#     add_fieldsets = UserAdmin.add_fieldsets + ADDITIONAL_USER_FIELDS
#     fieldsets = UserAdmin.fieldsets + ADDITIONAL_USER_FIELDS


# admin.site.register(User, admin.ModelAdmin)
