import os
from flask import *
import boto3
import requests
from dotenv import load_dotenv
from werkzeug.utils import redirect

app = Flask(__name__)

load_dotenv()

# AWS Setup
AWS_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY')
AWS_SECRET_KEY = os.environ.get('AWS_SECRET_KEY')
REGION_NAME = "ap-south-1"
BUCKET_NAME = os.environ.get("BUCKET_NAME")

# Create S3 client
s3 = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=REGION_NAME
)

# API Gateway endpoint
API_URL = os.environ.get('API')

@app.route('/', methods=['GET'])
def homee():
    # Check if there's a blog content to show
    blog_content = request.args.get('blog_content', '')
    error_message = request.args.get('error_message', '')
    return render_template('base.html', blog_content=blog_content, error_message=error_message)


@app.route('/', methods=['POST'])
def home():
    blog_content = ""
    error_message = ""

    blog_topic = request.form.get('blog_topic', '').strip()

    if not blog_topic:
        error_message = "Please enter a valid blog topic."
        return redirect(url_for('homee', error_message=error_message))

    try:
        # Send POST request to API Gateway to generate blog
        response = requests.post(API_URL, json={"blog_topic": blog_topic})
        response.raise_for_status()

        # List all files in blog-output/ prefix in S3
        response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix='blog-output/')

        if 'Contents' in response:
            # Sort by last modified to get the latest blog
            sorted_files = sorted(response['Contents'], key=lambda x: x['LastModified'], reverse=True)
            latest_file = sorted_files[0]['Key']

            # Download the latest blog
            s3.download_file(BUCKET_NAME, latest_file, "latest_blog.txt")
            with open("latest_blog.txt", "r") as f:
                blog_content = f.read()
        else:
            error_message = "No blog files found in S3."

    except Exception as e:
        error_message = f"An error occurred: {str(e)}"

    # Redirect to GET route with the blog content or error message
    return redirect(url_for('homee', blog_content=blog_content, error_message=error_message))


if __name__ == '__main__':
    app.run(debug=True)
