import pickle
import msvcrt
import snsapi.utils

if __name__ =='__main__':
    f = open('status_database.pickle','rb')
    objs = []
    while 1:
        try:
            objs.append(pickle.load(f))
        except EOFError:
            break
    f.close()
        
    print('The length of the database is ', len(objs))
    key = msvcrt.getch()