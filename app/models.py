"""
Definition of models.
"""

from django.db import models
from django.contrib.auth.models import Group
from django_pandas.managers import DataFrameManager


# Create your models here.
class Announcements(models.Model):
    message = models.CharField(max_length=255)
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.message}"


class Reports(models.Model):
    name = models.CharField(max_length=255, unique=True)
    table_name = models.CharField(max_length=255, unique=True)
    required_field = models.TextField()

    def __str__(self):
        return f"{self.name}"


class ExportReports(models.Model):
    name = models.CharField(max_length=255, unique=True)
    report_data = models.ForeignKey(Reports,
                                    on_delete=models.CASCADE,
                                    related_name='report_data',
                                    )

    def __str__(self):
        return f"{self.name}"


class Schedule(models.Model):
    name = models.CharField(max_length=255, unique=True)
    permission_group = models.ForeignKey(Group,
                                         on_delete=models.CASCADE,
                                         related_name='group_perm')
    report = models.ForeignKey(ExportReports,
                               on_delete=models.CASCADE,
                               related_name='report_name')
    def __str__(self):
        return f"{self.name}"


class ExecutiveSummaryData(models.Model):
    name = models.ForeignKey(Reports,
                             on_delete=models.CASCADE,
                             related_name='report_name',
                             )
    provider = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    charges = models.DecimalField(max_digits=18, decimal_places=2)
    payments = models.DecimalField(max_digits=18, decimal_places=2)
    adjustments = models.DecimalField(max_digits=18, decimal_places=2)
    date_ran = models.DateField(auto_now_add=True)
    objects = models.Manager()
    pdobjects = DataFrameManager()

    def __str__(self):
        return f"{self.location} - {self.provider}: ${self.charges}, ${self.payments}, ${self.adjustments}"


class accountingJE_GLMapping(models.Model):
    location = models.CharField(max_length=255)
    GL = models.CharField(max_length=25)

    def __str__(self):
        return f"{self.location} : {self.GL}"
