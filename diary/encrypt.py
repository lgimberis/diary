import base64
import os

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

SALT_SIZE_BYTES = 16
DEFAULT_ITERATIONS=100000

class Encryptor:
    def __init__(self, password, salt=None):
        self.password = password
        if salt:
            self.salt = salt
        else:
            self.salt = self.__random_salt()
        self.fernet = self.__get_fernet(self.salt, self.password)

    def __random_salt(self):
        """Get a random salt"""
        return os.urandom(SALT_SIZE_BYTES)

    def __get_fernet(self, iterations=DEFAULT_ITERATIONS):
        '''Returns a Fernet object based on the given salt and password'''

        if(type(salt) is not bytes):
            raise TypeError(f"Salt of type {type(item)} should be of type {type(bytes)}")
        if(type(password) is not bytes):
            raise TypeError(f"Password of type {type(item)} should be of type {type(bytes)}")

        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=self.salt, iterations=iterations, )
        key = base64.urlsafe_b64encode(kdf.derive(self.password))
        return Fernet(key)

    def get_salt(self):
        return self.salt

    def encrypt(self, item):
        """Return an encrypted version of the argument"""
        if type(item) == bytes:
            return self.fernet.encrypt(item)
        else:
            raise TypeError(f"Argument of type {type(item)} should be of type {type(bytes)}")

    def decrypt(self, item):
        """Return a decrypted version of the argument.
        
        May throw cryptography.fernet.InvalidToken or TypeError."""
        if type(item) == bytes:
            return self.fernet.decrypt(item)
        else:
            raise TypeError(f"Argument of type {type(item)} should be of type {type(bytes)}")
