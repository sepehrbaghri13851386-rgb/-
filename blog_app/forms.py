from django import forms
from .models import BlogPost


class BlogPostForm(forms.ModelForm):
    class Meta:
        model = BlogPost
        fields = ['title', 'image', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام بلاگ'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control-file', 'accept': 'image/*'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 10,
                                                 'placeholder': 'توضیحات بلاگ را اینجا بنویسید...'}),
        }