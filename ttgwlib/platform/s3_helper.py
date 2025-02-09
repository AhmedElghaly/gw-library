import os

import boto3
import botocore.exceptions

from ttgwlib.platform.exception import GatewayError


FIRMWARE_DIR = os.path.expanduser("~/.tychetools/.firm_update")
S3_BUCKET = "tychetools-fw-binaries"


def download_firmware(version, board):
    fw_dir = os.path.join(FIRMWARE_DIR, version)
    sd_file = os.path.join(fw_dir, "sd.hex")
    fw_file = os.path.join(fw_dir, "fw.hex")
    if os.path.isfile(sd_file) and os.path.isfile(fw_file):
        return sd_file, fw_file

    import tempfile
    import tarfile
    os.makedirs(fw_dir, exist_ok=True)
    s3_fw_name = f"gw-firmware_{board}_{version}.tar.gz"
    with tempfile.TemporaryDirectory() as tmp_dir:
        fw_download_path = os.path.join(tmp_dir, s3_fw_name)
        s3 = boto3.client("s3")
        try:
            s3.download_file(S3_BUCKET, s3_fw_name, fw_download_path)
        except botocore.exceptions.NoCredentialsError as e:
            raise GatewayError("AWS credentials not found") from e
        with tarfile.open(fw_download_path) as f:
            f.extractall(tmp_dir)
        for file in os.listdir(tmp_dir):
            if file[-4:] == ".hex":
                if "softdevice" in file or file == "sd.hex":
                    os.system(f"cp {tmp_dir}/{file} {sd_file}")
                else:
                    os.system(f"cp {tmp_dir}/{file} {fw_file}")
    return sd_file, fw_file
