import os
from typing import Optional
from decimal import Decimal
import boto3
from botocore.exceptions import ClientError
from repositories.protocols import UserEntity, ProgressEntity


def get_dynamodb_resource():
    """Get DynamoDB resource, supporting local testing."""
    endpoint_url = os.getenv("DYNAMODB_ENDPOINT_URL")
    region = os.getenv("AWS_REGION", "us-east-1")

    if endpoint_url:
        return boto3.resource("dynamodb", endpoint_url=endpoint_url, region_name=region)
    return boto3.resource("dynamodb", region_name=region)


class DynamoUserRepository:
    """DynamoDB-based user repository."""

    def __init__(self):
        dynamodb = get_dynamodb_resource()
        table_name = os.getenv("DYNAMODB_USERS_TABLE", "reader-progress-users")
        self.table = dynamodb.Table(table_name)

    def get_by_username(self, username: str) -> Optional[UserEntity]:
        try:
            response = self.table.get_item(Key={"username": username})
            item = response.get("Item")
            if not item:
                return None
            return UserEntity(
                id=item["username"],  # username is the ID in DynamoDB
                username=item["username"],
                password_hash=item["password_hash"]
            )
        except ClientError:
            return None

    def create(self, username: str, password_hash: str) -> UserEntity:
        try:
            self.table.put_item(
                Item={
                    "username": username,
                    "password_hash": password_hash
                },
                ConditionExpression="attribute_not_exists(username)"
            )
            return UserEntity(id=username, username=username, password_hash=password_hash)
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                raise ValueError(f"Username '{username}' already exists")
            raise

    def exists(self, username: str) -> bool:
        response = self.table.get_item(
            Key={"username": username},
            ProjectionExpression="username"
        )
        return "Item" in response


class DynamoProgressRepository:
    """DynamoDB-based progress repository."""

    def __init__(self):
        dynamodb = get_dynamodb_resource()
        table_name = os.getenv("DYNAMODB_PROGRESS_TABLE", "reader-progress-progress")
        self.table = dynamodb.Table(table_name)

    def get_by_user_and_document(
        self, user_id: str, document: str
    ) -> Optional[ProgressEntity]:
        try:
            response = self.table.get_item(
                Key={
                    "user_id": user_id,
                    "document": document
                }
            )
            item = response.get("Item")
            if not item:
                return None
            return ProgressEntity(
                user_id=item["user_id"],
                document=item["document"],
                progress=item["progress"],
                percentage=float(item["percentage"]),
                device=item["device"],
                device_id=item["device_id"],
                timestamp=int(item["timestamp"])
            )
        except ClientError:
            return None

    def upsert(self, progress: ProgressEntity) -> ProgressEntity:
        self.table.put_item(
            Item={
                "user_id": progress.user_id,
                "document": progress.document,
                "progress": progress.progress,
                "percentage": Decimal(str(progress.percentage)),
                "device": progress.device,
                "device_id": progress.device_id,
                "timestamp": progress.timestamp
            }
        )
        return progress
