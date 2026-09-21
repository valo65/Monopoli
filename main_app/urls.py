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
]