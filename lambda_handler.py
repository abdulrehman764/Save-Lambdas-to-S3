from botocore.exceptions import NoCredentialsError
import boto3
import json
import base64
import urllib.request
from urllib.parse import urlparse
# Initialize the Lambda client
lambda_client = boto3.client('lambda')

# Initialize the S3 client
s3_client = boto3.client('s3')

# Specify your S3 bucket name
bucket_name = 'abdul-lambda-workflow'
# Specify the S3 key (file name) where the data will be stored
s3_key = 'lambda_functions.json'

def list_lambda_functions():
    # List to hold all Lambda functions
    lambda_functions = []

    # Initialize pagination
    paginator = lambda_client.get_paginator('list_functions')
    for page in paginator.paginate():
        for function in page['Functions']:
            # Get the function's code
            code_s3_key = store_function_code(function['FunctionName'])
            function['CodeS3Key'] = code_s3_key
            lambda_functions.append(function)

    return lambda_functions

def store_function_code(function_name):
    try:
        response = lambda_client.get_function(FunctionName=function_name)
        code_url = response['Code']['Location']

        # Using urllib to download the code directly
        with urllib.request.urlopen(code_url) as code_response:
            code_content = code_response.read()
            # Generate S3 key for the zip file
            parsed_url = urlparse(code_url)
            code_filename = f"{function_name}.zip"
            s3_key = f"lambda_function_code/{code_filename}"

            # Upload the zip file to S3
            s3_client.put_object(Body=code_content, Bucket=bucket_name, Key=s3_key)

        return s3_key
    except NoCredentialsError:
        print("Credentials not available")
        return None
    except Exception as e:
        print(f"Error fetching code for function {function_name}: {e}")
        return None

def upload_metadata_to_s3(data, bucket, key):
    # Convert the data to JSON format
    json_data = json.dumps(data, indent=2)

    # Upload the JSON data to S3
    s3_client.put_object(Body=json_data, Bucket=bucket, Key=key)

def lambda_handler(event, context):
    # List all Lambda functions
    functions = list_lambda_functions()

    # Upload the list to S3
    upload_metadata_to_s3(functions, bucket_name, s3_key)

    print(f"Uploaded list of Lambda functions to s3://{bucket_name}/{s3_key}")

