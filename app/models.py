"""
Definition of models.
"""

from django.db import models

# Create your models here.
class Reports(models.Model):
    name = models.CharField(max_length=255, unique=True)
    table_name = models.CharField(max_length=255, unique=True)
    required_field = models.TextField()

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

    def __str__(self):
        return f"{self.location} - {self.provider}: ${self.charges}, ${self.payments}, ${self.adjustments}"
