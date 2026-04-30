from django.shortcuts import render,redirect,get_object_or_404,get_list_or_404
from khata.models import Description,Spilt,EqualShare,EqualShareSplit,Shopping,Group,GroupMember
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout,login,authenticate
from datetime import datetime
from decimal import Decimal, ROUND_DOWN
from itertools import zip_longest
from django.db import transaction
# from django.db.models import Case,When,Value
import time
from django.template.loader import render_to_string
from weasyprint import HTML

# from .utils import get_user_balance

import pytz

from django.db.models import Sum,Count,Q,Case,When,Value


# Create your views here.
from django.http import HttpResponse








# rent=7000

asia_tz = pytz.timezone('Asia/Kolkata')




def download(request,id):

    # Create an Excel file in memory
    if request.method=="POST":

        sdate=request.POST.get('from')
        edate=request.POST.get('to')
        # print(sdate)
        try:
            # start_date = datetime.strptime(f"{sdate}", '%Y-%m-%d').strftime('%m/%d/%y')
            # end_date = datetime.strptime(f"{edate}", '%Y-%m-%d').strftime('%m/%d/%y')
            start_date = sdate
            end_date = edate
        except ValueError:
            return HttpResponse("Invalid date format. Use MM/DD/YY.", status=400)

        descc=Description.objects.filter(date__range=(start_date,end_date),group_id=id).prefetch_related('spilts').order_by('-id')
        data={

            "objs":descc,
            "start_date":start_date,
            "end_date":end_date,
            "group_id":id,
            "date":datetime.now(asia_tz).date(),

        }

        return render(request,"download.html",data)
    else:
        data={
            "date":datetime.now(asia_tz).date(),

        }
        return render(request,"download.html",data)
def download_pdf(request, group_id,start_date,end_date):
    # Fetch your data
    expense_list = Description.objects.filter(date__range=(start_date,end_date),group_id=group_id).prefetch_related('spilts').order_by('-id')
    group_name =Group.objects.get(id=group_id).name
    html_string = render_to_string('../templates/expense_pdf.html', {
        'objs': expense_list,
        'group_name':group_name,
        'start_date':start_date,
        'end_date':end_date
    })

    html = HTML(string=html_string)
    pdf = html.write_pdf()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{group_name}_expenses-{start_date}_to_{end_date}.pdf"'
    # return redirect('khata:home', group_id)
    return response

def home(request,group_id):
 
    if User.objects.all().count() > 0:
        today = datetime.now(asia_tz)
        try:
            group= Group.objects.get(id=group_id)
            # print(group)
        
        except:
            # print("no--------")
            return redirect("khata:index")
        rent= group.rent
        start_day= group.start_day
    #     # Determine the current month and year
        current_month = today.month
        current_year = today.year

        # Calculate the start and end dates
        if today.day >= start_day:  # If today is the 8th or later, filter 8th of this month to 8th of next month
            start_date = datetime(current_year, current_month, start_day,tzinfo=asia_tz)
            if current_month == 12:  # Handle year-end transition
                end_date = datetime(current_year + 1, 1,start_day,tzinfo=asia_tz)
            else:
                end_date = datetime(current_year, current_month + 1, start_day,tzinfo=asia_tz)
        else:  # If today is before the 8th, filter 8th of last month to 8th of this month
            if current_month == 1:  # Handle year-start transition
                start_date = datetime(current_year - 1, 12, start_day,tzinfo=asia_tz)
            else:
                start_date = datetime(current_year, current_month - 1, start_day,tzinfo=asia_tz)
            end_date = datetime(current_year, current_month, start_day,tzinfo=asia_tz)

        # Format dates as MM/DD/YY for debugging or display
        formatted_start_date = start_date.strftime('%Y-%m-%d')
        name_start_date=start_date.date()
        formatted_end_date = end_date.strftime('%Y-%m-%d')

        descc=Description.objects.filter(date__range=(formatted_start_date, formatted_end_date),group=group_id).prefetch_related('spilts').order_by('-id')
        users = User.objects.exclude(id=1).filter(group_memberships__group=group_id)
        online_users = User.objects.exclude(id=1).filter(profile__is_online=True,group_memberships__group=group_id)
      
        rent_per_user = Decimal(rent) / Decimal(len(online_users)) if len(online_users) > 0 else Decimal(0)
        rent_per_user_reminder = Decimal(rent)-(Decimal(rent_per_user).quantize(Decimal('0.01')) * Decimal(len(online_users)))
        # print("rent: ", rent)
        # print("online users: ", len(online_users))
        # print("rent per user: ", rent_per_user)
        # print("rent per user: ", rent_per_user_reminder)

        group_name= Group.objects.get(id=group_id).name 

        membership = GroupMember.objects.get(group_id=group_id, user=request.user).is_admin
        print(membership)
        is_admin = membership


        def get_user_balance(user):
            user_expenses = (
                Description.objects
                .filter(date__range=(formatted_start_date, formatted_end_date), payer=user,group=group_id)
                .aggregate(total_amount=Sum('amount'))  # aggregate one number
            )

            spilt_expense = (
                Spilt.objects
                .filter(date__range=(formatted_start_date, formatted_end_date), user=user,group=group_id)
                .aggregate(total_amount=Sum('share'))  # aggregate one number Spilt.objects
            )
            equal_share=(
                EqualShareSplit.objects
                .filter(date__range=(formatted_start_date, formatted_end_date), user=user,group=group_id)
                .aggregate(total_amount=Sum('amount'))  # aggregate one number
            )
           
            credit = user_expenses["total_amount"] or Decimal(0)
            debit = spilt_expense["total_amount"] or Decimal(0)
            sharing = equal_share["total_amount"] or Decimal(0)
          
            if user.profile.is_online:
                user_rent = rent_per_user
            else:
                user_rent = Decimal(0)
            return ( user_rent + debit - credit + sharing).quantize(Decimal('0.01'))
            # return (Decimal(credit) - Decimal(debit)).quantize(Decimal('0.01'))

        balances = []
        for u in users:
            balances.append({
                'user': u,
                'balance': get_user_balance(u)
            })

        # print("this is balance :", balances)
        total_balance = sum(b['balance'] for b in balances)

        data={
                "objs":descc,
                "group_id":group_id,
                "group_name":group_name,
                "user_is_admin":is_admin,
                "online_users": zip_longest(users,balances,fillvalue=0),
                "start_date":name_start_date,
                "total_balance":total_balance+rent_per_user_reminder,
                "rent_per_user":rent_per_user.quantize(Decimal('0.01')),
                "rent_user_count":online_users,
                "today_date":datetime.now().date(),         
        }

        return render(request,"dashboard.html",data)
    else:
        data={
            "date":datetime.now(asia_tz).date(),

        }
        return render(request,"dashboard.html",data)

@login_required(login_url='khata:login')
def add_expense(request,group_id):
    if request.method=="POST":
       payer=User.objects.get(id=request.user.id)
       amount=request.POST.get('price')
       desc=request.POST.get('desc')
       date=datetime.now(asia_tz).date()
       times=datetime.now(asia_tz).strftime("%I:%M %p")
       user_list=request.POST.getlist('userss')
    #    print("this is user list: ",payer,amount,desc,date,times,user_list)
       expense=Description.objects.create(payer=payer,amount=amount,description=desc,date=date,times=times,group_id=group_id)
                        #    users = User.objects.exclude(id=1).filter(profile__is_online=True)

       total_user=len(user_list)

              
       amount = Decimal(amount)
       per_share = (amount / Decimal(total_user)).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
       # remainder due to rounding (ex: 100/3)
       remainder = amount - (per_share * total_user)
    #    print("this is reminder: ", remainder)
       with transaction.atomic():
           for u in user_list:
               share = per_share
               # Give remainder to payer (so total shares sum to amount)
               if User.objects.get(id=u) == payer:
                   share = per_share + remainder
            #    print("split:- ",payer,u,share,date,times)    
               Spilt.objects.create(expense=expense, user=User.objects.get(id=u), share=share,date=date,times=times,group_id=group_id) 
       return redirect('khata:home', f'{group_id}' )
    else:
        return render(request,"add_expense.html")
@login_required
def edit_expense(request,id):
    if request.method == "POST":
        price=request.POST.get("price")
        desc=request.POST.get("desc")
        group=request.POST.get("group")
        expense= Description.objects.get(id=id)
        expense.amount=price
        expense.description=desc
        expense.save()
        # expense= Description.objects.filter(id=id).update(amount=price,description=desc)
        # expense= Description.objects.get(id=id).update(amount=price,description=desc)
        split= get_list_or_404(Spilt,expense=expense)

        amount = Decimal(price)
        per_user=(amount/Decimal(len(split))).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
        reminder = amount - (per_user * Decimal(len(split)))

        # Spilt.objects.filter(expense=expense).update(share=per_user)
        Spilt.objects.filter(expense=expense).update(share=Case(When(user=expense.payer, then=per_user + reminder), default=per_user))
        # for i in split:
        #     print(i.share,per_user)
        #     i.share=per_user
        #     split.save()
        print(price,desc)
        print(len(split))
        return redirect("khata:admin_page",f"{group}")

    context={
        "exp_id":id,
        "pay":Description.objects.filter(id=id).prefetch_related('spilts')
        }
    return render(request,"edit.html",context)

@login_required
def delete_expense(request,group_id,id):
    expense= get_object_or_404(Description,id=id)
    expense.delete()
    # print(expense.amount,expense.payer)
    return redirect("khata:admin_page",group_id)



@login_required
def equalShareSplitor(request,id):
    if request.method=="POST":
       payer=User.objects.get(id=request.user.id)
       amount=request.POST.get('price')
       desc=request.POST.get('desc')
       date=datetime.now(asia_tz).date()
       times=datetime.now(asia_tz).strftime("%I:%M %p")
       user_list=request.POST.getlist('userss')
    #    print("this is Equal sharelist: ",payer,amount,desc,date,times,user_list)
       expense=EqualShare.objects.create(user=payer,group_id=id,amount=amount,desc=desc,date=date,times=times)
                        #    users = User.objects.exclude(id=1).filter(profile__is_online=True)

       total_user=len(user_list)

              
       amount = Decimal(amount)
       per_share = (amount / Decimal(total_user)).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
       # remainder due to rounding (ex: 100/3)
       remainder = amount - (per_share * total_user)
    #    print("this is reminder: ", remainder)
       with transaction.atomic():
           for u in user_list:
               share = per_share
               # Give remainder to payer (so total shares sum to amount)
               if User.objects.get(id=u) == payer:
                   share = per_share + remainder
            #    print("Equalshare split:- ",payer,u,share)    
               EqualShareSplit.objects.create(speaker=expense, user=User.objects.get(id=u), amount=share,date=date,times=times,group_id=id) 
       return redirect('khata:home', id)

@login_required
def shopping(request):
    if request.method=="POST":
       payer=User.objects.get(id=request.user.id)
       amount=request.POST.get('price')
       desc=request.POST.get('desc')
       date=datetime.now(asia_tz).date()
       times=datetime.now(asia_tz).strftime("%I:%M %p")

    #    print("this is user list: ",payer,amount,desc,date,times)
       expense=Shopping.objects.create(payer=payer,amount=amount,desc=desc,date=date,times=times)
    #    print("this is expense: ",expense)
       return redirect('khata:index')
    
    return render(request,"shopping.html",{"today_date":datetime.now()})

@login_required
def profile(request,group_id):

    # 7th to 7th date
    today = datetime.now(asia_tz)
    # Determine the current month and year
    group=get_object_or_404(Group,id=group_id)

    start_day= group.start_day
    current_month = today.month
    current_year = today.year
    # Calculate the start and end dates
    if today.day >= start_day:  # If today is the 8th or later, filter 8th of this month to 8th of next month
        start_date = datetime(current_year, current_month, start_day,tzinfo=asia_tz)
        if current_month == 12:  # Handle year-end transition
            end_date = datetime(current_year + 1, 1,start_day,tzinfo=asia_tz)
        else:
            end_date = datetime(current_year, current_month + 1, start_day,tzinfo=asia_tz)
    else:  # If today is before the 8th, filter 8th of last month to 8th of this month
        if current_month == 1:  # Handle year-start transition
            start_date = datetime(current_year - 1, 12, start_day,tzinfo=asia_tz)
        else:
            start_date = datetime(current_year, current_month - 1, start_day,tzinfo=asia_tz)
        end_date = datetime(current_year, current_month, start_day,tzinfo=asia_tz)
    # Format dates as MM/DD/YY for debugging or display
    formatted_start_date = start_date.strftime('%Y-%m-%d')
    formatted_end_date = end_date.strftime('%Y-%m-%d')

    # Total expense by current user
    total_expense = Description.objects.filter(payer=request.user,date__range=(formatted_start_date, formatted_end_date),group_id=group_id).aggregate(
        Sum('amount')
    )['amount__sum'] or 0
    #Total Shopping by current user
    total_Shopping_expense = Shopping.objects.filter(payer=request.user,date__range=(formatted_start_date, formatted_end_date)).aggregate(
            Sum('amount')
        )['amount__sum'] or 0

    # Sabhi users ka expense (group by payer)
    all_user_expense = (
    User.objects.annotate(
        balance=Sum(
            "paid_expenses__amount",
            filter=Q(paid_expenses__date__range=(formatted_start_date, formatted_end_date) , paid_expenses__group_id = group_id)
        )
    )
    .exclude(id__in=[request.user.id, 1])
)

    # Recent expenses of current user
    recent_expenses = Description.objects.filter(payer=request.user,date__range=(formatted_start_date, formatted_end_date),group_id=group_id).prefetch_related('spilts').order_by('-id')

    #Shopping of current user
    shopping_expenses = Shopping.objects.filter(payer=request.user,date__range=(formatted_start_date, formatted_end_date)).order_by('-id')

    #equal share model
    equal_share_expenses = EqualShare.objects.filter(group_id=group_id).prefetch_related('equalsharessplit').order_by('-id')
    return render(request, "profile.html", {
        "total_expense": total_expense,
        "group":group,
        "total_Shopping_expense": total_Shopping_expense,
        "all_user_expense": all_user_expense,
        "shopping_expenses": shopping_expenses,
        "equal_share_expenses": equal_share_expenses,
        "recent_expenses": recent_expenses,
    })


def signup_view(request):
    if request.method == "POST":
        username   = request.POST.get('username')
        email      = request.POST.get('email')
        firstname  = request.POST.get('first_name')
        lastname   = request.POST.get('last_name')
        password1  = request.POST.get('password1')
        password2  = request.POST.get('password2')

        # 1 Check empty fields
        if not all([username, email, firstname, lastname, password1, password2]):
            data = {
                "error": "All fields are required",
                "date": datetime.now(asia_tz).date(),
            }
            return render(request, "signup.html", data)

        # 2 Passwords match check
        if password1 != password2:
            data = {
                "error": "Passwords do not match",
                "date": datetime.now(asia_tz).date(),
            }
            return render(request, "signup.html", data)

        # 3 Check if username exists
        if User.objects.filter(username=username).exists():
            data = {
                "error": "Username already taken",
                "date": datetime.now(asia_tz).date(),
            }
            return render(request, "signup.html", data)

        # 4 Check if email exists
        if User.objects.filter(email=email).exists():
            data = {
                "error": "Email already exists",
                "date": datetime.now(asia_tz).date(),
            }
            return render(request, "signup.html", data)

        # 5 Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1,
            first_name=firstname,
            last_name=lastname
        )
        user.save()
        # print(" User created successfully")

        time.sleep(2)  # Optional: just to simulate a delay
        login(request, user)

        return redirect('khata:index')

    else:
        data = {
            "date": datetime.now(asia_tz).date(),
        }
        return render(request, "signup.html", data)

def login_view(request):
    if request.method=="POST":
        email=request.POST.get('email')
        password=request.POST.get('password')
        # print(email,password)
        try:
            user=User.objects.get(email=email)
            # print(user)
            user=authenticate(request,username=user.username,password=password)
            # print("this is user after authenticate: ",user)
            if user is not None:
                login(request,user)
                # print("user is logged in")
                return redirect('khata:index')
            else:
                data={
                    "error":"Invalid email or password",
                    "date":datetime.now(asia_tz).date(),
                }
                return render(request,"login.html",data)
        except User.DoesNotExist:
            data={
                "error":"Invalid email or password",
                "date":datetime.now(asia_tz).date(),
            }
            return render(request,"login.html",data)
    else:
        data={
            "date":datetime.now(asia_tz).date(),
        }
        return render(request,"login.html",data)
    
def index(request):
    groups = Group.objects.filter(group_memberships__user_id=request.user.id)   
    return render(request,"index.html",{"groups":groups})

@login_required
def create_group(request):
    if request.method == "POST":
        name = request.POST.get("name")
        start_day=request.POST.get("start_day")
        rent = request.POST.get("rent")
        users = request.POST.getlist("users")
        if rent is None or rent == "":
            rent = Decimal(0)
        if start_day is None or start_day=="":
            start_day= datetime.now().strftime("%d")
        group = Group.objects.create(
            name=name,
            rent=rent,
            start_day=start_day,
            created_by=request.user
        )

        GroupMember.objects.create(group=group, user=request.user, is_admin=True)

        for u in users:
            GroupMember.objects.create(group=group, user=User.objects.get(id=u))

        return redirect("khata:index")

    users = User.objects.exclude(id=request.user.id).exclude(id=1)
    return render(request, "create_group.html", {"users": users})

@login_required
def delete_group(request, id):
    if request.method == "POST":
        group = get_object_or_404(Group, id=id)
        group.delete()
    return redirect("khata:index")

@login_required
def add_member(request, id):
    group = get_object_or_404(Group, id=id)

    if request.method == "POST":
        name = request.POST.get("name")
        start_day = request.POST.get("start_day")
        rent = request.POST.get("rent")
        users = request.POST.getlist("users")

        # update group properly
        group.name = name
        group.rent = rent
        group.start_day = start_day
        group.save()

        # add members
        if users:
            for u in users:
                user_obj = User.objects.get(id=u)
                GroupMember.objects.create(group=group, user=user_obj)

        return redirect("khata:admin_page", id)

    # filter users not already in group
    users = User.objects.exclude(id=request.user.id).exclude(id=1)

    for u in users:
        if GroupMember.objects.filter(group=group, user=u).exists():
            users = users.exclude(id=u.id)

    context = {
        "group_id": id,
        "group_name": group.name,
        "group_rent": group.rent,
        "group_start_day": group.start_day,
        "users": users,
    }

    return render(request, "add_member.html", context)

@login_required
def remove_member(request, group_id, user_id):
    if request.method == "POST":
        group = get_object_or_404(Group, id=group_id)
        user = get_object_or_404(User, id=user_id)

        # prevent removing group creator (optional)
        if group.created_by == user:
            return redirect("khata:admin_page", group_id)

        GroupMember.objects.filter(group=group, user=user).delete()

        return redirect("khata:admin_page", group_id)

def admin_page(request,group_id):
    if User.objects.all().count() > 0:
        today = datetime.now(asia_tz)
        rent= Group.objects.get(id=group_id).rent
        start_day= Group.objects.get(id=group_id).start_day
    #     # Determine the current month and year
        current_month = today.month
        current_year = today.year

        # Calculate the start and end dates
        if today.day >= start_day:  # If today is the 8th or later, filter 8th of this month to 8th of next month
            start_date = datetime(current_year, current_month, start_day,tzinfo=asia_tz)
            if current_month == 12:  # Handle year-end transition
                end_date = datetime(current_year + 1, 1,start_day,tzinfo=asia_tz)
            else:
                end_date = datetime(current_year, current_month + 1, start_day,tzinfo=asia_tz)
        else:  # If today is before the 8th, filter 8th of last month to 8th of this month
            if current_month == 1:  # Handle year-start transition
                start_date = datetime(current_year - 1, 12, start_day,tzinfo=asia_tz)
            else:
                start_date = datetime(current_year, current_month - 1, start_day,tzinfo=asia_tz)
            end_date = datetime(current_year, current_month, start_day,tzinfo=asia_tz)

        # Format dates as MM/DD/YY for debugging or display
        formatted_start_date = start_date.strftime('%Y-%m-%d')
        name_start_date=start_date.date()
        formatted_end_date = end_date.strftime('%Y-%m-%d')

        descc=Description.objects.filter(date__range=(formatted_start_date, formatted_end_date),group=group_id).prefetch_related('spilts').order_by('-id')
        users = User.objects.exclude(id=1).filter(group_memberships__group=group_id)
        online_users = User.objects.exclude(id=1).filter(profile__is_online=True,group_memberships__group=group_id)
      
        rent_per_user = Decimal(rent) / Decimal(len(online_users)) if len(online_users) > 0 else Decimal(0)

        group_name= Group.objects.get(id=group_id).name
        def get_user_balance(user):
            user_expenses = (
                Description.objects
                .filter(date__range=(formatted_start_date, formatted_end_date), payer=user,group=group_id)
                .aggregate(total_amount=Sum('amount'))  # aggregate one number
            )

            spilt_expense = (
                Spilt.objects
                .filter(date__range=(formatted_start_date, formatted_end_date), user=user,group=group_id)
                .aggregate(total_amount=Sum('share'))  # aggregate one number Spilt.objects
            )
            equal_share=(
                EqualShareSplit.objects
                .filter(date__range=(formatted_start_date, formatted_end_date), user=user,group=group_id)
                .aggregate(total_amount=Sum('amount'))  # aggregate one number
            )
           
            credit = user_expenses["total_amount"] or Decimal(0)
            debit = spilt_expense["total_amount"] or Decimal(0)
            sharing = equal_share["total_amount"] or Decimal(0)
          
            if user.profile.is_online:
                user_rent = rent_per_user
            else:
                user_rent = Decimal(0)
            return ( user_rent + debit - credit + sharing).quantize(Decimal('0.01'))
            # return (Decimal(credit) - Decimal(debit)).quantize(Decimal('0.01'))

        balances = []
        for u in users:
            balances.append({
                'user': u,
                'balance': get_user_balance(u)
            })

        # print("this is balance :", balances)
        total_balance = sum(b['balance'] for b in balances)

        data={
                "objs":descc,
                "group_id":group_id,
                "group_name":group_name,
                "online_users": zip_longest(users,balances,fillvalue=0),
                "start_date":name_start_date,
                "total_balance":total_balance,
                "rent_per_user":rent_per_user.quantize(Decimal('0.01')),
                "rent_user_count":online_users,
                "today_date":datetime.now().date(),
        }
    return render(request,"admin_page.html",data)

def log_out(request):
    if request.method=="POST":
        logout(request)
    return redirect('khata:index')


