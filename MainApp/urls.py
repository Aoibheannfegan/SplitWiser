from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path('expenses', views.expenses, name ="expenses"),
    path('owing', views.owing, name ="owing"),
    path('add_expense', views.addExpense, name ="add_expense"),
    path('<int:expense_id>', views.individualExpense, name ="individual_expense"),
    path('groups', views.groups, name ="groups"),
    path('add_group', views.addGroup, name ="add_group"),
    path('add_friend', views.addFriend, name ="add_friend"),
    path("get_group_members/<int:group_id>/", views.get_group_members, name="get_group_members"),
    path("make_payment/<int:expense_id>/", views.make_payment, name="make_payment"),
    path("get_dashboard_data", views.get_dashboard_data, name="dashboard_data"),
    path("get_friends_group_filtered_data/<int:friend_id>/<int:group_id>/", views.get_filtered_data, name="filtered_data_with_params"),
    path("get_friends_filtered_data/<int:friend_id>", views.get_filtered_data, name="filtered_data_friends"),
    path("get_group_filtered_data/<int:group_id>", views.get_filtered_data, name="filtered_data_groups"),
    path('groups/<int:group_id>', views.individualGroup, name ="individual_group"),
    path('friends/<int:friend_id>', views.individualFriend, name ="individual_friend"),
    path('friends/add_payment', views.add_payment, name ="add_payment"),
]


