from django.db import models


class UserOwnedQuerySet(models.QuerySet):
    def for_user(self, user):
        return self.filter(user=user)


class UserOwnedManager(models.Manager):
    def get_queryset(self):
        return UserOwnedQuerySet(self.model, using=self._db)

    def for_user(self, user):
        return self.get_queryset().for_user(user)
