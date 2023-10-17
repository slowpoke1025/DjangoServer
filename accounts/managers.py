# Example

# from django.db import models

# class PublishedManager(models.Manager):
#     def get_queryset(self):
#         # Retrieve only published articles
#         return super().get_queryset().filter(published=True)

# class Article(models.Model):
#     title = models.CharField(max_length=100)
#     content = models.TextField()
#     published = models.BooleanField(default=False)

#     objects = models.Manager()  # Default manager
#     published_objects = PublishedManager()  # Custom manager

#     def __str__(self):
#         return self.title


from django.contrib.auth.models import BaseUserManager


class CustomUserManager(BaseUserManager):
    def create_user(self, username, **extra_fields):
        # Create and save a new user with the given username and password
        if not username:
            raise ValueError("The username must be set")

        # if not password:
        #     raise ValueError("The password must be set")

        user = self.model(username=username, **extra_fields)
        # user.set_password(password)
        user.save()
        return user

    def create_superuser(self, username, **extra_fields):
        # Create and save a new superuser with the given username and password
        # extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(username, **extra_fields)


# https://docs.djangoproject.com/en/4.2/topics/auth/customizing/#a-full-example
