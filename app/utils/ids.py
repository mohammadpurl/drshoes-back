import uuid


def new_id() -> str:
    return str(uuid.uuid4())


def new_product_id() -> str:
    return uuid.uuid4().hex[:12]
