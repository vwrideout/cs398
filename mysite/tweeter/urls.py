# -*- coding: utf-8 -*-
"""
Created on Mon Feb 22 19:44:11 2016

@author: Vincent
"""

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
]