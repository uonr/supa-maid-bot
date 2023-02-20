def is2XX(status_code: int) -> bool:
    return status_code >= 200 and status_code < 300
