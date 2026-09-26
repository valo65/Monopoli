from django.urls import path, include
from . import views

app_name = 'main_app'

urlpatterns = [
    path('', views.index, name='index'),           # Начална страница
    path('about/', views.about, name='about'),     # За нас
    path('contact/', views.contact, name='contact'), # Контакти
    path('api/', include('main_app.api_urls')),  # НОВИЯТ API маршрут
    path('create-game/', views.create_game, name='create_game'),
    path('add-fields/<int:game_id>/', views.add_fields, name='add_fields'),
    path('play/<int:game_id>/', views.play_game, name='play_game'),
    path('roll-dice/<int:session_id>/', views.roll_dice, name='roll_dice'),
    path('groups/', views.group_list, name='group_list'),
    path('groups/create/', views.create_group, name='create_group'),
    path('groups/join/', views.join_group, name='join_group'),
    path('groups/<int:group_id>/', views.group_detail, name='group_detail'),
    path('groups/<int:group_id>/add-students/', views.add_students, name='add_students'),
    path('groups/<int:group_id>/start/', views.start_group_game, name='start_group_game'),
    path('show-material/<int:group_id>/', views.show_material, name='show_material'),
    path('submit-material-answer/<int:material_id>/', views.submit_material_answer, name='submit_material_answer'),
]
