import yaml

def load_config(config_file_path):
    with open(config_file_path, "r") as file:
        config = yaml.safe_load(file)
    return config