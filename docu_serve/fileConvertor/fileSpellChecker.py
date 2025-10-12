import difflib

text = input('Write text: ')
textcheck = []
sugg = []
dict = []
fin = ' '

with open('wordlist.txt')as dict_file:
    for line in dict_file:
        line = line.replace('\n', '')
        dict.append(line)

text = text.split(' ')

for word in text:
    if word.lower() not in dict and word.upper not in dict:
        textcheck.append('*' + word + '*')
        sugg.append(word)

    else:
        textcheck.append(word)
        













