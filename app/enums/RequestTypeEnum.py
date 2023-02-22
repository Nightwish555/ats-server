from enum import IntEnum


class RequestType(IntEnum):
    http = 1
    grpc = 2
    dubbo = 3
    websocket = 4
    tcp = 5
    udp = 5
