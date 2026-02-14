import os
from typing import Optional
from decimal import Decimal
import boto3
from botocore.exceptions import ClientError
from repositories.protocols import UserEntity, ProgressEntity, DocumentLinkEntity, BookLabelEntity


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
                timestamp=int(item["timestamp"]),
                filename=item.get("filename")
            )
        except ClientError:
            return None

    def get_by_user_and_filename(
        self, user_id: str, filename: str
    ) -> Optional[ProgressEntity]:
        try:
            # Query using GSI on filename (requires GSI setup)
            # For now, scan with filter (less efficient but works without GSI)
            response = self.table.scan(
                FilterExpression="user_id = :uid AND filename = :fname",
                ExpressionAttributeValues={
                    ":uid": user_id,
                    ":fname": filename
                }
            )
            items = response.get("Items", [])
            if not items:
                return None
            # Return the most recent one
            item = max(items, key=lambda x: int(x.get("timestamp", 0)))
            return ProgressEntity(
                user_id=item["user_id"],
                document=item["document"],
                progress=item["progress"],
                percentage=float(item["percentage"]),
                device=item["device"],
                device_id=item["device_id"],
                timestamp=int(item["timestamp"]),
                filename=item.get("filename")
            )
        except ClientError:
            return None

    def get_all_by_user_and_filename(
        self, user_id: str, filename: str
    ) -> list[ProgressEntity]:
        try:
            response = self.table.scan(
                FilterExpression="user_id = :uid AND filename = :fname",
                ExpressionAttributeValues={
                    ":uid": user_id,
                    ":fname": filename
                }
            )
            return [
                ProgressEntity(
                    user_id=item["user_id"],
                    document=item["document"],
                    progress=item["progress"],
                    percentage=float(item["percentage"]),
                    device=item["device"],
                    device_id=item["device_id"],
                    timestamp=int(item["timestamp"]),
                    filename=item.get("filename")
                )
                for item in response.get("Items", [])
            ]
        except ClientError:
            return []

    def upsert(self, progress: ProgressEntity) -> ProgressEntity:
        item = {
            "user_id": progress.user_id,
            "document": progress.document,
            "progress": progress.progress,
            "percentage": Decimal(str(progress.percentage)),
            "device": progress.device,
            "device_id": progress.device_id,
            "timestamp": progress.timestamp
        }
        if progress.filename:
            item["filename"] = progress.filename
        self.table.put_item(Item=item)
        return progress

    def get_all_by_user(self, user_id: str) -> list[ProgressEntity]:
        try:
            response = self.table.query(
                KeyConditionExpression="user_id = :uid",
                ExpressionAttributeValues={":uid": user_id}
            )
            return [
                ProgressEntity(
                    user_id=item["user_id"],
                    document=item["document"],
                    progress=item["progress"],
                    percentage=float(item["percentage"]),
                    device=item["device"],
                    device_id=item["device_id"],
                    timestamp=int(item["timestamp"]),
                    filename=item.get("filename")
                )
                for item in response.get("Items", [])
            ]
        except ClientError:
            return []


class DynamoDocumentLinkRepository:
    """DynamoDB-based document link repository."""

    def __init__(self):
        dynamodb = get_dynamodb_resource()
        table_name = os.getenv("DYNAMODB_DOCUMENT_LINKS_TABLE", "reader-progress-document-links")
        self.table = dynamodb.Table(table_name)

    def get_canonical(self, user_id: str, document_hash: str) -> Optional[str]:
        try:
            response = self.table.get_item(
                Key={
                    "user_id": user_id,
                    "document_hash": document_hash
                }
            )
            item = response.get("Item")
            return item["canonical_hash"] if item else None
        except ClientError:
            return None

    def create_link(self, user_id: str, document_hash: str, canonical_hash: str) -> DocumentLinkEntity:
        self.table.put_item(
            Item={
                "user_id": user_id,
                "document_hash": document_hash,
                "canonical_hash": canonical_hash
            }
        )
        return DocumentLinkEntity(
            user_id=user_id,
            document_hash=document_hash,
            canonical_hash=canonical_hash
        )

    def get_all_links(self, user_id: str) -> list[DocumentLinkEntity]:
        try:
            response = self.table.query(
                KeyConditionExpression="user_id = :uid",
                ExpressionAttributeValues={":uid": user_id}
            )
            return [
                DocumentLinkEntity(
                    user_id=item["user_id"],
                    document_hash=item["document_hash"],
                    canonical_hash=item["canonical_hash"]
                )
                for item in response.get("Items", [])
            ]
        except ClientError:
            return []

    def delete_link(self, user_id: str, document_hash: str) -> bool:
        try:
            self.table.delete_item(
                Key={
                    "user_id": user_id,
                    "document_hash": document_hash
                }
            )
            return True
        except ClientError:
            return False

    def get_linked_hashes(self, user_id: str, canonical_hash: str) -> list[str]:
        try:
            # Scan with filter (would be better with GSI on canonical_hash)
            response = self.table.scan(
                FilterExpression="user_id = :uid AND canonical_hash = :chash",
                ExpressionAttributeValues={
                    ":uid": user_id,
                    ":chash": canonical_hash
                }
            )
            return [item["document_hash"] for item in response.get("Items", [])]
        except ClientError:
            return []


class DynamoBookLabelRepository:
    """DynamoDB-based book label repository."""

    def __init__(self):
        dynamodb = get_dynamodb_resource()
        table_name = os.getenv("DYNAMODB_BOOK_LABELS_TABLE", "reader-progress-book-labels")
        self.table = dynamodb.Table(table_name)

    def get_label(self, user_id: str, canonical_hash: str) -> Optional[str]:
        try:
            response = self.table.get_item(
                Key={
                    "user_id": user_id,
                    "canonical_hash": canonical_hash
                }
            )
            item = response.get("Item")
            return item["label"] if item else None
        except ClientError:
            return None

    def set_label(self, user_id: str, canonical_hash: str, label: str) -> BookLabelEntity:
        self.table.put_item(
            Item={
                "user_id": user_id,
                "canonical_hash": canonical_hash,
                "label": label
            }
        )
        return BookLabelEntity(
            user_id=user_id,
            canonical_hash=canonical_hash,
            label=label
        )

    def delete_label(self, user_id: str, canonical_hash: str) -> bool:
        try:
            self.table.delete_item(
                Key={
                    "user_id": user_id,
                    "canonical_hash": canonical_hash
                }
            )
            return True
        except ClientError:
            return False

    def get_all_labels(self, user_id: str) -> list[BookLabelEntity]:
        try:
            response = self.table.query(
                KeyConditionExpression="user_id = :uid",
                ExpressionAttributeValues={":uid": user_id}
            )
            return [
                BookLabelEntity(
                    user_id=item["user_id"],
                    canonical_hash=item["canonical_hash"],
                    label=item["label"]
                )
                for item in response.get("Items", [])
            ]
        except ClientError:
            return []
