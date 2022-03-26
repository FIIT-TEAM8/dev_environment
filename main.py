from xxlimited import new
import yaml
import subprocess
import os
import shutil


def create_directory_structure(compose_file):
    # create folders specified in compose
    if os.path.exists("data"):
        shutil.rmtree("data")
    for service in compose_file["services"]:
        if "volumes" in compose_file["services"][service]:
            for volume in compose_file["services"][service]["volumes"]:
                path_to_create = volume.split(":")[0]
                os.makedirs(path_to_create, exist_ok=True)

    chmod_cmd = ["chmod", "-R", "777" ,"data"]
    subprocess.Popen(chmod_cmd).wait()


def prepare_env_variables():
    cmd_env = ["./decrypt_env.sh", ENV_PASSWORD]
    child = subprocess.Popen(cmd_env)
    child.wait()
    if (child.returncode != 0):
        print("Error while extracting environmental variables. Probably bad password. Exit code: ", child.returncode)
        exit(0)





ENV_PASSWORD = input("Enter password for decrypting environmental variables: ")

print("Decrypting and unpacking env variables...")
prepare_env_variables()

with open("docker-compose.yml") as f:
    compose = yaml.safe_load(f)

print("Creating directory structure...")
create_directory_structure(compose)

print("DONE.")
