#Function to read the CSV file
def reader(filename: str): # grabs the file name retrieved in main
    dataList = []
    with open(filename) as my_file: #opens the file using python function 
        for line in my_file: # for loop used to read each line from file
            data = {}
            courses = []
            i = 3
            line = line.replace('\n', '') # takes any \n out of the line
            line = line.split(';') # uses each ; to replace and split the line into parts

            data['name'] = line[0] # first part, second, third
            data['studentId'] = line[1]
            data['courseNum'] = line[2]
            courseNum = int(line[2])
            while i < 3 + courseNum: # grabs the final parts, which are course to put them into a list
                courses.append(line[i])
                i += 1
    
            data['courses'] = courses # attributes list to a dict key
            dataList.append(data)  # appends the dict to a list

    return dataList #returns list



if __name__ == "__main__":
    #grabs file from the directory, can be changed to view a submitted file.
    print(reader('docu_serve/fileConvertor/fileExample.csv'))
