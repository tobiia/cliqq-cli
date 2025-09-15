import json
import os


# need func to extract info from the json
def run(actionable):
    data = json.loads(actionable)
    if data["action"] is "command":
        run_command(data["command"])
    if data["action"] is "file":
        save_file(data)


# need func to run command
def run_command(command):
    return


# need func to create file
def save_file(file):
    # file is in json, labels "path" and "content"
    path = file["path"]
    content = file["content"]
    name = os.path.basename(path)
    try:
        open(path, "x")
        with open(path, "w") as f:
            f.write(content)
    except:
        # ask for a different name and attempt again
        return False
    return True
