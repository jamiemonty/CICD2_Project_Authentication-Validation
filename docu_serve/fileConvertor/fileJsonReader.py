import json

def print_file(filename: str):
    with open(filename) as my_file:
        data = my_file.read()

    fileMemory = json.loads(data)

    for memory in fileMemory:
        print(memory)


if __name__ == "__main__":
    print(print_file('docu_serve/fileConvertor/fileExample.Json'))