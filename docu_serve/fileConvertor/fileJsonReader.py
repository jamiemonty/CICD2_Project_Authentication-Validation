import json

def print_file(filename: str): # grabs file from main again
    with open(filename) as my_file: # opens file
        data = my_file.read() # reads file

    fileMemory = json.loads(data) # uses json import to load the data

    for memory in fileMemory: #uses for loop to print each user
        print(memory)


if __name__ == "__main__":
    print(print_file('docu_serve/fileConvertor/fileExample.Json'))