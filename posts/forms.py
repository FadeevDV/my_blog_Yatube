from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ("group", "text", "image")
        labels = {"group": "Группа",
                  "text": "Наберите текст",
                  "image": "Выберите изображение"
                  }
        help_texts = {
            'text': 'Новая запись, не может быть пустой',
            'group': 'Не обязательно',
        }

    def clean_subject(self):
        data = self.cleaned_data['text']
        if data == '':
            raise forms.ValidationError("Это поле обязательно для заполнения")
        return data

class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ['text']

    def clean_subject(self):
        data = self.cleaned_data['text']
        if data == '':
            raise forms.ValidationError("Это поле обязательно для заполнения")
        return data
