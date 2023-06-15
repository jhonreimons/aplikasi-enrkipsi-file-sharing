from django.db import models
# from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
# from django.contrib.admin.models import LogEntry
# from django.contrib.auth import get_user_model
# # Create your models here.
class User(models.Model):
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(max_length=254)
    passphrase = models.CharField(max_length=200, null= True)
    public_key = models.CharField(max_length=2048, null=True, blank=True)
    private_key = models.CharField(max_length=2048, null=True, blank=True)

