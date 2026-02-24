import shutil
from pathlib import Path

from grpc_tools import protoc

BASE_DIR = Path(__file__).parent.resolve()

COMPILE_DIR = BASE_DIR / "compiled_protobufs"
SOURCE_DIR = BASE_DIR / "source_protobufs"


def compile_protobuf(protobuf_name: str):
    protoc.main([
        "protoc",
        f"-I{SOURCE_DIR}",
        f"--python_out={COMPILE_DIR}",
        f"--pyi_out={COMPILE_DIR}",
        str(SOURCE_DIR / protobuf_name),
    ])


def recompile_all():
    clear_all()

    for file in SOURCE_DIR.iterdir():
        if file.is_file():
            compile_protobuf(file.name)

    print("recompiled protobufs")


def clear_all():
    if COMPILE_DIR.exists():
        shutil.rmtree(COMPILE_DIR)
    COMPILE_DIR.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    recompile_all()
