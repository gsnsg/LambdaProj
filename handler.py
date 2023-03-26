from boto3 import client as boto3_client
import face_recognition
import pickle
import os
import sys
import boto3
import csv
import shutil


# Uncomment to test your code locally
# os.environ['AWS_ACCESS_KEY_ID'] = ""
# os.environ['AWS_SECRET_ACCESS_KEY'] = ""

# Function to read the 'encoding' file
def open_encoding(filename):
    file = open(filename, "rb")
    data = pickle.load(file)
    file.close()
    return data

# add "us-east-1" region to s3 and dynamodb to test locally
s3 = boto3.resource('s3')
dynamodb = boto3.resource('dynamodb')
table_name = "Student"
table = dynamodb.Table(table_name)

def parse_video(video_name, known_face_encodings, known_face_names):
    # print(encodings, names)
    path = "/tmp/"
    os.system("ffmpeg -i " + str(video_name) + " -r 1 " + str(path) + "image-%3d.jpeg")
    print("Video parsed successfully ✅")
    
    imgs = sorted([ img for img in os.listdir(path) if img.endswith(".jpeg")])
    # print(imgs)
    
    for img_name in imgs:
        if img_name.endswith(".jpeg"):
            img = face_recognition.load_image_file(path + img_name)
            face_encoding = face_recognition.face_encodings(img)[0]
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            if True in matches:
                first_match_index = matches.index(True)
                return known_face_names[first_match_index]
        else:
            continue
    
    return "Unknown"
    
    
def create_csv(filename, name, year, major):
    # Open the CSV file in write mode
    data = [ ["name", "major", "year"], [name, major, year]]
    with open(filename, mode='w', newline='') as csv_file:
        # Create a CSV writer object
        writer = csv.writer(csv_file)

        # Write the data to the CSV file
        for row in data:
            writer.writerow(row)

    print(f"{filename} created successfully!")
    
    
def face_recognition_handler(event, context):
    tmp = "/tmp/"
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    file_name = event['Records'][0]['s3']['object']['key']
    print("📎 Got bucket and file name", bucket_name, file_name)
    
    # bucket_name =  "ccinputvideos"# event['ccinputvideos']  # Replace with the name of your S3 bucket
    # file_name =  "test_0.mp4"# event['test_0.mp4']  # Replace with the name of your video file in the S3 bucket
    print("Downloading file from S3 bucket {} to {}".format(bucket_name, file_name))
    
    # load encoding file
    encodings = open_encoding("encoding")
    
    # download the file from S3 bucket
    # Reference: https://stackoverflow.com/questions/39383465/error-read-only-file-system-in-aws-lambda-when-downloading-a-file-from-s3
    s3.Bucket("ccinputvideos").download_file(file_name, "/tmp/" + file_name)
    
    result = parse_video(tmp + file_name, encodings['encoding'], encodings['name'])
    
    print("🚀 Result: ", result)
    
    response = table.get_item(
        Key = {
            'name': result
        }
    )
    
    print("🥳 Response: ", response)
    
    year, major = response['Item']['year'], response['Item']['major']
   
    csv_file = file_name.split(".")[0] + ".csv"
    create_csv(tmp + csv_file, result, year, major)
    
    with open(tmp + csv_file, 'rb') as f:
        s3.Bucket("ccoutputvideos").upload_fileobj(f, csv_file)
        
    print(f"{csv_file} uploaded to ccoutputvideos successfully!")
    
    # cleanup
    # shutil.rmtree(tmp)	

    return {
        'statusCode': 200,
        'body': result
    }
