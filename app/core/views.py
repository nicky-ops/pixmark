from django.shortcuts import render


def landing_page(request):
    '''
    Rendering the landing page
    '''
    return render(request, 'core/landing_page.html')