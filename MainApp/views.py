from django.shortcuts import get_object_or_404, render, redirect
from django.http import Http404, HttpResponse, HttpResponseRedirect, JsonResponse
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django import forms
from django.urls import reverse
from django.utils import timezone
from django.db.models import Q, Sum, Case, When, DecimalField, F
from django.db.models.functions import Concat
from django.template import RequestContext
from django.core.exceptions import ObjectDoesNotExist
import datetime
import markdown
import json

from .models import Friends, PaymentGroup, Expense, Owing, User
from .utils.charts import colorPrimary, colorOwed, colorOwe, generate_color_palette

class NewExpenseForm(forms.Form):
    expense = forms.DecimalField(label="Amount", widget=forms.TextInput(attrs={'class': 'form-inputs', 'id': 'expense-amount-input'}), required=True)
    description = forms.CharField(label="Description of expense", widget=forms.TextInput(attrs={'class': 'form-inputs'}), required=True)
    currency = forms.ChoiceField(label="Currency", choices=Expense.CURRENCY_CHOICES, initial='CAD', widget=forms.Select(attrs={'class': 'form-inputs'}))
    # split_between = forms.ModelMultipleChoiceField(label="Split Between", queryset=User.objects.all(), widget=forms.SelectMultiple(attrs={'class': 'form-inputs'}))
    
class NewGroupForm(forms.Form):
    title = forms.CharField(label="Name of Group", widget=forms.TextInput(attrs={'class': 'form-inputs'}))
    members = forms.ModelMultipleChoiceField(label="Members", queryset=User.objects.all(), widget=forms.SelectMultiple(attrs={'class': 'form-inputs'}))

class AddFriendForm(forms.Form):
    email = forms.EmailField(label="Email Address", widget=forms.TextInput(attrs={'class': 'form-inputs'}))



def index(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))
    
    user = request.user
    owe_sum = Owing.objects.filter(user=user, paid=False).aggregate(total_remaining_balance=Sum('remaining_balance'))
    total_remaining_balance = owe_sum['total_remaining_balance'] or 0
    count_of_owing_to_me_expenses = len(Expense.objects.filter(created_by_user=user, paid=False))

    owed_sum = Owing.objects.filter(expense__created_by_user = user, paid=False).aggregate(total_remaining_balance=Sum('remaining_balance'))
    total_outstanding_balance = owed_sum['total_remaining_balance'] or 0
    count_of_owed_by_me_expenses = len(Owing.objects.filter(user=user, paid=False))

    try:
        friends = Friends.objects.get(user=user).friends.all()
    except Friends.DoesNotExist:
        friends = None

    friends_owe = Owing.objects.filter(expense__created_by_user=user,paid=False).exclude(user=user).values('user__username').annotate(total_owed=Sum('amount'))
    owed_sum = Owing.objects.filter(expense__created_by_user=user).aggregate(total_remaining_balance=Sum('remaining_balance'))
    total_outstanding_balance = owed_sum['total_remaining_balance'] or 0
    for friend in friends_owe:
        friend['percentage'] = (friend['total_owed'] / total_outstanding_balance) * 100 if total_outstanding_balance != 0 else 0

    owe_sum = Owing.objects.filter(user=user).aggregate(total_remaining_balance=Sum('remaining_balance'))
    total_remaining_balance = owe_sum['total_remaining_balance'] or 0
    groups_owe = Owing.objects.filter(user=user, paid=False).exclude(expense__created_by_user=user).values('expense__payment_group__group_name').annotate(total_owed=Sum('amount'))
    for group in groups_owe:
        group['percentage'] = (group['total_owed'] / total_remaining_balance) * 100 if total_remaining_balance != 0 else 0


    groups = PaymentGroup.objects.filter(members = user)

    recent_expenses = Expense.objects.filter(
        Q(created_by_user=user) | Q(sub_expenses__user=user)
    ).order_by('-date_added')

    # Filter out duplicate expenses
    unique_expenses = []
    seen_ids = set()
    for expense in recent_expenses:
        if expense.id not in seen_ids:
            unique_expenses.append(expense)
            seen_ids.add(expense.id)

    # Limit the list to 10 unique expenses
    recent_expenses = unique_expenses[:10]

    return render(request, "MainApp/index.html", {
        "owed_by_me_balance": total_remaining_balance, 
        "owed_to_me_balance": total_outstanding_balance,
        "groups": groups,
        "friends": friends,
        "expenses_owed_to_me_count": count_of_owing_to_me_expenses,
        "expenses_owed_by_me_count": count_of_owed_by_me_expenses,
        "friends_owe": friends_owe,
        "groups_owe": groups_owe,
        "recent_expenses": recent_expenses,
    })

def login_view(request):
    if request.method == "POST":
        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        # Check if authentication successful
        if user is not None:
            print('user confirmed')
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            print('issue verifying user')
            return render(request, "MainApp/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "MainApp/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        first_name = request.POST["first_name"]
        last_name = request.POST["last_name"]
        username = request.POST["username"]
        email = request.POST["email"]
        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "MainApp/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
            user.first_name = first_name
            user.last_name = last_name
            user.save()
        except IntegrityError:
            return render(request, "MainApp/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "MainApp/register.html")


@login_required
def expenses(request):
    user = request.user
    if "expenses" not in request.session:
        request.session["expenses"] = []
    
    # get expenses and group by creation date
    expense_objects = Expense.objects.filter(created_by_user=user).order_by('date_added')
    expenses_by_date = {}
    for expense_obj in expense_objects:
        date_added = expense_obj.date_added.date()
        if date_added not in expenses_by_date:
            expenses_by_date[date_added] = []
        expenses_by_date[date_added].append(expense_obj)
    expenses_by_date = dict(sorted(expenses_by_date.items(), key=lambda x: x[0], reverse=True))
    today = timezone.now().date()

    # Calculate the total owed by friends to current user
    friends = Owing.objects.filter(expense__created_by_user=user,paid=False).exclude(user=user).values('user__username').annotate(total_owed=Sum('amount'))
    owed_sum = Owing.objects.filter(expense__created_by_user=user).aggregate(total_remaining_balance=Sum('remaining_balance'))
    total_outstanding_balance = owed_sum['total_remaining_balance'] or 0
    for friend in friends:
        friend['percentage'] = (friend['total_owed'] / total_outstanding_balance) * 100 if total_outstanding_balance != 0 else 0


    return render(request, "MainApp/expenses.html", {
        "expenses": Expense.objects.filter(created_by_user=user).order_by('date_added'),
        "expenses_by_date": expenses_by_date,
        "today": today,
        "friends": friends,
        "total_owed": total_outstanding_balance,
    })

@login_required
def owing(request):
    user = request.user

    if "owing" not in request.session:
        request.session["owing"] = []

    owing_objects = Owing.objects.filter(user=user, paid=False).order_by('-expense__date_added')

    # Create a dictionary to hold expenses grouped by creation date
    expenses_by_date = {}

    # Group the expenses by creation date
    for owing_obj in owing_objects:
        date_added = owing_obj.expense.date_added.date()
        if date_added not in expenses_by_date:
            expenses_by_date[date_added] = []
        expenses_by_date[date_added].append(owing_obj)

    # Sort the grouped expenses by date in descending order
    expenses_by_date = dict(sorted(expenses_by_date.items(), key=lambda x: x[0], reverse=True))

    # Get today's date
    today = timezone.now().date()

    # Calculate the total owed by the user
    owe_sum = Owing.objects.filter(user=user).aggregate(total_remaining_balance=Sum('remaining_balance'))
    total_remaining_balance = owe_sum['total_remaining_balance'] or 0

    # Calculate the percentage for each group
    groups = Owing.objects.filter(user=user, paid=False).exclude(expense__created_by_user=user).values('expense__payment_group__group_name').annotate(total_owed=Sum('amount'))
    for group in groups:
        group['percentage'] = (group['total_owed'] / total_remaining_balance) * 100 if total_remaining_balance != 0 else 0

    return render(request, "MainApp/owing.html", {
        "expenses_by_date": expenses_by_date,
        "today": today,
        "owing": Owing.objects.filter(user=user, paid=False).order_by('-expense__date_added'),
        "groups": groups,
        "total_owed": total_remaining_balance,
    })


@login_required
def addExpense(request):
    if request.method == "POST":
        user = request.user
        form_data = json.loads(request.body)
        expense_data = form_data.get('expenseInputs', {})
        user_inputs = form_data.get('userInputs', {})
        group_input = form_data.get('group')
        amount = expense_data.get('amount')
        description = expense_data.get('description')
        currency = 'CAD'

        if group_input:
            group = PaymentGroup.objects.get(group_name=group_input)
            expense=Expense(amount=amount, remaining_balance=amount, description=description, currency=currency, created_by_user=user, payment_group = group)
            expense.save()
        else:
            expense=Expense(amount=amount, remaining_balance=amount, description=description, currency=currency, created_by_user=user)
            expense.save()


        for username, amount_owed in user_inputs.items():
            selected_user = User.objects.get(username=username) 
            if selected_user == user:
                owing=Owing(expense=expense, user=user, amount=amount_owed, remaining_balance = 0, paid=True)
                owing.save()
                expense.remaining_balance = float(expense.remaining_balance) - float(owing.amount)
                expense.save()
            else:  
                owing=Owing(expense=expense, user=selected_user, amount=amount_owed, remaining_balance=amount_owed)
                owing.save()
        
        return JsonResponse({"message": "Successfully added"})
    
    else:
        user = request.user
        if not user.is_authenticated:
            return HttpResponseRedirect(reverse("login"))

        groups = PaymentGroup.objects.filter(members=user)
        friends = User.objects.exclude(id = user.id)
        user = request.user
        return render(request, "MainApp/addexpense.html", {
            "groups": groups,
            "friends": friends,
            "user": request.user
        })

@login_required
def addGroup(request): 
    if request.method == "POST":
        user = request.user
        form_data = json.loads(request.body)
        # print(form_data)
        group_name = form_data.get('group_name')
        print(f"Group Name: {group_name}")
        group_members = form_data.get('members', {})
        group=PaymentGroup(group_name=group_name)
        group.save()

        for user_id, username in group_members.items():
            selected_user = User.objects.get(username=username) 
            group.members.add(selected_user)
        return JsonResponse({"message": "Successfully added"})
    user = request.user
    friends = User.objects.exclude(id = user.id)
    return render(request, "MainApp/addgroup.html", {
        "form": NewGroupForm(),
        "friends": friends,
        "user": user,
    })

@login_required
def addFriend(request): 
    if request.method == "POST":
        user = request.user
        form_data = json.loads(request.body)
        email = form_data.get('email')

        try:
            friend = User.objects.get(email=email)
            if friend == user:
                return JsonResponse({"message": "Invalid Friend. User cannot add themselves"})
            else:
                if user.friends.filter(friends__email=email).exists():
                    return JsonResponse({"message": "Friend already added"})
                else:
                # if user exists with that email create or add to current users friends
                    currentUser, created = Friends.objects.get_or_create(user=user)
                    currentUser.friends.add(friend)
                    currentUser.save()
                    return JsonResponse({"message": "Successfully added"})
        except User.DoesNotExist: 
            return JsonResponse({"message": "No user found with that email"})

    try:
        current_user_friends = Friends.objects.get(user=request.user).friends.all()
        user=request.user
        if current_user_friends: 
            print('Yay, found friends!')
            friends=[]
            for friend_object in current_user_friends:
                friend = User.objects.get(username=friend_object.username)
                total_owed_by_me = Owing.objects.filter(user=user, expense__created_by_user=friend, paid=False).aggregate(total_owed_by_me=Sum('remaining_balance'))['total_owed_by_me'] or 0
                total_owed_to_me = Owing.objects.filter(user=friend, expense__created_by_user=request.user, paid=False).aggregate(total_owed_to_me=Sum('remaining_balance'))['total_owed_to_me'] or 0
                net_total = total_owed_to_me - total_owed_by_me
                friends.append({
                    'friend': friend,
                    'total_owed_by_me': total_owed_by_me,
                    'total_owed_to_me': total_owed_to_me,
                    'net_total': net_total
                })
        else:
            print('no friends')
            friends = None
    except ObjectDoesNotExist:
        print('No Friends object found for the current user.')
        friends = None
    return render(request, "MainApp/addfriend.html", {
        "form": AddFriendForm(),
        "friends": friends,
    })

@login_required
def individualExpense(request, expense_id): 
    user = request.user
    expense = Expense.objects.get(id=expense_id)
    split_between = Owing.objects.filter(expense=expense_id)
    return render(request, "MainApp/individualexpense.html", {
        "expense": expense,
        "split_between": split_between,
        "current_user": user,
    })

@login_required
def individualGroup(request, group_id): 
    user = request.user
    group_details = PaymentGroup.objects.get(id=group_id)
    members = PaymentGroup.objects.get(id=group_id).members.all()
    group_members = {}
    for member in members: 
        owed_by_me = Owing.objects.filter(user=user, expense__created_by_user = member, expense__payment_group = group_details).aggregate(total_amount=Sum('remaining_balance'))['total_amount'] or 0
        owed_to_me = Owing.objects.filter(user=member, expense__created_by_user=request.user, expense__payment_group=group_details).aggregate(total_amount=Sum('remaining_balance'))['total_amount'] or 0
        group_members[member.username] = {
            'net_owed': owed_to_me - owed_by_me,
            'member_id': member.id, 
        }
    group_expenses = PaymentGroup.objects.get(id=group_id).expenses.annotate(
    amount_lent=Case(
        When(
            created_by_user=user,  # If expense created by current user
            then=Sum(
                Case(
                    When(
                        sub_expenses__user=user,  # Exclude sub_expenses where user is current user
                        then=0
                    ),
                    default=F('sub_expenses__amount'),  # Sum the amounts of remaining sub_expenses
                    output_field=DecimalField()
                )
            )
        ), 
        When(
            ~Q(created_by_user=user),  # If expense not created by current user
            then=F('sub_expenses__amount')  # Sum amounts from Owing objects where the user is the current user
        ), 
        default=0,  # Default to 0
        output_field=DecimalField()
    )
).order_by('-date_added')
    owed_to_you = Owing.objects.filter(expense__created_by_user = user, expense__payment_group = group_details).aggregate(total_amount=Sum('remaining_balance'))['total_amount'] or 0
    owed_by_you = Owing.objects.filter(user = user, expense__payment_group = group_details).aggregate(total_amount=Sum('remaining_balance'))['total_amount'] or 0
    net_total = owed_to_you - owed_by_you
    return render(request, "MainApp/individualgroup.html", {
        "group_expenses": group_expenses,
        "group_details": group_details,
        "group_members": group_members,
        "user": user,
        "net_total": net_total,
    })

@login_required
def individualFriend(request, friend_id): 
    user = request.user
    friend = User.objects.get(id=friend_id)
    print(f'friend is {friend}')
    owed_by_me = Owing.objects.filter(user=user, expense__created_by_user = friend, paid=False).aggregate(total_amount=Sum('remaining_balance'))['total_amount'] or 0
    owed_to_me = Owing.objects.filter(user=friend, expense__created_by_user=user, paid=False).aggregate(total_amount=Sum('remaining_balance'))['total_amount'] or 0
    net_total_owed = owed_to_me - owed_by_me

    friend_expenses = Owing.objects.filter(
        Q(user=friend, expense__created_by_user=user) |
        Q(user=user, expense__created_by_user=friend)
    ).order_by('-expense__date_added')
    return render(request, "MainApp/individualfriend.html", {
        "user": user,
        "friend": friend,
        "net_total": net_total_owed,
        "owed_by_me": owed_by_me,
        "owed_to_me": owed_to_me,
        "friend_expenses": friend_expenses

    })


@login_required
def groups(request):
    user = request.user
    user_groups = PaymentGroup.objects.filter(members=user)
    
    user_groups = PaymentGroup.objects.filter(members=user).annotate(
        total_owed_by_me=Sum(Case(
            When(expenses__sub_expenses__user=user, expenses__sub_expenses__paid=False, then=F('expenses__sub_expenses__amount')),
            default=0,
            output_field=DecimalField()
        )),
        total_owed_to_me=Sum(Case(
            When(expenses__created_by_user=user, expenses__sub_expenses__paid=False, then=F('expenses__sub_expenses__amount')),
            default=0,
            output_field=DecimalField()
        )), 
    ).annotate(
        net_total=F('total_owed_to_me') - F('total_owed_by_me')
    )

    
    return render(request, "MainApp/groups.html", {
        "groups": user_groups,
       
    })

@login_required
def get_group_members(request, group_id):
    if group_id == 100000:
        members = User.objects.all()
    else:
        group = PaymentGroup.objects.get(id=group_id)
        members = group.members.all()
    data = {'members': [{'id': member.id, 'username': member.username} for member in members]}
    return JsonResponse(data)

@login_required
def make_payment(request, expense_id):
    if request.method == "POST":
        user = request.user
        expense = Expense.objects.get(id=expense_id)
        try:
            # get users current outstanding balance for this expense
            owed = Owing.objects.get(expense=expense, user=user) 
            amount = request.POST["amount"]
            individual_balance_remaining = owed.remaining_balance

            print(f"Expense Remaining Balance:{expense.remaining_balance} Indivdual Remaining Balance: {individual_balance_remaining} Amount: {amount}")
            
            # check if they paid expense in full
            if individual_balance_remaining - int(amount) == 0:
                owed.paid = True
                print(owed.paid)

            #update users remaining balance for this expense as well as the total remaining balance on expense
            owed.remaining_balance = int(individual_balance_remaining) - int(amount) 
            owed.save()
            expense.remaining_balance = int(expense.remaining_balance) - int(amount)
            expense.save()

            print(f"Remaining Balance on total: {expense.remaining_balance}")
            print(f"Remaining Balance on individual: {owed.remaining_balance}")
        
        except Owing.DoesNotExist:
            pass
        
        return redirect('individual_expense', expense_id=expense.id)
    
    user = request.user
    expense = Expense.objects.get(id=expense_id)
    return render(request, "MainApp/makepayment.html", {
        "expense": Owing.objects.get(expense=expense,user=user),
        "expense_id": expense_id,
    })

@login_required
def add_payment(request):
    if request.method == "POST":
        form_data = json.loads(request.body)
        user_input = form_data.get('user')
        friend_input = form_data.get('friend')
        
        amount = float(form_data.get('amount'))
        user = User.objects.get(username=user_input)
        friend = User.objects.get(username=friend_input)

        expenses_owed = Owing.objects.filter(
            Q(user=friend, expense__created_by_user=user) |
            Q(user=user, expense__created_by_user=friend)
        ).order_by('-expense__date_added')
        

        for expense in expenses_owed:
            expense.paid = True
            expense.save()

        return JsonResponse({"message": "Successfully added"})

    else:
        return redirect('add_friend')


@login_required
def get_dashboard_data(request):
    user = request.user
    # Get data for "What You Owe" chart
    owe_sum = Owing.objects.filter(user=user).aggregate(total_remaining_balance=Sum('remaining_balance'))
    total_remaining_balance = owe_sum['total_remaining_balance'] or 0
    
    owed_sum = Owing.objects.filter(expense__created_by_user=user).aggregate(total_remaining_balance=Sum('remaining_balance'))
    total_outstanding_balance = owed_sum['total_remaining_balance'] or 0

    # Get data for "Friends Owe" chart
    friends_owe = Owing.objects.filter(expense__created_by_user=user,paid=False).exclude(user=user).values('user__username').annotate(total_owed=Sum('amount'))

    # Get data for "Friends Owed" chart
    friends_owed = Owing.objects.filter(user=user, paid=False).exclude(expense__created_by_user=user).values('expense__created_by_user__username').annotate(total_owed=Sum('amount'))

    # Get data for "Groups Owe" chart
    groups_owe = Owing.objects.filter(expense__created_by_user=user,paid=False).exclude(user=user).values('expense__payment_group__group_name').annotate(total_owed=Sum('amount'))

    # Get data for "Groups Owed" chart
    groups_owed = Owing.objects.filter(user=user,paid=False).exclude(expense__created_by_user=user).values('expense__payment_group__group_name').annotate(total_owed=Sum('amount'))

    user_groups = PaymentGroup.objects.filter(members=user).prefetch_related('members')

    return JsonResponse({
        "user_owes": {
            "title": "What You Owe",
            "data": {
                "labels": ["Owed", "Owe"],
                "datasets": [{
                    "label": "Outstanding Balances",
                    "backgroundColor": [colorOwed, colorOwe],
                    "borderColor": [colorOwed, colorOwe],
                    "data": [
                        total_outstanding_balance,
                        total_remaining_balance,
                    ]
                }]
            }
        },
        "friends_owe": {
            "title": "Friends Owe",
            "data": {
                "labels": [friend['user__username'] for friend in friends_owe],
                "datasets": [{
                    "label": "Owes",
                    "backgroundColor": generate_color_palette(len(friends_owe)),
                    "borderColor": generate_color_palette(len(friends_owe)),
                    "data": [friend['total_owed'] for friend in friends_owe],
                }]
            }
        },
        "friends_owed": {
            "title": "Friends Owed",
            "data": {
                "labels": [friend['expense__created_by_user__username'] for friend in friends_owed],
                "datasets": [{
                    "label": "Owed",
                    "backgroundColor": generate_color_palette(len(friends_owed)),
                    "borderColor": generate_color_palette(len(friends_owed)),
                    "data": [friend['total_owed'] for friend in friends_owed],
                }]
            }
        },
        "groups_owe": {
            "title": "Groups Owe",
            "data": {
                "labels": [group['expense__payment_group__group_name'] for group in groups_owe],
                "datasets": [{
                    "label": "Owes",
                    "backgroundColor": generate_color_palette(len(groups_owe)),
                    "borderColor": generate_color_palette(len(groups_owe)),
                    "data": [group['total_owed'] for group in groups_owe],
                }]
            }
        },
        "groups_owed": {
            "title": "Groups Owed",
            "data": {
                "labels": [group['expense__payment_group__group_name'] for group in groups_owed],
                "datasets": [{
                    "label": "Owed",
                    "backgroundColor": generate_color_palette(len(groups_owed)),
                    "borderColor": generate_color_palette(len(groups_owed)),
                    "data": [group['total_owed'] for group in groups_owed],
                }]
            }
        },
        "user_groups": {
            "data": [
                {
                    group.group_name:[member.username for member in group.members.all()]
                }
                for group in user_groups
            ]
        }
    })

@login_required
def get_filtered_data(request, friend_id=None, group_id=None):
    user = request.user
    if friend_id is not None:
        friend = User.objects.get(id=friend_id)
    if group_id is not None:
        group = PaymentGroup.objects.get(id=group_id)
    
    if friend_id is not None and group_id is not None:
        owe_sum = Owing.objects.filter(user=user, expense__created_by_user=friend, expense__payment_group=group).aggregate(total_remaining_balance=Sum('remaining_balance'))
        owed_sum = Owing.objects.filter(expense__created_by_user=user, user=friend, expense__payment_group=group).aggregate(total_remaining_balance=Sum('remaining_balance'))
        
        friends_owe = Owing.objects.filter(expense__created_by_user=user,expense__payment_group=group, user=friend,paid=False).exclude(user=user).values('user__username').annotate(total_owed=Sum('amount'))
        friends_owed = Owing.objects.filter(user=user, expense__payment_group=group, paid=False).exclude(expense__created_by_user=friend).values('expense__created_by_user__username').annotate(total_owed=Sum('amount'))

        groups_owe = Owing.objects.filter(expense__created_by_user=user,expense__payment_group=group,user=friend,paid=False).exclude(user=user).values('expense__payment_group__group_name').annotate(total_owed=Sum('amount'))
        groups_owed = Owing.objects.filter(user=user,expense__created_by_user=friend,expense__payment_group=group,paid=False).exclude(expense__created_by_user=user).values('expense__payment_group__group_name').annotate(total_owed=Sum('amount'))


    elif friend_id is not None:
        owe_sum = Owing.objects.filter(user=user, expense__created_by_user=friend).aggregate(total_remaining_balance=Sum('remaining_balance'))
        owed_sum = Owing.objects.filter(expense__created_by_user=user, user=friend).aggregate(total_remaining_balance=Sum('remaining_balance'))
        
        friends_owe = Owing.objects.filter(expense__created_by_user=user,user=friend,paid=False).exclude(user=user).values('user__username').annotate(total_owed=Sum('amount'))
        friends_owed = Owing.objects.filter(user=user, paid=False).exclude(expense__created_by_user=friend).values('expense__created_by_user__username').annotate(total_owed=Sum('amount'))
        
        groups_owe = Owing.objects.filter(expense__created_by_user=user,user=friend,paid=False).exclude(user=user).values('expense__payment_group__group_name').annotate(total_owed=Sum('amount'))
        groups_owed = Owing.objects.filter(user=user,expense__created_by_user=friend,paid=False).exclude(expense__created_by_user=user).values('expense__payment_group__group_name').annotate(total_owed=Sum('amount'))

        
    elif group_id is not None:
        owe_sum = Owing.objects.filter(user=user, expense__payment_group=group).aggregate(total_remaining_balance=Sum('remaining_balance'))
        owed_sum = Owing.objects.filter(expense__created_by_user=user, expense__payment_group=group).aggregate(total_remaining_balance=Sum('remaining_balance'))
        
        friends_owe = Owing.objects.filter(expense__created_by_user=user,expense__payment_group=group, paid=False).exclude(user=user).values('user__username').annotate(total_owed=Sum('amount'))
        friends_owed = Owing.objects.filter(user=user, expense__payment_group=group, paid=False).values('expense__created_by_user__username').annotate(total_owed=Sum('amount'))

        groups_owe = Owing.objects.filter(expense__created_by_user=user,expense__payment_group=group,paid=False).exclude(user=user).values('expense__payment_group__group_name').annotate(total_owed=Sum('amount'))
        groups_owed = Owing.objects.filter(user=user,expense__payment_group=group,paid=False).exclude(expense__created_by_user=user).values('expense__payment_group__group_name').annotate(total_owed=Sum('amount'))

       
    else:
        owe_sum = Owing.objects.filter(user=user).aggregate(total_remaining_balance=Sum('remaining_balance'))
        owed_sum = Owing.objects.filter(expense__created_by_user=user).aggregate(total_remaining_balance=Sum('remaining_balance'))
        friends_owe = Owing.objects.filter(expense__created_by_user=user,paid=False).exclude(user=user).values('user__username').annotate(total_owed=Sum('amount'))
        friends_owed = Owing.objects.filter(user=user, paid=False).exclude(expense__created_by_user=user).values('expense__created_by_user__username').annotate(total_owed=Sum('amount'))
        groups_owe = Owing.objects.filter(expense__created_by_user=user,paid=False).exclude(user=user).values('expense__payment_group__group_name').annotate(total_owed=Sum('amount'))
        groups_owed = Owing.objects.filter(user=user,paid=False).exclude(expense__created_by_user=user).values('expense__payment_group__group_name').annotate(total_owed=Sum('amount'))
    
    total_remaining_balance = owe_sum['total_remaining_balance'] or 0
    total_outstanding_balance = owed_sum['total_remaining_balance'] or 0

    return JsonResponse({
        "user_owes": {
            "title": "What You Owe",
            "data": {
                "labels": ["Owed", "Owe"],
                "datasets": [{
                    "label": "Outstanding Balances",
                    "backgroundColor": [colorOwed, colorOwe],
                    "borderColor": [colorOwed, colorOwe],
                    "data": [
                        total_outstanding_balance,
                        total_remaining_balance,
                    ]
                }]
            }
        },
        "friends_owe": {
            "title": "Friends Owe",
            "data": {
                "labels": [friend['user__username'] for friend in friends_owe],
                "datasets": [{
                    "label": "Owes",
                    "backgroundColor": generate_color_palette(len(friends_owe)),
                    "borderColor": generate_color_palette(len(friends_owe)),
                    "data": [friend['total_owed'] for friend in friends_owe],
                }]
            }
        },
        "friends_owed": {
            "title": "Friends Owed",
            "data": {
                "labels": [friend['expense__created_by_user__username'] for friend in friends_owed],
                "datasets": [{
                    "label": "Owed",
                    "backgroundColor": generate_color_palette(len(friends_owed)),
                    "borderColor": generate_color_palette(len(friends_owed)),
                    "data": [friend['total_owed'] for friend in friends_owed],
                }]
            }
        },
        "groups_owe": {
            "title": "Groups Owe",
            "data": {
                "labels": [group['expense__payment_group__group_name'] for group in groups_owe],
                "datasets": [{
                    "label": "Owes",
                    "backgroundColor": generate_color_palette(len(groups_owe)),
                    "borderColor": generate_color_palette(len(groups_owe)),
                    "data": [group['total_owed'] for group in groups_owe],
                }]
            }
        },
        "groups_owed": {
            "title": "Groups Owed",
            "data": {
                "labels": [group['expense__payment_group__group_name'] for group in groups_owed],
                "datasets": [{
                    "label": "Owed",
                    "backgroundColor": generate_color_palette(len(groups_owed)),
                    "borderColor": generate_color_palette(len(groups_owed)),
                    "data": [group['total_owed'] for group in groups_owed],
                }]
            }
        }
    })
       