from .models import Post, Comment
from django import forms


class PostCreateForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = [
          'image',
          'caption'
        ]


class CommentCreateForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = [
          'text',
        ]
        labels = {'text': 'Tu comentario'}
        widgets = {'text': forms.Textarea(attrs={'rows': 3})}
