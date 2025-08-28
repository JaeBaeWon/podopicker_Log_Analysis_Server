import os
from dotenv import load_dotenv
import boto3

load_dotenv(dotenv_path="/home/ubuntu/mcp-log-analyzer/.env")

BUCKET_NAME = "podopicker-cf-logs-bucket"
PREFIX = "AWSLogs/639965457439/CloudFront/logs/"
LOCAL_DIR = "logs"
DOWNLOADED_TRACKER = "downloaded_files.txt"

session = boto3.Session(
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION", "ap-northeast-2")
)
s3 = boto3.client("s3")

def load_downloaded_files():
    if not os.path.exists(DOWNLOADED_TRACKER):
        return set()
    with open(DOWNLOADED_TRACKER, "r") as f:
        return set(line.strip() for line in f.readlines())

def save_downloaded_file(filename):
    with open(DOWNLOADED_TRACKER, "a") as f:
        f.write(filename + "\n")

def download_new_logs():
    if not os.path.exists(LOCAL_DIR):
        os.makedirs(LOCAL_DIR)

    already_downloaded = load_downloaded_files()
    token = None  # for pagination

    while True:
        if token:
            response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=PREFIX, ContinuationToken=token)
        else:
            response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=PREFIX)

        if "Contents" not in response:
            print("⚠️ S3 버킷에 로그가 없습니다.")
            return

        for obj in response["Contents"]:
            key = obj["Key"]
            if not key.endswith(".gz"):
                            continue

            filename = key.split("/")[-1]
            if filename in already_downloaded:
                continue

            local_path = os.path.join(LOCAL_DIR, filename)
            print(f"⬇️ 다운로드 중: {filename}")
            s3.download_file(BUCKET_NAME, key, local_path)
            save_downloaded_file(filename)

        if response.get("IsTruncated"):
            token = response.get("NextContinuationToken")
        else:
            break

if __name__ == "__main__":
    download_new_logs()

    from main import main
    main()

