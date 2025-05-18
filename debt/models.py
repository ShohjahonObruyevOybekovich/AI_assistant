from django.db import models

from command.models import BaseModel
from account.models import CustomUser

class Debt(BaseModel):
    user : "CustomUser" = models.ForeignKey("account.CustomUser", on_delete=models.SET_NULL, null=True,blank=True,related_name="debtor_user")
    target_person : str = models.CharField(max_length=120,blank=True,null=True)
    amount : int = models.IntegerField(default=0)
    type : str = models.CharField(choices=[
        ("GIVE","GIVE"),
        ("TAKE","TAKE"),
    ],max_length=11,null=True,blank=True)
    currency : str = models.CharField(max_length=10, default="SUM")
    due_date : str = models.DateTimeField(max_length=120,null=True,blank=True)
    status = models.CharField(max_length=20, choices=[
        ("UNPAID", "Unpaid"),
        ("PARTIAL", "Partial"),
        ("PAID", "Paid")],
        default="UNPAID")
    reason : str = models.CharField(max_length=120)
    date : str = models.DateField(auto_now=True)
    time : str = models.TimeField(auto_now=True)


class Payed(BaseModel):
    user : "CustomUser" = models.ForeignKey("account.CustomUser", on_delete=models.SET_NULL, null=True,blank=True,related_name="payed_user")
    debt : "Debt" = models.ForeignKey("debt.Debt", on_delete=models.SET_NULL, null=True,blank=True,related_name="payed_debt")
    target_person = models.CharField(max_length=120,null=True,blank=True)
    type : str = models.CharField(choices=[
        ("GIVE","GIVE"),
        ("TAKE","TAKE"),
    ])
    amount : int = models.IntegerField(default=0)
    currency : str = models.CharField(max_length=10, default="SUM")
    date : str = models.DateField(auto_now=True)
    time : str = models.TimeField(auto_now=True)
    reason : str = models.CharField(max_length=120)

