# This file is meant to be run on initializion to add new permission

from app.models import Reports, ExecutiveSummaryData
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

# Run this command with new permission uncommented
# python manage.py shell < permissions.py

#content_type = ContentType.objects.get_for_model(Reports)
#permission = Permission.objects.create(
#    codename='can_view',
#    name='Can View reports',
#    content_type=content_type,
#)

#content_type2 = ContentType.objects.get_for_model(Reports)
#permission = Permission.objects.create(
#    codename='can_upload',
#    name='Can Upload report data',
#    content_type=content_type2,
#)

#content_type3 = ContentType.objects.get_for_model(ExecutiveSummaryData)
#permission = Permission.objects.create(
#    codename='can_view_exsumm',
#    name='Can View the Executive Summary',
#    content_type=content_type3,
#)

#content_type4 = ContentType.objects.get_for_model(Reports)
#permission = Permission.objects.create(
#    codename='accounting_view',
#    name='Allows access to accounting reports',
#    content_type=content_type4,
#)
