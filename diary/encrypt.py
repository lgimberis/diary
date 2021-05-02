import base64
import os

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class Encryptor:

    SALT_SIZE_BYTES = 16
    DEFAULT_ITERATIONS = 100000

    def __init__(self, password, salt=None, iterations=DEFAULT_ITERATIONS,
                 salt_size_bytes=SALT_SIZE_BYTES):
        self.password = password
        self.iterations = iterations

        if salt:
            self.salt = salt
        else:
            self.salt = Encryptor.__random_salt(salt_size_bytes)

        try:
            self.fernet = self.__get_fernet()
        except TypeError:
            if type(self.salt) is not bytes:
                raise TypeError(f"Type of salt is {type(self.salt)}, "
                                f"should be {bytes}")
            elif type(self.password) is not bytes:
                raise TypeError(f"Type of password is {type(self.password)}, "
                                f"should be {bytes}")

    @staticmethod
    def __random_salt(size: int) -> bytes:
        """Get a salt with size bytes.

        """
        return os.urandom(size)

    def __get_fernet(self) -> Fernet:
        """Set up and return a Fernet object based on our salt and password.

        """
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32,
                         salt=self.salt, iterations=self.iterations, )
        key = base64.urlsafe_b64encode(kdf.derive(self.password))
        return Fernet(key)

    def get_salt(self):
        return self.salt

    def encrypt(self, item: bytes) -> bytes:
        """Return an encrypted version of the argument.

        """
        try:
            return self.fernet.encrypt(item)
        except TypeError:
            raise TypeError(f"Argument to Encryptor.encrypt must be of type "
                            f"{bytes}, is instead {type(item)}")

    def decrypt(self, item: bytes) -> bytes:
        """Return a decrypted version of the argument.

        May throw InvalidToken if it wasn't encrypted with the exact same settings.
        """
        try:
            return self.fernet.decrypt(item)
        except TypeError:
            raise TypeError(f"Argument to Encryptor.decrypt must be of type "
                            f"{bytes}, is instead {type(item)}")
