import re

class NonComformingTextException(Exception):
    '''Raised when a .txt file does not match the expected format'''
    pass

def txt_to_dict(f):
    '''Return the content of file 'f' as dict
    
    This function assumes text files have the following format:
    1) Keys are on their own line
    2) Keys are enclosed in square brackets []
    3) Anything after a key until another key is the value of the preceding key

    Any non-conforming .txt file will raise a NonComformingTextException
    '''
    mydict = {}
    key = None
    category = "none"
    value = ''
    for line in f:
        if line.strip():
            match = re.match(r'\[([^\]]*)\]', line.strip())
            if match:
                if key and value:
                    try:
                        mydict[key][category] = value
                    except KeyError:
                        mydict[key] = {category:value}
                key = match.group(1)

                if key in mydict:
                    raise NonComformingTextException(f'Key {key} declared multiple times')
                category = "none"
                value = ''
            else:
                matchCategory = re.match(r'\(([^\)]*)\)', line.strip())
                if matchCategory:
                    if value:
                        try:
                            mydict[key][category] = value
                        except KeyError:
                            mydict[key] = {category:value}
                        value = ''
                    category = matchCategory.group(1)
                    if category == "none":
                        raise NonComformingTextException(f'"none" is a reserved category name')
                    elif key in mydict and category in mydict[key]:
                        raise NonComformingTextException(f'Category {category} declared multiple times')
                else:
                    if key:
                        if value:
                            value += '\n'
                        value += line.strip()
                    else:
                        raise NonComformingTextException('Key not declared before text')
    if key and value:
        try:
            mydict[key][category] = value
        except KeyError:
            mydict[key] = {category: value}
    return mydict

def dict_to_txt(dictionary):
    '''Convert an existing dict to a .txt file in our special format
    '''

    txtFile = ''
    for key in dictionary:
        if txtFile:
            txtFile += '\n'
        txtFile += '['+key+']'
        thisKey = dictionary[key]
        if "none" in thisKey:
            txtFile += '\n'+thisKey["none"]
        for category in thisKey:
            if category != "none":
                txtFile += '\n('+category+')'
                txtFile += '\n'+thisKey[category]
    return txtFile