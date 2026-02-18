import os
import pygame
import socket
import struct
import sys

from Player import PlayerData, handle_input, health_bar_update, S_health_bar_update
from settings import *
from map_data import MAP
from map import draw_map

def qc3_pack(cmd: int, payload: bytes = b"") -> bytes:
    body = bytes([cmd]) + payload
    return struct.pack("!I", len(body)) + body

class QC3Stream:
    def __init__(self):
        self.buf = bytearray()

    def feed(self, data: bytes):
        self.buf.extend(data)

    def pop_messages(self):
        msgs = []
        while True:
            if len(self.buf) < 4:
                break
            (length,) = struct.unpack("!I", self.buf[:4])
            if len(self.buf) < 4 + length:
                break
            body = bytes(self.buf[4:4 + length])
            del self.buf[:4 + length]
            cmd = body[0]
            payload = body[1:]
            msgs.append((cmd, payload))
        return msgs


def dir_to_vec(d: int) -> tuple[int, int]:
    if d == 1: return (1, 0)
    if d == 2: return (1, 1)
    if d == 3: return (0, 1)
    if d == 4: return (-1, 1)
    if d == 5: return (-1, 0)
    if d == 6: return (-1, -1)
    if d == 7: return (0, -1)
    if d == 8: return (1, -1)
    return (0, 1)