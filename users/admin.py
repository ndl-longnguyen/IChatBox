from django.contrib import admin
from users.models import Participant, User


admin.site.register(User)
admin.site.register(Participant)
