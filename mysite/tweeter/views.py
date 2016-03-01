from django.shortcuts import render
from django import forms

class TweetForm(forms.Form):
    tweet = forms.CharField(label='Tweet here', max_length=140)



def index(request):
    if request.method == 'POST':
        form = TweetForm(request.POST)
        if form.is_valid():
            return render(request, 'tweeter.html', {'form': form, 'message': form.cleaned_data })
    form = TweetForm()
    return render(request, 'tweeter.html', {'form': form})