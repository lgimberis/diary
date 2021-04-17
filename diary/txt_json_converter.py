import re

class NonComformingTextException(Exception):
    '''Raised when a .txt file does not match the expected format'''
    pass

def txt_to_json(f):
    '''Return the content of file 'f' as JSON
    
    This function assumes text files have the following format:
    1) Keys are on their own line
    2) Keys are enclosed in square brackets []
    3) Anything after a key until another key is the value of the preceding key

    Any non-conforming .txt file will raise a NonComformingTextException
    '''
    myJson = {}
    key = None
    category = "none"
    value = ''
    for line in f:
        if line.strip():
            match = re.match(r'\[([^\]]*)\]', line.strip())
            if match:
                if key:
                    myJson[key][category] = value
                key = match.group(1)

                if key in myJson:
                    raise NonComformingTextException(f'Key {key} declared multiple times')
                category = "none"
                myJson[key] = {}
                value = ''
            else:
                matchCategory = re.match(r'\(([^\)]*)\)', line.strip())
                if matchCategory:
                    category = matchCategory.group(1)
                    if category == "none":
                        raise NonComformingTextException(f'"none" is a reserved category name')
                    elif category in myJson[key]:
                        raise NonComformingTextException(f'Category {category} declared multiple times')
                else:
                    if key:
                        value += line.strip()
                    else:
                        raise NonComformingTextException('Key not declared before text')
    if key:
        myJson[key][category] = value
    return myJson
