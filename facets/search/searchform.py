from django import forms

from .models import Post

class SearchForm(forms.ModelForm):

    class Meta:
        model = Post
        fields = ('pattern')

