from django.db import models
from pymongo import MongoClient

class GoogleTakeoutFile(models.Model):
    file_name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)

client = MongoClient('localhost', 27017)
db = client['datapunk_mongo']
collection = db['parsed_data']