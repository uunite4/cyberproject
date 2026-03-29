import os

SERVERS_ADDRESSES = []

for i in range(4):
    val = os.getenv(f"GAME_SERVER_{i + 1}", f"127.0.0.1:900{i}")
    if val:
        ip, port = val.split(":")
        SERVERS_ADDRESSES.append({"ip": ip, "port": int(port)})

CMDS = {
    "INIT_POS": 0x01,
    "MOVE": 0x02,
    "OVERLAP": 0x03,
    "SWITCH_SERVER": 0x04,
    "POS_DONT_RESPOND": 0x05,
    "INIT_LB": 0x06,
    "LB_ADDING_PLAYER": 0x07,
    "RENDER": 0x08,
    "DAMAGE": 0x09,
    "RESPAWN": 0x0A,
    "ATTACK": 0x0B,
    "OUT_OF_OVERLAP": 0x0C,
    "REMOVE_ME": 0x0D,
    "HP_DONT_RESPOND": 0x0E,
    "CHANGE_WEAPON": 0x0F,
    "ADD_ME": 0x10,
    "FART": 0x11,
    "HELLO": 0x12,
    "LOGIN_TO_LB": 0x13,
    "CLIENT_DATA": 0x14,
    "DELETE_ITEM": 0x15,
    "FART_READY": 0x16,
    "PICKUP_ITEM": 0x17,
    "ADD_ITEM": 0x18,
    "TRANSFER_P": 0x19,
    "HELLO_FROM_LB": 0x1A,
    "INVIS": 0x1B,
    "LASER": 0x1C,
    "BRIT": 0x1D,
    "FARTING": 0x1E,
    "ERROR": 0x1F,
    "PLAYER_LEFT": 0x20,
    "TELEPORT_READY": 0x21,
    "TELEPORT": 0x22,
}

BASIC_INV = ['da', 'gu', 0, 0, 0, 0, 0, 0]
INVENTORY_SIZE = len(BASIC_INV)
