# Copyright (c) 2014, Hubert Kario
#
# See the LICENSE file for legal information regarding use of this file.

# compatibility with Python 2.6, for that we need unittest2 package,
# which is not available on 3.3 or 3.4
try:
    import unittest2 as unittest
except ImportError:
    import unittest
from hypothesis import given, example
from hypothesis.strategies import integers
import math

from tlslite.utils.cryptomath import isPrime, numBits, numBytes, numberToByteArray

class TestIsPrime(unittest.TestCase):
    def test_with_small_primes(self):
        self.assertTrue(isPrime(3))
        self.assertTrue(isPrime(5))
        self.assertTrue(isPrime(7))
        self.assertTrue(isPrime(11))

    def test_with_small_composites(self):
        self.assertFalse(isPrime(4))
        self.assertFalse(isPrime(6))
        self.assertFalse(isPrime(9))
        self.assertFalse(isPrime(10))

    def test_with_hard_primes_to_test(self):

        # XXX Rabin-Miller fails to properly detect following composites
        with self.assertRaises(AssertionError):
            for i in range(100):
                # OEIS A014233
                self.assertFalse(isPrime(2047))
                self.assertFalse(isPrime(1373653))
                self.assertFalse(isPrime(25326001))
                self.assertFalse(isPrime(3215031751))
                self.assertFalse(isPrime(2152302898747))
                self.assertFalse(isPrime(3474749660383))
                self.assertFalse(isPrime(341550071728321))
                self.assertFalse(isPrime(341550071728321))
                self.assertFalse(isPrime(3825123056546413051))
                self.assertFalse(isPrime(3825123056546413051))
                self.assertFalse(isPrime(3825123056546413051))

    def test_with_big_primes(self):
        # NextPrime[2^256]
        self.assertTrue(isPrime(115792089237316195423570985008687907853269984665640564039457584007913129640233))
        # NextPrime[2^1024]
        self.assertTrue(isPrime(179769313486231590772930519078902473361797697894230657273430081157732675805500963132708477322407536021120113879871393357658789768814416622492847430639474124377767893424865485276302219601246094119453082952085005768838150682342462881473913110540827237163350510684586298239947245938479716304835356329624224137859))

    def test_with_big_composites(self):
        # NextPrime[2^256]-2 (factors: 71, 1559, 4801, 7703, 28286...8993)
        self.assertFalse(isPrime(115792089237316195423570985008687907853269984665640564039457584007913129640233-2))
        # NextPrime[2^256]+2 (factors: 3^2, 5, 7, 11, 1753, 19063..7643)
        self.assertFalse(isPrime(115792089237316195423570985008687907853269984665640564039457584007913129640233+2))
        # NextPrime[2^1024]-2
        self.assertFalse(isPrime(179769313486231590772930519078902473361797697894230657273430081157732675805500963132708477322407536021120113879871393357658789768814416622492847430639474124377767893424865485276302219601246094119453082952085005768838150682342462881473913110540827237163350510684586298239947245938479716304835356329624224137859-2))
        # NextPrime[2^1024]+2
        self.assertFalse(isPrime(179769313486231590772930519078902473361797697894230657273430081157732675805500963132708477322407536021120113879871393357658789768814416622492847430639474124377767893424865485276302219601246094119453082952085005768838150682342462881473913110540827237163350510684586298239947245938479716304835356329624224137859+2))
        # NextPrime[NextPrime[2^512]]*NextPrime[2^512]
        self.assertFalse(isPrime(179769313486231590772930519078902473361797697894230657273430081157732675805500963132708477322407536021120113879871393357658789768814416622492847430639477074095512480796227391561801824887394139579933613278628104952355769470429079061808809522886423955917442317693387325171135071792698344550223571732405562649211))

class TestNumberToBytesFunctions(unittest.TestCase):
    def test_numberToByteArray(self):
        self.assertEqual(numberToByteArray(0x00000000000001),
                         bytearray(b'\x01'))

    def test_numberToByteArray_with_MSB_number(self):
        self.assertEqual(numberToByteArray(0xff),
                         bytearray(b'\xff'))

    def test_numberToByteArray_with_length(self):
        self.assertEqual(numberToByteArray(0xff, 2),
                         bytearray(b'\x00\xff'))

    def test_numberToByteArray_with_not_enough_length(self):
        self.assertEqual(numberToByteArray(0x0a0b0c, 2),
                         bytearray(b'\x0b\x0c'))

class TestNumBits(unittest.TestCase):

    @staticmethod
    def num_bits(number):
        if number == 0:
            return 0
        return len(bin(number).lstrip('-0b'))

    @staticmethod
    def num_bytes(number):
        if number == 0:
            return 0
        return (TestNumBits.num_bits(number) + 7) // 8

    @given(integers(min_value=0, max_value=1<<16384))
    @example(0)
    @example(255)
    @example(256)
    @example((1<<1024)-1)
    @example((1<<521)-1)
    @example(1<<8192)
    @example((1<<8192)-1)
    def test_numBits(self, number):
        self.assertEqual(numBits(number), self.num_bits(number))

    @given(integers(min_value=0, max_value=1<<16384))
    @example(0)
    @example(255)
    @example(256)
    @example((1<<1024)-1)
    @example((1<<521)-1)
    @example(1<<8192)
    @example((1<<8192)-1)
    def test_numBytes(self, number):
        self.assertEqual(numBytes(number), self.num_bytes(number))
