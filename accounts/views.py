from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages

# Por ahora solo usaremos las vistas de autenticación de Django
# Más adelante podemos agregar vistas personalizadas si es necesario