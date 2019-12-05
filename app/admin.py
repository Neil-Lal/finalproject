from django.contrib import admin
from .models import Reports, ExecutiveSummaryData, accountingJE_GLMapping, Announcements, ExportReports, Schedule

# Register your models here.
admin.site.register(Reports)
admin.site.register(ExecutiveSummaryData)
admin.site.register(accountingJE_GLMapping)
admin.site.register(Announcements)
admin.site.register(ExportReports)
admin.site.register(Schedule)