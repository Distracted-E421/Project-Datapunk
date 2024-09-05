from django.shortcuts import render
from .models import GoogleTakeoutFile

def upload_file(request):
    if request.method == 'POST':
        uploaded_file = request.FILES['document']
        takeout_file = GoogleTakeoutFile(file_name=uploaded_file.name)
        takeout_file.save()
        # Handle parsing here
    return render(request, 'parsers/upload.html')
