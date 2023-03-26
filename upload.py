import boto3
import json
from collections import defaultdict
import pickle
import numpy

import os

region = 'us-east-1'
os.environ['AWS_ACCESS_KEY_ID'] = ""
os.environ['AWS_SECRET_ACCESS_KEY'] = ""

f_ptr = open('student_data.json')
json_dict = json.load(f_ptr)

table_name = "Student"
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(table_name)

for item in json_dict:
    table.put_item(Item=item)
    
print("All items uploaded to DynamoDB table 'student_data' ✅")

