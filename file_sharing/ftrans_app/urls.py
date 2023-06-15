from django.contrib import admin
from django.urls import path
from . import views

app_name = 'ftrans_app'

urlpatterns = [
    path('',views.file_list, name='index'),
    path('example/',views.example, name='example'),
    path('enkripsi',views.enkripsi, name='enkripsi'),
    path('dekripsi',views.dekripsi, name='dekripsi'),
    path('decrypt_file/',views.decrypt_file, name='decrypt_file'),
    # path('encrypt/', views.encrypt_file, name='encrypt'),
    # path('login',views.login, name='login'),
    path('encrypted', views.encrypt_file, name='encrypt_file'),
    path('generate-key/', views.form_generate, name='generate'),
    path('generate/', views.generate_key_view, name='generateKey'),
    path('download_file/', views.download_file, name='download_file'),
    path('signup/',views.signup, name='signup'),
    path('signout/',views.signout, name='signout'),
    path('login/',views.signin, name='login'),
]