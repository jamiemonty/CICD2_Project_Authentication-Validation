def reader(filename: str):
    dataList = []
    with open(filename) as my_file:
        for line in my_file:
            data = {}
            courses = []
            i = 3
            line = line.replace('\n', '')
            line = line.split(';')

            data['name'] = line[0]
            data['studentId'] = line[1]
            data['courseNum'] = line[2]
            courseNum = int(line[2])
            while i < 3 + courseNum:
                courses.append(line[i])
                i += 1
    
            data['courses'] = courses
            dataList.append(data)

    return dataList



if __name__ == "__main__":
    print(reader('docu_serve/fileConvertor/fileExample.csv'))
