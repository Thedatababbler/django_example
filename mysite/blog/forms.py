from django import forms
class EmailPostForm(forms.Form):
    name = forms.CharField(max_length=25)
    email = forms.EmailField()
    to = forms.EmailField()
    comments = forms.CharField(required=False, widget=forms.Textarea)

from .models import Comment, subComment
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('name', 'email', 'body')
class subCommentForm(forms.ModelForm):
    class Meta:
        model = subComment
        fields = ('name', 'email', 'body')