
def getFernet(salt, password):
    '''Returns a Fernet object based on the given salt and password'''

    import base64
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

    if(type(salt) is not bytes):
        raise TypeError("salt passed to getFernet should be in bytes")
    if(type(password) is not bytes):
        raise TypeError("password passed to getFernet should be in bytes")

    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000, )
    key = base64.urlsafe_b64encode(kdf.derive(password))
    return Fernet(key)

def createFile(fileName, modify=True, encrypt=True):
    ''' which is unlocked by the specified password'''

    #Create an empty file if it doesn't already exist
    with open(fileName, mode='w') as f:
        pass

    if(modify):
        #Allow initial content for this file
        modifyFile(fileName)

    if(encrypt):
        #Create the encrypted file based on our salt and the existing file with its content
        encryptFile(fileName, fileName+".secret", fernet, salt)

recognisedEditors = {}

def modifyFile(fileName, editor=None):
    '''Grants the user an opportunity to modify the content of the named file
    
    editor can be None, "manual", or any value in recognisedEditors.
    Accordingly, the behaviour of this function is:
    None: try to use the "system default" text editor,
    manual: require user input to proceed, 
    other: try to launch that specific supported editor'''

    import subprocess, platform
    from time import sleep

    if editor == 'manual':
        #Manual is a special integral case in which the program pauses and the usually manually updates the file.
        input("Please press Enter when you are done modifying the file ...")
    elif editor in recognisedEditors:
        #TODO
        pass
    else:
        #Try to use the 'default' editor
        if platform.system() == 'Windows':
            print("Opening file, please close when finished ...")
            doc = subprocess.Popen(["start", "/WAIT", fileName], shell=True)

            while doc.poll() is None:
                sleep(0.1)
        else:
            raise OSError('Your OS is not supported in modifyFile')

def encryptFile(fileName, delete=True, password=None):
    '''Creates an encrypted file from an unencrypted one'''
    import os, getpass

    #Get passsword from user
    if(password is None):
        myPassword = getpass.getpass()
    else:
        myPassword = password
    myPassword = myPassword.encode('utf-8')

    #Generate a salt
    salt = os.urandom(16)

    #Get fernet object using salt and password
    fernet = getFernet(salt, myPassword)

    eFileName = fileName+".secret"
    with open(eFileName, mode='wb') as e:
        #Write the salt and encrypted password on two separate lines
        e.write(salt + b'\n')
        e.write(fernet.encrypt(myPassword) + b'\n')
        #Write out the file contents
        toWrite = ""
        with open(fileName, mode='r') as f:
            for line in f:
                toWrite += line
        e.write(fernet.encrypt(toWrite.encode('utf-8')))

    if delete:
        os.remove(fileName)

def decryptFile(fileName, delete=True, password=None):
    '''Opens an encrypted file and decrypts its contents'''
    import getpass, os
    import cryptography.exceptions

    #Get passsword from user
    if password is None:
        myPassword = getpass.getpass()
    else:
        myPassword = password
    myPassword = myPassword.encode('utf-8')

    if ".secret" in fileName:
        eFileName = fileName
        fileName = eFileName[:eFileName.rindex('.')]
    else:
        eFileName = fileName+".secret"

    with open(eFileName, mode='rb') as e:
        salt = next(e)
        encryptedPassword = next(e)

        #Remove trailing newlines from both
        salt = salt[:salt.index(b"\n")]
        encryptedPassword = encryptedPassword[:encryptedPassword.index(b"\n")]

        #Get fernet object using salt and password
        fernet = getFernet(salt, myPassword)

        try:
            decryptedPassword = fernet.decrypt(encryptedPassword)

            #Read all content and write into decrypted file
            with open(fileName, mode='w') as f:
                for line in e:
                    decryptedLine = fernet.decrypt(line)
                    f.write(decryptedLine.decode('utf-8'))
        except cryptography.fernet.InvalidToken:
            print("Password does not match file's password")
            return None
    if delete:
        os.remove(eFileName)

def main():
    '''Either creates a file to encrypt, or temporarily decrypts an encrypted file'''
    import sys

    if len(sys.argv) > 1:
        fileName = sys.argv[1]
        if checkPassword(fileName):
            modifyFile(fileName)
    else:
        print("No filename passed; assuming a new file is to be created")
        fileName = input("Please enter a name for the new file:")
        if len(fileName) > 0:
            createFile(fileName)
        else:
            print("No filename entered; no action taken")

if __name__=="__main__":
    main()