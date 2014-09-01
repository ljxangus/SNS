import shelve
import msvcrt 

if __name__ =='__main__':
    s = shelve.open('status_hash.bat')
    for key in s:
        print ('The key hash is ', key)
        
    print('The length of the database is ', len(s))
    key = msvcrt.getch()