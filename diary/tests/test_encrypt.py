import os
import unittest

from ..encrypt import Encryptor

class EncryptorTester(unittest.TestCase):
    def testRoundTrip(self):
        """Check that the same password and salt can encrypt and decrypt a message

        """
        password = "correctbatteryhorsestaple".encode('utf-8')
        message = "This is a test message. To be successful, this round trip must return the exact same message.".encode('utf-8')
        encryptor = Encryptor(password)
        second_encryptor = Encryptor(password, encryptor.get_salt())

        encrypted_message = encryptor.encrypt(message)
        decrypted_message = second_encryptor.decrypt(encrypted_message)
        self.assertEqual(message, decrypted_message)

if __name__=="__main__":
    unittest.main()
