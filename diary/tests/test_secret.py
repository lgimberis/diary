import secret
import unittest
import os

#A test case:
# 1) Answers a single question about the code it is testing
# 2) Runs completely by itself
# 3) Returns an objective Fail or Pass
# 4) Runs in isolation and is independent from any others
#test functions should start with test

class EncryptDecryptRoundTrip(unittest.TestCase):
    def roundTrip(self, fileName, fileContent):
        workingDir = os.listdir()
        if fileName in workingDir:
            os.remove(fileName)
    
        with open(fileName, mode='w') as f:
            f.write(fileContent)

        secret.encryptFile(fileName, password="password")

        #Make sure that we don't accidentally read the same file even if the functions don't work
        workingDir = os.listdir()
        if fileName in workingDir:
            os.remove(fileName)

        secret.decryptFile(fileName, password="password")

        roundTripContent = ""
        with open(fileName, mode='r') as f:
            for line in f:
                roundTripContent += line

        os.remove(fileName)

        return roundTripContent

    def test_basic(self):
        fileName = 'secret_test_basic.txt'
        fileContent = 'this\nis\na\ntest\n'

        roundTripContent = self.roundTrip(fileName, fileContent)
        self.assertEqual(fileContent, roundTripContent)

        

if __name__=="__main__":
    unittest.main()
