from django import forms
from .models import Game, Field

class GameForm(forms.ModelForm):
    class Meta:
        model = Game
        fields = ['title', 'subject', 'description', 'center_image']

class FieldForm(forms.ModelForm):
    class Meta:
        model = Field
        fields = ['position', 'field_type', 'label', 'material_title', 'material_content', 'material_image', 'material_link']