import re

class NonComformingTextException(Exception):
    '''Raised when a .txt file does not match the expected format'''
    pass

def txt_to_json(f, key_close=']', value_close='['):
    '''Return the content of file 'f' as JSON
    
    This function assumes text files have the following format:
    1) Keys are on their own line
    2) Keys are enclosed in square brackets []
    3) Anything after a key until another key is the value of the preceding key

    Any non-conforming .txt file will raise a NonComformingTextException
    '''
    myJson = {}
    key = None
    for line in f:
        if '[' or ']' in line:
            if key:
                myJson[key] = value
            key = re.sub(r'[\[\]]',r'',line.strip())
            if key in myJson:
                raise NonComformingTextException(f'Key {key} declared multiple times')
            value = ''
        else:
            if not key:
                raise NonComformingTextException('Key not declared before text')
            else:
                value.append(line.strip())

def main():
    import unittest
    unittest.main()

if __name__=="__main__":
    main()        