from django.contrib import admin
from .models import Client, Account, Transaction

admin.site.register(Client)
admin.site.register(Account)
admin.site.register(Transaction)
