import yaml
import subprocess
import os
import shutil

CONFIG_FILE = "dev_env_config.yaml"

with open(CONFIG_FILE) as f:
    global_config = yaml.safe_load(f)


def prepare_service_config():
    shutil.rmtree("service_config", ignore_errors=True)
    cmd_git_clone = ["git", "clone", global_config["service_details"]["service_config"]["repository"]]
    subprocess.Popen(cmd_git_clone).wait()
    # for safety reasons all git stuff is deleted
    shutil.rmtree("service_config/.git", ignore_errors=True)
    shutil.rmtree("service_config/.github", ignore_errors=True)
    os.remove("service_config/.gitignore")



def remove_redundant_services():
    redundant_services = global_config["redundant_services"]

    with open("service_config/docker-compose.yml") as f:
        compose_file = yaml.safe_load(f)

    # delete redundant services
    for service in redundant_services:
        compose_file["services"].pop(service, None)
    
    return compose_file



def create_directory_structure(compose_file):
    # create folders specified in compose
    cwd = os.getcwd()
    os.chdir("service_config")
    for service in compose_file["services"]:
        if "volumes" in compose_file["services"][service]:
            for volume in compose_file["services"][service]["volumes"]:
                path_to_create = volume.split(":")[0]
                os.makedirs(path_to_create, exist_ok=True)

    os.chdir(cwd)


def prepare_env_variables():
    cwd = os.getcwd()
    os.chdir("service_config")
    cmd_env = ["./decrypt_env.sh", ENV_PASSWORD]
    child = subprocess.Popen(cmd_env)
    child.wait()
    if (child.returncode != 0):
        print("Error while extracting environmental variables. Probably bad password. Exit code: ", child.returncode)
        exit(0)
    os.chdir(cwd)


def dump_compose(compose_file):
    with open("service_config/docker-compose.yml", "w") as f:
        yaml.dump(compose_file, f)



def additional_config(compose_file):
    for service in global_config["service_details"]:
        if "additional_config" in global_config["service_details"][service]:
            for key in global_config["service_details"][service]["additional_config"]:
                if key in compose_file["services"][service] and isinstance(compose_file["services"][service][key], list):
                    compose_file["services"][service][key].extend(global_config["service_details"][service]["additional_config"][key])
                else:
                    compose_file["services"][service][key] = global_config["service_details"][service]["additional_config"][key]
    return compose_file


ENV_PASSWORD = input("Enter password for decrypting environmental variables: ")
print("Cloning Github repository..")
prepare_service_config()
print("Adjusting docker-compose.yml...")
compose = remove_redundant_services()
print("Creating directory structure...")
create_directory_structure(compose)
print("Decrypting and unpacking env variables...")
prepare_env_variables()
print("Adjusting with user config...")
compose = additional_config(compose)

print("DONE.")
dump_compose(compose)

# temporary fix, dot notation not working in .env files on wsl2
open("service_config/env/elastic.env", "w")