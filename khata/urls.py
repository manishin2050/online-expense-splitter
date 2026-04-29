from django.urls import path
from khata import views
app_name = 'khata'
urlpatterns = [
   
    path('', views.index,name="index" ),
    path('home/<int:group_id>/', views.home, name='home'),
    path('create_group/', views.create_group,name="create_group" ),
    path('delete_group/<int:id>/', views.delete_group, name="delete_group" ),
    path('add_member/<int:id>', views.add_member,name="add_member" ),
    path('remove_member/<int:group_id>/<int:user_id>/', views.remove_member, name='remove_member'),
    path('add/<int:group_id>/', views.add_expense,name="add_expense" ),
    path('edit/<int:id>/', views.edit_expense,name="edit_expense" ),
    path('delete_expense/<int:group_id>/<int:id>/', views.delete_expense,name="delete_expense" ),
    path('equalShareSplitor/<int:id>', views.equalShareSplitor,name="equalShareSplitor" ),
    path('download/<int:id>/', views.download, name='download'),
    path('download/<int:group_id>/<str:start_date>/<str:end_date>', views.download_pdf, name='download_pdf'),
    path('shopping/', views.shopping, name='shopping'),
    path('profile/<int:group_id>/', views.profile, name='profile'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('admin_page/<int:group_id>/', views.admin_page,name="admin_page" ),
    path('logout/', views.log_out, name='logout'),
]
