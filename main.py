from xxlimited import new
import yaml
import subprocess
import os
import shutil

CONFIG_FILE = "config.yaml"
ES_INDEXER_FILE = "es_indexer.yaml"

with open(CONFIG_FILE) as f:
    global_config = yaml.safe_load(f)

with open(ES_INDEXER_FILE) as f:
    es_indexer_yaml = yaml.safe_load(f)


def prepare_service_config():
    shutil.rmtree("service_config", ignore_errors=True)
    cmd_git_clone = ["git", "clone", global_config["service_details"]["service_config"]["repository"]]
    subprocess.Popen(cmd_git_clone).wait()
    # for safety reasons all git stuff is deleted
    shutil.rmtree("service_config/.git", ignore_errors=True)
    shutil.rmtree("service_config/.github", ignore_errors=True)
    os.remove("service_config/.gitignore")



def remove_redundant_services(compose_file):
    redundant_services = global_config["redundant_services"]

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

    chmod_cmd = ["chmod", "-R", "777" ,"data_link"]
    subprocess.Popen(chmod_cmd).wait()
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



def user_config(compose_file):
    for service in global_config["service_details"]:
        if "compose_adjustment" in global_config["service_details"][service]:
            for key in global_config["service_details"][service]["compose_adjustment"]:
                if key in compose_file["services"][service] and isinstance(compose_file["services"][service][key], list):
                    compose_file["services"][service][key].extend(global_config["service_details"][service]["compose_adjustment"][key])
                else:
                    compose_file["services"][service][key] = global_config["service_details"][service]["compose_adjustment"][key]
    return compose_file


def add_es_indexer(compose_file):
    ''' add es_indexer to dev environment compose file in services section '''

    compose_file['services']['es_indexer'] = es_indexer_yaml['es_indexer']

    return compose_file


def prepareNGINX():
    cmd_git = ["git", "clone", global_config["service_details"]["nginx"]["repository"], global_config["service_details"]["nginx"]["clone_destination"]]
    subprocess.Popen(cmd_git).wait()
    config = global_config["service_details"]["nginx"]["clone_destination"] + "app.conf"
    new_config_text = open("nginx.app.conf").read()
    with open(config, "w") as overwrite:
        overwrite.write(new_config_text)


ENV_PASSWORD = input("Enter password for decrypting environmental variables: ")
print("Cloning Github repository..")
prepare_service_config()

with open("service_config/docker-compose.yml") as f:
    compose = yaml.safe_load(f)

print("Adjusting docker-compose.yml...")
compose = user_config(compose)
compose = add_es_indexer(compose)
compose = remove_redundant_services(compose)
print("Creating directory structure...")
create_directory_structure(compose)
print("Decrypting and unpacking env variables...")
prepare_env_variables()
print("Setup NGINX...")
prepareNGINX()
print("Adjusting with user config...")

print("DONE.")
dump_compose(compose)

# temporary fix, dot notation not working in .env files on wsl2
open("service_config/env/elastic.env", "w")