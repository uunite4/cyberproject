import os
import shutil
from pathlib import Path

from grpc_tools import protoc

COMPILE_DIR = 'compiled_protobufs'
SOURCE_DIR = 'source_protobufs'


def compile_protobuf(protobuf_name: str):
    protoc.main([
        "protoc",
        f"-I{SOURCE_DIR}",
        f"--python_out={COMPILE_DIR}",
        f"--pyi_out={COMPILE_DIR}",
        protobuf_name,
    ])


def recompile_all():
    clear_all()
    src_dir = Path(SOURCE_DIR)

    for file in src_dir.iterdir():
        if file.is_file():
            compile_protobuf(file.name)

    print('recompiled protobufs')


def clear_all():
    try:
        shutil.rmtree(COMPILE_DIR)
        os.mkdir(COMPILE_DIR)
    except:
        None


if __name__ == "__main__":
    recompile_all()
