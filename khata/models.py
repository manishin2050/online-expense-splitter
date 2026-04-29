from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal, ROUND_DOWN

# Create your models here.

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    is_online = models.BooleanField(default=False)   # user login hai ya nahi
    last_seen = models.DateTimeField(null=True, blank=True)
    def __str__(self):
        return self.user.username

class Group(models.Model):
    name = models.CharField(max_length=255)
    rent=models.DecimalField(max_digits=10, decimal_places=2,default=0)
    start_day=models.IntegerField(default=1)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_groups")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class GroupMember(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="group_memberships")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="group_memberships")
    is_admin = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} in {self.group.name}"

class Description(models.Model):
    payer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='paid_expenses',default=2)
    amount = models.DecimalField(max_digits=10, decimal_places=2,default=0)
    description = models.CharField(max_length=255, blank=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="paid_expenses", null=True)
    date=models.DateField(null=True)
    times=models.CharField(null=True,max_length=50)

    def __str__(self):
        return f"{self.description} - {self.amount} by {self.payer.username}"


class Spilt(models.Model):
    expense= models.ForeignKey(Description, on_delete=models.CASCADE, related_name='spilts',default=2)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='spilts',default=2)
    share = models.DecimalField(max_digits=10, decimal_places=2)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True)
    date=models.DateField(null=True)
    times=models.CharField(null=True,max_length=50)
    def __str__(self):
        return f"{self.user} owes {self.share}rs for {self.expense.id} " 

class Shopping(models.Model):
    payer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shoppings',default=2)
    amount=models.DecimalField(max_digits=10, decimal_places=2,default=0)
    desc=models.CharField(max_length=255, blank=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="shoppings", null=True)
    date=models.DateField(null=True)
    times=models.CharField(null=True,max_length=50)
    def __str__(self):
        return f"{self.payer} shop {self.desc}"

class EqualShare(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='equalshares',default=2)
    amount = models.DecimalField(max_digits=10, decimal_places=2,default=0)
    desc=models.CharField(max_length=255, blank=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True)
    date=models.DateField(null=True)
    times=models.CharField(null=True,max_length=50)
    def __str__(self):
        return f"{self.user} added {self.desc}"
    
class EqualShareSplit(models.Model):
    speaker=models.ForeignKey(EqualShare,on_delete=models.CASCADE,related_name='equalsharessplit')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='equalsharessplit',default=2)
    amount= models.DecimalField(max_digits=10, decimal_places=2,default=0)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True)
    date=models.DateField(null=True)
    times=models.CharField(null=True,max_length=50)
    def __str__(self):
        return f"{self.speaker} shares  {self.amount}"
    
