def reader(filename: str):
    with open(filename) as my_file:
        for line in my_file:
            line = line.replace('\n', '')
            line = line.split(';')

            






if __name__ == "__main__":
    print(reader('docu_serve/fileConvertor/fileExample.csv'))
