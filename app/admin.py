from django.contrib import admin
from .models import Reports, ExecutiveSummaryData, accountingJE_GLMapping

# Register your models here.
admin.site.register(Reports)
admin.site.register(ExecutiveSummaryData)
admin.site.register(accountingJE_GLMapping)
