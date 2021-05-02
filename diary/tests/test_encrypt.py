import unittest

from diary.encrypt import Encryptor


class EncryptorTester(unittest.TestCase):

    TEST_PASSWORD = "correctbatteryhorsestaple"
    TEST_MESSAGE = "This is a test message."

    def test_round_trip(self):
        """Check that the same password and salt can encrypt and decrypt a message

        """
        password = self.TEST_PASSWORD.encode('utf-8')
        message = self.TEST_MESSAGE.encode('utf-8')
        encryptor = Encryptor(password)
        second_encryptor = Encryptor(password, encryptor.get_salt())

        encrypted_message = encryptor.encrypt(message)
        decrypted_message = second_encryptor.decrypt(encrypted_message)
        self.assertEqual(message, decrypted_message)


if __name__ == "__main__":
    unittest.main()
