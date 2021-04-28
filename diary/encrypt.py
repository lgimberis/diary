import base64
import os

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

SALT_SIZE_BYTES = 16
DEFAULT_ITERATIONS = 100000


class Encryptor:
    def __init__(self, password, salt=None):
        self.password = password
        if salt:
            self.salt = salt
        else:
            self.salt = self.__random_salt()
        try:
            self.fernet = self.__get_fernet(self.salt, self.password)
        except TypeError:
            if type(self.salt) is not bytes:
                raise TypeError(f"Type of salt is {type(self.salt)}, should be {bytes}")
            elif type(self.password) is not bytes:
                raise TypeError(f"Type of password is {type(self.password)}, should be {bytes}")

    @staticmethod
    def __random_salt():
        """Get a random salt"""
        return os.urandom(SALT_SIZE_BYTES)

    @staticmethod
    def __get_fernet(salt, password, iterations=DEFAULT_ITERATIONS):
        """Returns a Fernet object based on the given salt and password

        salt : bytes
        password : bytes
        iterations : integer
        """
        try:
            kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=iterations, )
        except TypeError:
            raise TypeError("Arguments salt and password to __get_fernet ")
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return Fernet(key)

    def get_salt(self):
        return self.salt

    def encrypt(self, item):
        """Return an encrypted version of the argument
        
        item : bytes
        """
        try:
            return self.fernet.encrypt(item)
        except TypeError:
            raise TypeError(f"Argument to Encryptor.encrypt must be of type {bytes}, is instead {type(item)}")

    def decrypt(self, item):
        """Return a decrypted version of the argument.
        
        item : bytes
        
        May throw InvalidToken
        """
        try:
            return self.fernet.decrypt(item)
        except TypeError:
            raise TypeError(f"Argument to Encryptor.decrypt must be of type {bytes}, is instead {type(item)}")
