from django.shortcuts import render


def show_visualization(request):
    # Generate or fetch visualization data here
    return render(request, 'visualizations/show.html')