from django import forms

from .models import Post, Comment

'''
Вопрос:
    В __init__ я не указывал, что поле group должно быть селектором, эл-тами
    которого являются все объекты модели Group, но при рендеринге все равно
    создается нужный селектор. То же самое касается поля text, изначально
    я не указывал св-во required, но именно у поля text оно изначально
    почему-то равно True, хотя у group оно False.

    Почему это так работает?
'''


class PostForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['text'].required = True

    class Meta:
        model = Post
        fields = ['text', 'group', 'image']


class CommentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['text'].required = True

    class Meta:
        model = Comment
        fields = ('text',)
