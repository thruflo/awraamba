#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Provides a ``mapping`` of ``/request/path``s to ``RequestHandler``s."""

import schema
import views

mapping = [
    (r'/', views.Index),
    (r'/signup', views.Signup),
    (r'/client_strings.json', views.ClientStrings),
    (r'/.*', views.NotFound)
]
