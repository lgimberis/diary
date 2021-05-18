import base64
import os

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class Encryptor:

    SALT_SIZE_BYTES = 16
    DEFAULT_ITERATIONS = 100000

    def __init__(self, password: bytes, salt=b"", iterations=DEFAULT_ITERATIONS):
        self.password = password
        self.iterations = iterations

        if salt:
            self.salt = salt
        else:
            self.salt = Encryptor.random_salt()

        self.fernet = self.__get_fernet()

    @staticmethod
    def random_salt(size=SALT_SIZE_BYTES) -> bytes:
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
        return self.fernet.encrypt(item)

    def decrypt(self, item: bytes) -> bytes:
        """Return a decrypted version of the argument.

        May throw InvalidToken if it wasn't encrypted with the exact same settings.
        """
        return self.fernet.decrypt(item)
