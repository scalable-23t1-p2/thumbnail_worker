import subprocess
import s3utils
import utils
import boto3
import os
from dotenv import load_dotenv
from celery import Celery

raw_video = "raw_video"
thumbnail_output = "thumbnail_output"
client = boto3.client(
's3',
aws_access_key_id=os.getenv("S3_ACCESS_KEY"),
aws_secret_access_key=os.getenv("S3_SECRET_KEY")
)
BROKER_URL = os.getenv("CELERY_BROKER_URL")
RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND")
celery_app = Celery('thumbnail', broker=BROKER_URL,
                    backend=RESULT_BACKEND)

@celery_app.task(name="thumbnail")
def thumbnail(filename, s3_file_path):
    print("Thumbnailing video")
    print("filename+s3filepath="+filename+','+s3_file_path)
    # try:
    utils.create_dir(raw_video)
    utils.create_dir(thumbnail_output)
    file = filename
    filename_noext, extension = utils.extract_ext(file)
    user_folder = s3_file_path.split('/',1)[0]
    output_file = filename_noext + ".jpg"
    BUCKET_NAME = 'toktikbucket'
    S3_PATH = s3_file_path
    LOCAL_PATH=f"{raw_video}/{file}"
    S3_UPLOAD_PATH = f'{user_folder}/{output_file}'
    s3utils.download_s3_file(client= client, local_path=LOCAL_PATH, s3_path=S3_PATH)
    print("downloaded raw from s3")
    subprocess.run(
        [
            "ffmpeg",
            "-i",
            f"{raw_video}/{file}",
            "-ss",
            "00:00:01.000",
            "-vframes",
            "1",
            f"{thumbnail_output}/{output_file}",
        ]
    )
    print("done thumbnailing")
    s3utils.upload_s3_file(client, f"{thumbnail_output}/{output_file}", S3_UPLOAD_PATH)
    print("done upload to s3")    
    utils.clean_dir(filename)
    # except Exception as e:
    #     print(e.with_traceback)
    celery_app.send_task("chunk", queue='q02',args=[filename, S3_UPLOAD_PATH])
if __name__ == "__main__":
    thumbnail()