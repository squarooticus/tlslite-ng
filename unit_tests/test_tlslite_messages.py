# Author: Hubert Kario (c) 2014
# see LICENCE file for legal information regarding use of this file

# compatibility with Python 2.6, for that we need unittest2 package,
# which is not available on 3.3 or 3.4
try:
    import unittest2 as unittest
except ImportError:
    import unittest
from tlslite.messages import ClientHello, ServerHello, RecordHeader3, Alert, \
        RecordHeader2, Message, ClientKeyExchange, ServerKeyExchange, \
        CertificateRequest, CertificateVerify, ServerHelloDone, ServerHello2, \
        ClientMasterKey, ClientFinished, ServerFinished
from tlslite.utils.codec import Parser
from tlslite.constants import CipherSuite, CertificateType, ContentType, \
        AlertLevel, AlertDescription, ExtensionType, ClientCertificateType, \
        HashAlgorithm, SignatureAlgorithm, ECCurveType, GroupName, \
        SSL2HandshakeType
from tlslite.extensions import SNIExtension, ClientCertTypeExtension, \
    SRPExtension, TLSExtension
from tlslite.errors import TLSInternalError

class TestMessage(unittest.TestCase):
    def test___init__(self):
        msg = Message(ContentType.application_data, bytearray(0))

        self.assertEqual(ContentType.application_data, msg.contentType)
        self.assertEqual(bytearray(0), msg.data)

    def test_write(self):
        msg = Message(0, bytearray(10))

        self.assertEqual(bytearray(10), msg.write())

class TestClientHello(unittest.TestCase):
    def test___init__(self):
        client_hello = ClientHello()

        assert client_hello
        self.assertEqual(False, client_hello.ssl2)
        self.assertEqual((0,0), client_hello.client_version)
        self.assertEqual(bytearray(32), client_hello.random)
        self.assertEqual(bytearray(0), client_hello.session_id)
        self.assertEqual([], client_hello.cipher_suites)
        self.assertEqual([], client_hello.compression_methods)

    def test_create(self):
        client_hello = ClientHello()
        client_hello.create((3,0), bytearray(32), bytearray(0), \
                [])

        self.assertEqual((3,0), client_hello.client_version)
        self.assertEqual(bytearray(32), client_hello.random)
        self.assertEqual(bytearray(0), client_hello.session_id)
        self.assertEqual([], client_hello.cipher_suites)
        self.assertEqual([0], client_hello.compression_methods)

    def test_create_with_one_ciphersuite(self):
        client_hello = ClientHello()
        client_hello.create((3,0), bytearray(32), bytearray(0), \
                [CipherSuite.TLS_EMPTY_RENEGOTIATION_INFO_SCSV])

        self.assertEqual((3,0), client_hello.client_version)
        self.assertEqual(bytearray(32), client_hello.random)
        self.assertEqual(bytearray(0), client_hello.session_id)
        self.assertEqual([CipherSuite.TLS_EMPTY_RENEGOTIATION_INFO_SCSV], \
                client_hello.cipher_suites)
        self.assertEqual([0], client_hello.compression_methods)

    def test_create_with_random(self):
        client_hello = ClientHello()
        client_hello.create((3,0), bytearray(b'\x01' + \
                b'\x00'*30 + b'\x02'), bytearray(0), \
                [])

        self.assertEqual((3,0), client_hello.client_version)
        self.assertEqual(bytearray(b'\x01' + b'\x00'*30 + b'\x02'), \
                client_hello.random)
        self.assertEqual(bytearray(0), client_hello.session_id)
        self.assertEqual([], client_hello.cipher_suites)
        self.assertEqual([0], client_hello.compression_methods)

    def test_parse(self):
        p = Parser(bytearray(
            # we don't include the type of message as it is handled by the
            # hello protocol parser
            #b'x01' +             # type of message - client_hello
            b'\x00'*2 + b'\x26' + # length - 38 bytes
            b'\x01\x01' +         # protocol version - arbitrary (invalid)
            b'\x00'*32 +          # client random
            b'\x00' +             # session ID length
            b'\x00'*2 +           # cipher suites length
            b'\x00'               # compression methods length
            ))
        client_hello = ClientHello()
        client_hello = client_hello.parse(p)

        self.assertEqual((1,1), client_hello.client_version)
        self.assertEqual(bytearray(32), client_hello.random)
        self.assertEqual(bytearray(0), client_hello.session_id)
        self.assertEqual([], client_hello.cipher_suites)
        self.assertEqual([], client_hello.compression_methods)
        self.assertEqual(bytearray(0), client_hello.server_name)
        # XXX not sent
        self.assertEqual([0], client_hello.certificate_types)
        self.assertEqual(False, client_hello.supports_npn)
        self.assertEqual(False, client_hello.tack)
        self.assertEqual(None, client_hello.srp_username)
        self.assertEqual(None, client_hello.extensions)

    def test_parse_with_empty_extensions(self):
        p = Parser(bytearray(
            # we don't include the type of message as it is handled by the
            # hello protocol parser
            #b'x01' +             # type of message - client_hello
            b'\x00'*2 + b'\x28' + # length - 38 bytes
            b'\x01\x01' +         # protocol version - arbitrary (invalid)
            b'\x00'*32 +          # client random
            b'\x00' +             # session ID length
            b'\x00'*2 +           # cipher suites length
            b'\x00' +             # compression methods length
            b'\x00\x00'           # extensions length
            ))
        client_hello = ClientHello()
        client_hello = client_hello.parse(p)

        self.assertEqual((1,1), client_hello.client_version)
        self.assertEqual(bytearray(32), client_hello.random)
        self.assertEqual(bytearray(0), client_hello.session_id)
        self.assertEqual([], client_hello.cipher_suites)
        self.assertEqual([], client_hello.compression_methods)
        self.assertEqual([], client_hello.extensions)

    def test_parse_with_SNI_extension(self):
        p = Parser(bytearray(
            # we don't include the type of message as it is handled by the
            # hello protocol parser
            #b'x01' +             # type of message - client_hello
            b'\x00'*2 + b'\x3c' + # length - 60 bytes
            b'\x01\x01' +         # protocol version - arbitrary (invalid)
            b'\x00'*32 +          # client random
            b'\x00' +             # session ID length
            b'\x00'*2 +           # cipher suites length
            b'\x00' +             # compression methods length
            b'\x00\x14' +         # extensions length - 20 bytes
            b'\x00\x00' +         # extension type - SNI (0)
            b'\x00\x10' +         # extension length - 16 bytes
            b'\x00\x0e' +         # length of array - 14 bytes
            b'\x00' +             # type of entry - host_name (0)
            b'\x00\x0b' +         # length of name - 11 bytes
            # UTF-8 encoding of example.com
            b'\x65\x78\x61\x6d\x70\x6c\x65\x2e\x63\x6f\x6d'
            ))
        client_hello = ClientHello()
        client_hello = client_hello.parse(p)

        self.assertEqual((1,1), client_hello.client_version)
        self.assertEqual(bytearray(32), client_hello.random)
        self.assertEqual(bytearray(0), client_hello.session_id)
        self.assertEqual([], client_hello.cipher_suites)
        self.assertEqual([], client_hello.compression_methods)
        self.assertEqual(bytearray(b'example.com'), client_hello.server_name)
        sni = SNIExtension().create(bytearray(b'example.com'))
        self.assertEqual([sni], client_hello.extensions)

    def test_parse_with_cert_type_extension(self):
        p = Parser(bytearray(
            # we don't include the type of message as it is handled by the
            # hello protocol parser
            #b'x01' +             # type of message - client_hello
            b'\x00'*2 + b'\x2f' + # length - 47 bytes
            b'\x01\x01' +         # protocol version - arbitrary (invalid)
            b'\x00'*32 +          # client random
            b'\x00' +             # session ID length
            b'\x00'*2 +           # cipher suites length
            b'\x00' +             # compression methods length
            b'\x00\x07' +         # extensions length - 7 bytes
            b'\x00\x09' +         # extension type - certTypes (9)
            b'\x00\x03' +         # extension length - 3 bytes
            b'\x02' +             # length of array - 2 bytes
            b'\x00' +             # type - x509 (0)
            b'\x01'               # type - opengpg (1)
            ))
        client_hello = ClientHello()
        client_hello = client_hello.parse(p)

        self.assertEqual((1,1), client_hello.client_version)
        self.assertEqual(bytearray(32), client_hello.random)
        self.assertEqual(bytearray(0), client_hello.session_id)
        self.assertEqual([], client_hello.cipher_suites)
        self.assertEqual([], client_hello.compression_methods)
        self.assertEqual([0,1], client_hello.certificate_types)
        certTypes = ClientCertTypeExtension().create([0,1])
        self.assertEqual([certTypes], client_hello.extensions)

    def test_parse_with_SRP_extension(self):
        p = Parser(bytearray(
            # we don't include the type of message as it is handled by the
            # hello protocol parser
            #b'x01' +             # type of message - client_hello
            b'\x00'*2 + b'\x35' + # length - 53 bytes
            b'\x01\x01' +         # protocol version - arbitrary (invalid)
            b'\x00'*32 +          # client random
            b'\x00' +             # session ID length
            b'\x00'*2 +           # cipher suites length
            b'\x00' +             # compression methods length
            b'\x00\x0d' +         # extensions length - 13 bytes
            b'\x00\x0c' +         # extension type - SRP (12)
            b'\x00\x09' +         # extension length - 9 bytes
            b'\x08' +             # length of name - 8 bytes
            b'username'           # UTF-8 encoding of "username" :)
            ))
        client_hello = ClientHello()
        client_hello = client_hello.parse(p)

        self.assertEqual((1,1), client_hello.client_version)
        self.assertEqual(bytearray(32), client_hello.random)
        self.assertEqual(bytearray(0), client_hello.session_id)
        self.assertEqual([], client_hello.cipher_suites)
        self.assertEqual([], client_hello.compression_methods)
        self.assertEqual(bytearray(b'username'), client_hello.srp_username)
        srp = SRPExtension().create(bytearray(b'username'))
        self.assertEqual([srp], client_hello.extensions)

    def test_parse_with_NPN_extension(self):
        p = Parser(bytearray(
            # we don't include the type of message as it is handled by the
            # hello protocol parser
            #b'x01' +             # type of message - client_hello
            b'\x00'*2 + b'\x2c' + # length - 44 bytes
            b'\x01\x01' +         # protocol version - arbitrary (invalid)
            b'\x00'*32 +          # client random
            b'\x00' +             # session ID length
            b'\x00'*2 +           # cipher suites length
            b'\x00' +             # compression methods length
            b'\x00\x04' +         # extensions length - 4 bytes
            b'\x33\x74' +         # extension type - NPN (13172)
            b'\x00\x00'           # extension length - 0 bytes
            ))
        client_hello = ClientHello()
        client_hello = client_hello.parse(p)

        self.assertEqual((1,1), client_hello.client_version)
        self.assertEqual(bytearray(32), client_hello.random)
        self.assertEqual(bytearray(0), client_hello.session_id)
        self.assertEqual([], client_hello.cipher_suites)
        self.assertEqual([], client_hello.compression_methods)
        self.assertEqual(True, client_hello.supports_npn)
        npn = TLSExtension().create(13172, bytearray(0))
        self.assertEqual([npn], client_hello.extensions)

    def test_parse_with_TACK_extension(self):
        p = Parser(bytearray(
            # we don't include the type of message as it is handled by the
            # hello protocol parser
            #b'x01' +             # type of message - client_hello
            b'\x00'*2 + b'\x2c' + # length - 44 bytes
            b'\x01\x01' +         # protocol version - arbitrary (invalid)
            b'\x00'*32 +          # client random
            b'\x00' +             # session ID length
            b'\x00'*2 +           # cipher suites length
            b'\x00' +             # compression methods length
            b'\x00\x04' +         # extensions length - 4 bytes
            b'\xf3\x00' +         # extension type - TACK (62208)
            b'\x00\x00'           # extension length - 0 bytes
            ))
        client_hello = ClientHello()
        client_hello = client_hello.parse(p)

        self.assertEqual((1,1), client_hello.client_version)
        self.assertEqual(bytearray(32), client_hello.random)
        self.assertEqual(bytearray(0), client_hello.session_id)
        self.assertEqual([], client_hello.cipher_suites)
        self.assertEqual([], client_hello.compression_methods)
        self.assertEqual(True, client_hello.tack)
        tack = TLSExtension().create(62208, bytearray(0))
        self.assertEqual([tack], client_hello.extensions)

    def test_write(self):
        # client_hello = ClientHello(ssl2)
        client_hello = ClientHello()

        self.assertEqual(list(bytearray(
            b'\x01' +               # type of message - client_hello
            b'\x00'*2 + b'\x26' +   # length - 38 bytes
            b'\x00'*2 +             # protocol version
            b'\x00'*32 +            # client random
            b'\x00' +               # session ID length
            b'\x00'*2 +             # cipher suites length
            b'\x00'                 # compression methods length
            )), list(client_hello.write()))

    def test_write_with_certificate_types(self):

        # note that ClienHello is "clever" and doesn't send the extension
        # if only x509 certificate type is present, so we pass two values
        client_hello = ClientHello().create((3,1),
                bytearray(b'\x00'*31 + b'\xff'), bytearray(0),
                [], certificate_types=[
                    CertificateType.x509, CertificateType.openpgp])

        self.assertEqual(list(bytearray(
                b'\x01' +               # type of message - client_hello
                b'\x00'*2 + b'\x30' +   # length - 48 bytes
                b'\x03\x01' +           # protocol version (TLS 1.0)
                b'\x00'*31 + b'\xff' +  # client random
                b'\x00' +               # session ID length
                b'\x00\x00' +           # cipher suites length
                b'\x01' +               # compression methods length
                b'\x00' +               # supported method - NULL
                b'\x00\x07' +           # extensions length
                b'\x00\x09' +           # cert_type extension value (9)
                b'\x00\x03' +           # size of the extension
                b'\x02' +               # length of supported types
                b'\x00' +               # type - X.509
                b'\x01'                 # type - OpenPGP
                )), list(client_hello.write()))

    def test_write_with_srp_username(self):
        client_hello = ClientHello().create((3,1),
                bytearray(b'\x00'*31 + b'\xff'), bytearray(0),
                [], srpUsername="example-test")

        self.assertEqual(list(bytearray(
                b'\x01' +               # type of message - client_hello
                b'\x00'*2 + b'\x3a' +   # length - 58 bytes
                b'\x03\x01' +           # protocol version (TLS 1.0)
                b'\x00'*31 + b'\xff' +  # client random
                b'\x00' +               # session ID length
                b'\x00\x00' +           # cipher suites length
                b'\x01' +               # compression methods length
                b'\x00' +               # supported method - NULL
                b'\x00\x11' +           # extensions length
                b'\x00\x0c' +           # srp extension value (12)
                b'\x00\x0d' +           # size of the extension
                b'\x0c' +               # length of name
                # ascii encoding of "example-test":
                b'\x65\x78\x61\x6d\x70\x6c\x65\x2d\x74\x65\x73\x74'
                )), list(client_hello.write()))

    def test_write_with_tack(self):
         client_hello = ClientHello().create((3,1),
                 bytearray(b'\x00'*31 + b'\xff'), bytearray(0),
                 [], tack=True)

         self.assertEqual(list(bytearray(
                b'\x01' +               # type of message - client_hello
                b'\x00'*2 + b'\x2d' +   # length - 45 bytes
                b'\x03\x01' +           # protocol version
                b'\x00'*31 + b'\xff' +  # client random
                b'\x00' +               # session ID length
                b'\x00\x00' +           # cipher suites length
                b'\x01' +               # compression methods length
                b'\x00' +               # supported method - NULL
                b'\x00\x04' +           # extensions length
                b'\xf3\x00' +           # TACK extension value (62208)
                b'\x00\x00'             # size of the extension
                )), list(client_hello.write()))

    def test_write_with_npn(self):
         client_hello = ClientHello().create((3,1),
                 bytearray(b'\x00'*31 + b'\xff'), bytearray(0),
                 [], supports_npn=True)

         self.assertEqual(list(bytearray(
                b'\x01' +               # type of message - client_hello
                b'\x00'*2 + b'\x2d' +   # length - 45 bytes
                b'\x03\x01' +           # protocol version
                b'\x00'*31 + b'\xff' +  # client random
                b'\x00' +               # session ID length
                b'\x00\x00' +           # cipher suites length
                b'\x01' +               # compression methods length
                b'\x00' +               # supported method - NULL
                b'\x00\x04' +           # extensions length
                b'\x33\x74' +           # NPN extension value (13172)
                b'\x00\x00'             # size of the extension
                )), list(client_hello.write()))

    def test_write_with_server_name(self):
         client_hello = ClientHello().create((3,1),
                 bytearray(b'\x00'*31 + b'\xff'), bytearray(0),
                 [], serverName="example.com")

         self.assertEqual(list(bytearray(
                b'\x01' +               # type of message - client_hello
                b'\x00'*2 + b'\x3d' +   # length - 61 bytes
                b'\x03\x01' +           # protocol version
                b'\x00'*31 + b'\xff' +  # client random
                b'\x00' +               # session ID length
                b'\x00\x00' +           # cipher suites length
                b'\x01' +               # compression methods length
                b'\x00' +               # supported method - NULL
                b'\x00\x14' +           # extensions length
                b'\x00\x00' +           # servername extension value (0)
                b'\x00\x10' +           # byte size of the extension
                b'\x00\x0e' +           # length of the list
                b'\x00' +               # name type: host_name (0)
                b'\x00\x0b' +           # length of host name
                # utf-8 encoding of "example.com"
                b'\x65\x78\x61\x6d\x70\x6c\x65\x2e\x63\x6f\x6d'
                )), list(client_hello.write()))

    def test___str__(self):
        client_hello = ClientHello().create((3,0), bytearray(4), bytearray(0),\
                [])

        self.assertEqual("client_hello,version(3.0),random(...),"\
                "session ID(bytearray(b'')),cipher suites([]),"\
                "compression methods([0])", str(client_hello))

    def test___str___with_all_null_session_id(self):
        client_hello = ClientHello().create((3,0), bytearray(4), bytearray(10),\
                [])

        self.assertEqual("client_hello,version(3.0),random(...),"\
                "session ID(bytearray(b'\\x00'*10)),cipher suites([]),"\
                "compression methods([0])", str(client_hello))

    def test___str___with_extensions(self):
        client_hello = ClientHello().create((3,0), bytearray(4), bytearray(0),\
                [],  extensions=[TLSExtension().create(0, bytearray(b'\x00'))])

        self.assertEqual("client_hello,version(3.0),random(...),"\
                "session ID(bytearray(b'')),cipher suites([]),"\
                "compression methods([0]),extensions(["\
                "TLSExtension(extType=0, extData=bytearray(b'\\x00'), "\
                "serverType=False)])",
                str(client_hello))

    def test___repr__(self):
        client_hello = ClientHello().create((3,3), bytearray(1), bytearray(0),\
                [], extensions=[TLSExtension().create(0, bytearray(0))])

        self.assertEqual("ClientHello(ssl2=False, client_version=(3.3), "\
                "random=bytearray(b'\\x00'), session_id=bytearray(b''), "\
                "cipher_suites=[], compression_methods=[0], "\
                "extensions=[TLSExtension(extType=0, "\
                "extData=bytearray(b''), serverType=False)])",
                repr(client_hello))

    def test_getExtension(self):
        client_hello = ClientHello().create((3, 3), bytearray(1), bytearray(0),
                [], extensions=[TLSExtension().create(0, bytearray(0))])

        ext = client_hello.getExtension(1)

        self.assertIsNone(ext)

    def test_getExtension_with_present_id(self):
        client_hello = ClientHello().create((3, 3), bytearray(1), bytearray(0),
                [], extensions=[TLSExtension().create(0, bytearray(0))])

        ext = client_hello.getExtension(0)

        self.assertEqual(ext, TLSExtension().create(0, bytearray(0)))

    def test_getExtension_with_duplicated_extensions(self):
        client_hello = ClientHello().create((3, 3), bytearray(1), bytearray(0),
                [], extensions=[TLSExtension().create(0, bytearray(0)),
                                SNIExtension().create(b'localhost')])

        with self.assertRaises(TLSInternalError):
            client_hello.getExtension(0)

    def test_certificate_types(self):
        client_hello = ClientHello().create((3, 3), bytearray(1), bytearray(0),
                [])

        self.assertEqual(client_hello.certificate_types, [0])

        client_hello.certificate_types = [0, 1]

        self.assertEqual(client_hello.certificate_types, [0, 1])

        client_hello.certificate_types = [0, 1, 2]

        self.assertEqual(client_hello.certificate_types, [0, 1, 2])

        ext = client_hello.getExtension(ExtensionType.cert_type)
        self.assertEqual(ext.certTypes, [0, 1, 2])

    def test_srp_username(self):
        client_hello = ClientHello().create((3, 3), bytearray(1), bytearray(0),
                [])

        self.assertIsNone(client_hello.srp_username)

        client_hello.srp_username = b'my-name'

        self.assertEqual(client_hello.srp_username, b'my-name')

        client_hello.srp_username = b'her-name'

        self.assertEqual(client_hello.srp_username, b'her-name')

        ext = client_hello.getExtension(ExtensionType.srp)
        self.assertEqual(ext.identity, b'her-name')

    def test_tack(self):
        client_hello = ClientHello().create((3, 3), bytearray(1), bytearray(0),
                [])

        self.assertFalse(client_hello.tack)

        client_hello.tack = True

        self.assertTrue(client_hello.tack)

        client_hello.tack = True

        self.assertTrue(client_hello.tack)

        ext = client_hello.getExtension(ExtensionType.tack)
        self.assertIsNotNone(ext)

        client_hello.tack = False

        self.assertFalse(client_hello.tack)

        ext = client_hello.getExtension(ExtensionType.tack)
        self.assertIsNone(ext)

    def test_supports_npn(self):
        client_hello = ClientHello().create((3, 3), bytearray(1), bytearray(0),
                [])

        self.assertFalse(client_hello.supports_npn)

        client_hello.supports_npn = True

        self.assertTrue(client_hello.supports_npn)

        client_hello.supports_npn = True

        self.assertTrue(client_hello.supports_npn)

        ext = client_hello.getExtension(ExtensionType.supports_npn)
        self.assertIsNotNone(ext)

        client_hello.supports_npn = False

        self.assertFalse(client_hello.supports_npn)

        ext = client_hello.getExtension(ExtensionType.supports_npn)
        self.assertIsNone(ext)

    def test_server_name(self):
        client_hello = ClientHello().create((3, 3), bytearray(1), bytearray(0),
                [])

        client_hello.server_name = b'example.com'

        self.assertEqual(client_hello.server_name, b'example.com')

        client_hello.server_name = b'example.org'

        self.assertEqual(client_hello.server_name, b'example.org')

        ext = client_hello.getExtension(ExtensionType.server_name)
        self.assertIsNotNone(ext)

    def test_server_name_other_than_dns_name(self):
        client_hello = ClientHello().create((3, 3), bytearray(1), bytearray(0),
                [])

        sni_ext = SNIExtension().create(serverNames=[\
                SNIExtension.ServerName(1, b'test')])

        client_hello.extensions = [sni_ext]

        self.assertEqual(client_hello.server_name, bytearray(0))

    def test_parse_with_SSLv2_client_hello(self):
        parser = Parser(bytearray(
            # length and type is handled by hello protocol parser
            #b'\x80\x2e' +           # length - 46 bytes
            #b'\x01' +               # message type - client hello
            b'\x00\x02' +           # version - SSLv2
            b'\x00\x15' +           # cipher spec length - 21 bytes
            b'\x00\x00' +           # session ID length - 0 bytes
            b'\x00\x10' +           # challange length - 16 bytes
            b'\x07\x00\xc0' +       # cipher - SSL2_DES_192_EDE3_CBC_WITH_MD5
            b'\x05\x00\x80' +       # cipher - SSL2_IDEA_128_CBC_WITH_MD5
            b'\x03\x00\x80' +       # cipher - SSL2_RC2_CBC_128_CBC_WITH_MD5
            b'\x01\x00\x80' +       # cipher - SSL2_RC4_128_WITH_MD5
            b'\x06\x00\x40' +       # cipher - SSL2_DES_64_CBC_WITH_MD5
            b'\x04\x00\x80' +       # cipher - SSL2_RC2_CBC_128_CBC_WITH_MD5
            b'\x02\x00\x80' +       # cipher - SSL2_RC4_128_EXPORT40_WITH_MD5
            b'\x01' * 16            # challenge
            ))
        client_hello = ClientHello(ssl2=True)

        client_hello = client_hello.parse(parser)

        # the value on the wire is LSB, but should be interpreted MSB for
        # SSL2
        self.assertEqual((0, 2), client_hello.client_version)
        self.assertEqual(bytearray(0), client_hello.session_id)
        self.assertEqual([458944, 327808, 196736, 65664, 393280, 262272,
                          131200],
                         client_hello.cipher_suites)
        self.assertEqual(bytearray(b'\x00'*16 + b'\x01'*16),
                         client_hello.random)
        self.assertEqual([0], client_hello.compression_methods)

    def test_parse_with_SSLv2_client_hello(self):
        parser = Parser(bytearray(
            # length and type is handled by hello protocol parser
            #b'\x80\x2e' +           # length - 46 bytes
            #b'\x01' +               # message type - client hello
            b'\x03\x02' +           # version - TLSv1.1
            b'\x00\x06' +           # cipher spec length - 6 bytes
            b'\x00\x10' +           # session ID length - 16 bytes
            b'\x00\x20' +           # challange length - 32 bytes
            b'\x07\x00\xc0' +       # cipher - SSL2_DES_192_EDE3_CBC_WITH_MD5
            b'\x00\x00\x2f' +       # cipher - TLS_RSA_WITH_AES_128_CBC_SHA
            b'\xff' * 16 +          # session_id
            b'\x01' * 32            # challenge
            ))
        client_hello = ClientHello(ssl2=True)

        client_hello = client_hello.parse(parser)

        # the value on the wire is LSB, but should be interpreted MSB for
        # SSL2
        self.assertEqual((3, 2), client_hello.client_version)
        self.assertEqual(bytearray(b'\xff'*16), client_hello.session_id)
        self.assertEqual([458944, CipherSuite.TLS_RSA_WITH_AES_128_CBC_SHA],
                         client_hello.cipher_suites)
        self.assertEqual(bytearray(b'\x01'*32),
                         client_hello.random)
        self.assertEqual([0], client_hello.compression_methods)

    def test_write_with_SSLv2(self):
        client_hello = ClientHello(ssl2=True)
        ciphers = [0x0700c0,
                   CipherSuite.TLS_RSA_WITH_AES_128_CBC_SHA]

        client_hello.create((3, 2), random=bytearray(b'\xab'*16),
                            session_id=bytearray(0),
                            cipher_suites=ciphers)

        self.assertEqual(bytearray(
            b'\x01' +             # type of message - CLIENT HELLO
            b'\x03\x02' +         # version - TLSv1.1
            b'\x00\x06' +         # cipher list length
            b'\x00\x00' +         # session id length
            b'\x00\x10' +         # challange length
            b'\x07\x00\xc0' +     # cipher - SSL2_DES_192_EDE3_CBC_WITH_MD5
            b'\x00\x00\x2f' +     # cipher - TLS_RSA_WITH_AES_128_CBC_SHA
            b'\xab'*16),          # challange
            client_hello.write())

class TestServerHello(unittest.TestCase):
    def test___init__(self):
        server_hello = ServerHello()

        self.assertEqual((0,0), server_hello.server_version)
        self.assertEqual(bytearray(32), server_hello.random)
        self.assertEqual(bytearray(0), server_hello.session_id)
        self.assertEqual(0, server_hello.cipher_suite)
        self.assertEqual(CertificateType.x509, server_hello.certificate_type)
        self.assertEqual(0, server_hello.compression_method)
        self.assertEqual(None, server_hello.tackExt)
        self.assertEqual(None, server_hello.next_protos_advertised)
        self.assertEqual(None, server_hello.next_protos)

    def test_create(self):
        server_hello = ServerHello().create(
                (1,1),                          # server version
                bytearray(b'\x00'*31+b'\x01'),  # random
                bytearray(0),                   # session id
                4,                              # cipher suite
                1,                              # certificate type
                None,                           # TACK ext
                None)                           # next protos advertised

        self.assertEqual((1,1), server_hello.server_version)
        self.assertEqual(bytearray(b'\x00'*31 + b'\x01'), server_hello.random)
        self.assertEqual(bytearray(0), server_hello.session_id)
        self.assertEqual(4, server_hello.cipher_suite)
        self.assertEqual(CertificateType.openpgp, server_hello.certificate_type)
        self.assertEqual(0, server_hello.compression_method)
        self.assertEqual(None, server_hello.tackExt)
        self.assertEqual(None, server_hello.next_protos_advertised)

    def test_create_with_minimal_options(self):
        server_hello = ServerHello().create(
                (3, 3),                                 # server version
                bytearray(b'\x02'*31+b'\x01'),          # random
                bytearray(4),                           # session ID
                CipherSuite.TLS_RSA_WITH_RC4_128_MD5)   # ciphersuite

        self.assertEqual(bytearray(
            b'\x02' +                   # type of message
            b'\x00\x00\x2a' +           # length
            b'\x03\x03' +               # server version
            b'\x02'*31+b'\x01' +        # random
            b'\x04' +                   # Session ID length
            b'\x00'*4 +                 # session id
            b'\x00\x04' +               # selected ciphersuite
            b'\x00'                     # selected compression method
            ), server_hello.write())

    def test_parse(self):
        p = Parser(bytearray(
            # don't include type of message as it is handled by the hello
            # protocol layer
            # b'\x02' +                     # type of message - server_hello
            b'\x00\x00\x36' +               # length - 54 bytes
            b'\x03\x03' +                   # version - TLS 1.2
            b'\x01'*31 + b'\x02' +          # random
            b'\x00' +                       # session id length
            b'\x00\x9d' +                   # cipher suite
            b'\x01' +                       # compression method (zlib)
            b'\x00\x0e' +                   # extensions length - 14 bytes
            b'\xff\x01' +                   # ext type - renegotiation_info
            b'\x00\x01' +                   # ext length - 1 byte
            b'\x00' +                       # value - supported (0)
            b'\x00\x23' +                   # ext type - session ticket (35)
            b'\x00\x00' +                   # ext length - 0 bytes
            b'\x00\x0f' +                   # ext type - heartbeat (15)
            b'\x00\x01' +                   # ext length - 1 byte
            b'\x01'))                       # peer allowed to send requests (1)
        server_hello = ServerHello()
        server_hello = server_hello.parse(p)

        self.assertEqual((3,3), server_hello.server_version)
        self.assertEqual(bytearray(b'\x01'*31 + b'\x02'), server_hello.random)
        self.assertEqual(bytearray(0), server_hello.session_id)
        self.assertEqual(157, server_hello.cipher_suite)
        # XXX not sent by server!
        self.assertEqual(CertificateType.x509, server_hello.certificate_type)
        self.assertEqual(1, server_hello.compression_method)
        self.assertEqual(None, server_hello.tackExt)
        self.assertEqual(None, server_hello.next_protos_advertised)

    def test_parse_with_length_short_by_one(self):
        p = Parser(bytearray(
            # don't include type of message as it is handled by the hello
            # protocol layer
            # b'\x02' +                     # type of message - server_hello
            b'\x00\x00\x25' +               # length - 37 bytes (one short)
            b'\x03\x03' +                   # version - TLS 1.2
            b'\x01'*31 + b'\x02' +          # random
            b'\x00' +                       # session id length
            b'\x00\x9d' +                   # cipher suite
            b'\x01'                         # compression method (zlib)
            ))
        server_hello = ServerHello()
        with self.assertRaises(SyntaxError) as context:
            server_hello.parse(p)

        # TODO the message probably could be more descriptive...
        self.assertIsNone(context.exception.msg)

    def test_parse_with_length_long_by_one(self):
        p = Parser(bytearray(
            # don't include type of message as it is handled by the hello
            # protocol layer
            # b'\x02' +                     # type of message - server_hello
            b'\x00\x00\x27' +               # length - 39 bytes (one long)
            b'\x03\x03' +                   # version - TLS 1.2
            b'\x01'*31 + b'\x02' +          # random
            b'\x00' +                       # session id length
            b'\x00\x9d' +                   # cipher suite
            b'\x01'                         # compression method (zlib)
            ))
        server_hello = ServerHello()
        with self.assertRaises(SyntaxError) as context:
            server_hello.parse(p)

        # TODO the message probably could be more descriptive...
        self.assertIsNone(context.exception.msg)

    def test_parse_with_extensions_length_short_by_one(self):
        p = Parser(bytearray(
            # don't include type of message as it is handled by the hello
            # protocol layer
            # b'\x02' +                     # type of message - server_hello
            b'\x00\x00\x36' +               # length - 54 bytes
            b'\x03\x03' +                   # version - TLS 1.2
            b'\x01'*31 + b'\x02' +          # random
            b'\x00' +                       # session id length
            b'\x00\x9d' +                   # cipher suite
            b'\x01' +                       # compression method (zlib)
            b'\x00\x0d' +                   # extensions length - 13 bytes (!)
            b'\xff\x01' +                   # ext type - renegotiation_info
            b'\x00\x01' +                   # ext length - 1 byte
            b'\x00' +                       # value - supported (0)
            b'\x00\x23' +                   # ext type - session ticket (35)
            b'\x00\x00' +                   # ext length - 0 bytes
            b'\x00\x0f' +                   # ext type - heartbeat (15)
            b'\x00\x01' +                   # ext length - 1 byte
            b'\x01'))                       # peer allowed to send requests (1)
        server_hello = ServerHello()

        with self.assertRaises(SyntaxError) as context:
            server_hello.parse(p)

        # TODO the message could be more descriptive...
        self.assertIsNone(context.exception.msg)

    def test_parse_with_extensions_length_long_by_one(self):
        p = Parser(bytearray(
            # don't include type of message as it is handled by the hello
            # protocol layer
            # b'\x02' +                     # type of message - server_hello
            b'\x00\x00\x36' +               # length - 54 bytes
            b'\x03\x03' +                   # version - TLS 1.2
            b'\x01'*31 + b'\x02' +          # random
            b'\x00' +                       # session id length
            b'\x00\x9d' +                   # cipher suite
            b'\x01' +                       # compression method (zlib)
            b'\x00\x0f' +                   # extensions length - 15 bytes (!)
            b'\xff\x01' +                   # ext type - renegotiation_info
            b'\x00\x01' +                   # ext length - 1 byte
            b'\x00' +                       # value - supported (0)
            b'\x00\x23' +                   # ext type - session ticket (35)
            b'\x00\x00' +                   # ext length - 0 bytes
            b'\x00\x0f' +                   # ext type - heartbeat (15)
            b'\x00\x01' +                   # ext length - 1 byte
            b'\x01'))                       # peer allowed to send requests (1)
        server_hello = ServerHello()

        with self.assertRaises(SyntaxError) as context:
            server_hello.parse(p)

        # TODO the message could be more descriptive...
        self.assertIsNone(context.exception.msg)

    def test_parse_with_cert_type_extension(self):
        p = Parser(bytearray(
            b'\x00\x00\x2d' +               # length - 45 bytes
            b'\x03\x03' +                   # version - TLS 1.2
            b'\x01'*31 + b'\x02' +          # random
            b'\x00' +                       # session id length
            b'\x00\x9d' +                   # cipher suite
            b'\x00' +                       # compression method (none)
            b'\x00\x05' +                   # extensions length - 5 bytes
            b'\x00\x09' +                   # ext type - cert_type (9)
            b'\x00\x01' +                   # ext length - 1 byte
            b'\x01'                         # value - OpenPGP (1)
            ))

        server_hello = ServerHello().parse(p)
        self.assertEqual(1, server_hello.certificate_type)

    def test_parse_with_bad_cert_type_extension(self):
        p = Parser(bytearray(
            b'\x00\x00\x2e' +               # length - 46 bytes
            b'\x03\x03' +                   # version - TLS 1.2
            b'\x01'*31 + b'\x02' +          # random
            b'\x00' +                       # session id length
            b'\x00\x9d' +                   # cipher suite
            b'\x00' +                       # compression method (none)
            b'\x00\x06' +                   # extensions length - 5 bytes
            b'\x00\x09' +                   # ext type - cert_type (9)
            b'\x00\x02' +                   # ext length - 2 bytes
            b'\x00\x01'                     # value - X.509 (0), OpenPGP (1)
            ))

        server_hello = ServerHello()
        with self.assertRaises(SyntaxError) as context:
            server_hello.parse(p)

    def test_parse_with_NPN_extension(self):
        p = Parser(bytearray(
            b'\x00\x00\x3c' +               # length - 60 bytes
            b'\x03\x03' +                   # version - TLS 1.2
            b'\x01'*31 + b'\x02' +          # random
            b'\x00' +                       # session id length
            b'\x00\x9d' +                   # cipher suite
            b'\x00' +                       # compression method (none)
            b'\x00\x14' +                   # extensions length - 20 bytes
            b'\x33\x74' +                   # ext type - npn
            b'\x00\x10' +                   # ext length - 16 bytes
            b'\x08' +                       # length of first name - 8 bytes
            b'http/1.1' +
            b'\x06' +                       # length of second name - 6 bytes
            b'spdy/3'
            ))

        server_hello = ServerHello().parse(p)

        self.assertEqual([bytearray(b'http/1.1'), bytearray(b'spdy/3')],
                server_hello.next_protos)

    def test_write(self):
        server_hello = ServerHello().create(
                (1,1),                          # server version
                bytearray(b'\x00'*31+b'\x02'),  # random
                bytearray(0),                   # session id
                4,                              # cipher suite
                None,                           # certificate type
                None,                           # TACK ext
                None)                           # next protos advertised

        self.assertEqual(list(bytearray(
            b'\x02' +               # type of message - server_hello
            b'\x00\x00\x26' +       # length
            b'\x01\x01' +           # proto version
            b'\x00'*31 + b'\x02' +  # random
            b'\x00' +               # session id length
            b'\x00\x04' +           # cipher suite
            b'\x00'                 # compression method
            )), list(server_hello.write()))

    def test_write_with_next_protos(self):
        server_hello = ServerHello().create(
                (1,1),                          # server version
                bytearray(b'\x00'*31+b'\x02'),  # random
                bytearray(0),                   # session id
                4,                              # cipher suite
                0,                              # certificate type
                None,                           # TACK ext
                [b'spdy/3', b'http/1.1'])       # next protos advertised

        self.assertEqual(list(bytearray(
            b'\x02' +               # type of message - server_hello
            b'\x00\x00\x3c' +       # length
            b'\x01\x01' +           # proto version
            b'\x00'*31 + b'\x02' +  # random
            b'\x00' +               # session id length
            b'\x00\x04' +           # cipher suite
            b'\x00' +               # compression method
            b'\x00\x14' +           # extensions length
            b'\x33\x74' +           # ext type - NPN (13172)
            b'\x00\x10' +           # ext length - 16 bytes
            b'\x06' +               # first entry length - 6 bytes
            # utf-8 encoding of 'spdy/3'
            b'\x73\x70\x64\x79\x2f\x33'
            b'\x08' +               # second entry length - 8 bytes
            # utf-8 endoding of 'http/1.1'
            b'\x68\x74\x74\x70\x2f\x31\x2e\x31'
            )), list(server_hello.write()))

    def test___str__(self):
        server_hello = ServerHello()
        server_hello = server_hello.create(
                (3,0),
                bytearray(b'\x00'*32),
                bytearray(b'\x01\x20'),
                34500,
                0,
                None,
                None)

        self.assertEqual("server_hello,length(40),version(3.0),random(...),"\
                "session ID(bytearray(b'\\x01 ')),cipher(0x86c4),"\
                "compression method(0)",
                str(server_hello))

    def test___repr__(self):
        server_hello = ServerHello()
        server_hello = server_hello.create(
                (3,0),
                bytearray(b'\x00'*32),
                bytearray(0),
                34500,
                0,
                None,
                None,
                extensions=[])
        self.maxDiff = None
        self.assertEqual("ServerHello(server_version=(3, 0), "\
                "random=bytearray(b'\\x00\\x00"\
                "\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00"\
                "\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00"\
                "\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00'), "\
                "session_id=bytearray(b''), "\
                "cipher_suite=34500, compression_method=0, _tack_ext=None, "\
                "extensions=[])", repr(server_hello))

class TestServerHello2(unittest.TestCase):
    def test___init__(self):
        sh = ServerHello2()

        self.assertIsNotNone(sh)

    def test_create(self):
        sh = ServerHello2()

        sh = sh.create(1, 2, (3, 4), bytearray(b'\x05'), [6, 7],
                       bytearray(b'\x08\x09'))

        self.assertEqual(sh.session_id_hit, 1)
        self.assertEqual(sh.certificate_type, 2)
        self.assertEqual(sh.server_version, (3, 4))
        self.assertEqual(sh.certificate, bytearray(b'\x05'))
        self.assertEqual(sh.ciphers, [6, 7])
        self.assertEqual(sh.session_id, bytearray(b'\x08\x09'))

    def test_write(self):
        sh = ServerHello2()
        sh = sh.create(1, 2, (3, 4), bytearray(b'\x05'), [6, 7],
                       bytearray(b'\x08\x09'))

        self.assertEqual(bytearray(
            b'\x04' +           # type - SERVER-HELLO
            b'\x01' +           # session ID hit
            b'\x02' +           # certificate_type
            b'\x03\x04' +       # version
            b'\x00\x01' +       # certificate length
            b'\x00\x06' +       # ciphers length
            b'\x00\x02' +       # session ID length
            b'\x05' +           # certificate
            b'\x00\x00\x06' +   # first cipher
            b'\x00\x00\x07' +   # second cipher
            b'\x08\x09'         # session ID
            ), sh.write())

    def test_parse(self):
        p = Parser(bytearray(
            # don't include type of message as it is handled by the
            # record layer protocol
            #b'\x04' +           # type - SERVER-HELLO
            b'\x01' +           # session ID hit
            b'\x02' +           # certificate_type
            b'\x03\x04' +       # version
            b'\x00\x01' +       # certificate length
            b'\x00\x06' +       # ciphers length
            b'\x00\x02' +       # session ID length
            b'\x05' +           # certificate
            b'\x00\x00\x06' +   # first cipher
            b'\x00\x00\x07' +   # second cipher
            b'\x08\x09'         # session ID
            ))
        sh = ServerHello2()
        sh = sh.parse(p)

        self.assertEqual(sh.session_id_hit, 1)
        self.assertEqual(sh.certificate_type, 2)
        self.assertEqual(sh.server_version, (3, 4))
        self.assertEqual(sh.certificate, bytearray(b'\x05'))
        self.assertEqual(sh.ciphers, [6, 7])
        self.assertEqual(sh.session_id, bytearray(b'\x08\x09'))

    def test_write_with_invalid_version(self):
        sh = ServerHello2()
        sh = sh.create(1, 2, (3, 4, 12), bytearray(b'\x05'), [6, 7],
                       bytearray(b'\x08\x09'))

        with self.assertRaises(ValueError):
            sh.write()

class TestRecordHeader2(unittest.TestCase):
    def test___init__(self):
        rh = RecordHeader2()

        self.assertTrue(rh.ssl2)
        self.assertEqual(0, rh.type)
        self.assertEqual((0, 0), rh.version)

    def test_parse(self):
        parser = Parser(bytearray(
            b'\x80' +       # head
            b'\x12'         # length
            ))

        rh = RecordHeader2()
        rh = rh.parse(parser)

        self.assertTrue(rh.ssl2)
        self.assertEqual(ContentType.handshake, rh.type)
        self.assertEqual((2, 0), rh.version)
        self.assertEqual(18, rh.length)

    def test_parse_with_invalid_header(self):
        parser = Parser(bytearray(
            b'\x00' +       # header (bad)
            b'\x12'         # length
            ))

        rh = RecordHeader2()
        with self.assertRaises(SyntaxError):
            rh.parse(parser)

    def test_parse_with_very_long_message(self):
        parser = Parser(bytearray(
            b'\x82' +       # header and a nibble of length
            b'\x00'
            ))

        rh = RecordHeader2()

        rh = rh.parse(parser)

        self.assertEqual(512, rh.length)
        self.assertEqual(0, rh.padding)

    def test_parse_with_3_byte_long_header(self):
        parser = Parser(bytearray(
            b'\x02' +       # 3 byte header and nibble of length
            b'\x00' +       # second byte of length
            b'\x0a'         # padding length
            ))

        rh = RecordHeader2()
        rh = rh.parse(parser)

        self.assertEqual(512, rh.length)
        self.assertEqual(10, rh.padding)

    def test_parse_with_2_byte_header_and_security_escape_bit_set(self):
        parser = Parser(bytearray(
            b'\xc0' +
            b'\x12'))

        rh = RecordHeader2()
        rh = rh.parse(parser)
        self.assertEqual(0x4012, rh.length)
        self.assertEqual(0, rh.padding)
        self.assertFalse(rh.securityEscape)

    def test_parse_with_3_byte_header_and_security_escape_bit_set(self):
        parser = Parser(bytearray(
            b'\x40' +
            b'\x12' +
            b'\x01'))

        rh = RecordHeader2()
        rh = rh.parse(parser)
        self.assertEqual(0x0012, rh.length)
        self.assertEqual(1, rh.padding)
        self.assertTrue(rh.securityEscape)

    def test_create(self):
        rh = RecordHeader2()
        rh.create(512)

        self.assertEqual(512, rh.length)
        self.assertEqual(0, rh.padding)
        self.assertFalse(rh.securityEscape)

    def test_write(self):
        rh = RecordHeader2()
        rh.create(0x0123)

        data = rh.write()

        self.assertEqual(bytearray(
            b'\x81'
            b'\x23'), data)

    def test_write_with_padding(self):
        rh = RecordHeader2()
        rh.create(0x0123, padding=12)

        data = rh.write()

        self.assertEqual(bytearray(
            b'\x01'
            b'\x23'
            b'\x0c'), data)

    def test_write_with_security_escape(self):
        rh = RecordHeader2()
        rh.create(0x0123, securityEscape=True)

        data = rh.write()

        self.assertEqual(bytearray(
            b'\x41'
            b'\x23'
            b'\x00'), data)

    def test_write_with_large_data_and_short_header(self):
        rh = RecordHeader2()
        rh.create(0x7fff)

        data = rh.write()

        self.assertEqual(bytearray(
            b'\xff'
            b'\xff'), data)

    def test_write_with_too_long_length_and_short_header(self):
        rh = RecordHeader2()
        rh.create(0x8000)

        with self.assertRaises(ValueError):
            rh.write()

    def test_write_with_long_length_and_long_header(self):
        rh = RecordHeader2()
        rh.create(0x3fff, padding=1)

        data = rh.write()

        self.assertEqual(bytearray(
            b'\x3f'
            b'\xff'
            b'\x01'), data)

    def test_write_with_too_long_length_and_long_header(self):
        rh = RecordHeader2()
        rh.create(0x4000, padding=1)

        with self.assertRaises(ValueError):
            rh.write()

class TestRecordHeader3(unittest.TestCase):
    def test___init__(self):
        rh = RecordHeader3()

        self.assertEqual(0, rh.type)
        self.assertEqual((0, 0), rh.version)
        self.assertEqual(0, rh.length)
        self.assertFalse(rh.ssl2)

    def test_create(self):
        rh = RecordHeader3()

        rh = rh.create((3, 3), ContentType.application_data, 10)

        self.assertEqual((3, 3), rh.version)
        self.assertEqual(ContentType.application_data, rh.type)
        self.assertEqual(10, rh.length)
        self.assertFalse(rh.ssl2)

    def test_write(self):
        rh = RecordHeader3()

        rh = rh.create((3, 3), ContentType.application_data, 10)

        self.assertEqual(bytearray(
            b'\x17' +       # protocol type
            b'\x03\x03' +   # protocol version
            b'\x00\x0a'     # length
            ), rh.write())

    def test_write_with_too_big_length(self):
        rh = RecordHeader3()

        rh = rh.create((3, 3), ContentType.application_data, 2**17)

        with self.assertRaises(ValueError):
            rh.write()

    def test_parse(self):
        parser = Parser(bytearray(
            b'\x17' +       # protocol type - app data
            b'\x03\x03' +   # protocol version
            b'\x00\x0f'     # length
            ))

        rh = RecordHeader3()

        rh = rh.parse(parser)

        self.assertFalse(rh.ssl2)
        self.assertEqual(ContentType.application_data, rh.type)
        self.assertEqual((3, 3), rh.version)
        self.assertEqual(15, rh.length)

    def test_typeName(self):
        rh = RecordHeader3()
        rh = rh.create((3,0), ContentType.application_data, 0)

        self.assertEqual("application_data", rh.typeName)

    def test___str__(self):
        rh = RecordHeader3()
        rh = rh.create((3,0), ContentType.handshake, 12)

        self.assertEqual("SSLv3 record,version(3.0),content type(handshake)," +\
                "length(12)", str(rh))

    def test___str___with_invalid_content_type(self):
        rh = RecordHeader3()
        rh = rh.create((3,3), 12, 0)

        self.assertEqual("SSLv3 record,version(3.3)," +\
                "content type(unknown(12)),length(0)",
                str(rh))

    def test___repr__(self):
        rh = RecordHeader3()
        rh = rh.create((3,0), ContentType.application_data, 256)

        self.assertEqual("RecordHeader3(type=23, version=(3.0), length=256)",
                repr(rh))

class TestAlert(unittest.TestCase):
    def test___init__(self):
        alert = Alert()

        self.assertEqual(alert.contentType, ContentType.alert)
        self.assertEqual(alert.level, 0)
        self.assertEqual(alert.description, 0)

    def test_levelName(self):
        alert = Alert().create(AlertDescription.record_overflow,
                AlertLevel.fatal)

        self.assertEqual("fatal", alert.levelName)

    def test_levelName_with_wrong_level(self):
        alert = Alert().create(AlertDescription.close_notify, 11)

        self.assertEqual("unknown(11)", alert.levelName)

    def test_descriptionName(self):
        alert = Alert().create(AlertDescription.record_overflow,
                AlertLevel.fatal)

        self.assertEqual("record_overflow", alert.descriptionName)

    def test_descriptionName_with_wrong_id(self):
        alert = Alert().create(1)

        self.assertEqual("unknown(1)", alert.descriptionName)

    def test___str__(self):
        alert = Alert().create(AlertDescription.record_overflow,
                AlertLevel.fatal)

        self.assertEqual("Alert, level:fatal, description:record_overflow",
                str(alert))

    def test___repr__(self):
        alert = Alert().create(AlertDescription.record_overflow,
                AlertLevel.fatal)

        self.assertEqual("Alert(level=2, description=22)", repr(alert))

    def test_parse(self):
        alert = Alert()

        parser = Parser(bytearray(
            b'\x01' +           # level
            b'\x02'             # description
            ))

        alert = alert.parse(parser)

        self.assertEqual(alert.level, 1)
        self.assertEqual(alert.description, 2)

    def test_parse_with_missing_data(self):
        alert = Alert()

        parser = Parser(bytearray(
            b'\x01'))           # level

        with self.assertRaises(SyntaxError):
            alert.parse(parser)

    def test_write(self):
        alert = Alert().create(AlertDescription.record_overflow)

        self.assertEqual(bytearray(
            b'\x02\x16'), alert.write())

class TestClientKeyExchange(unittest.TestCase):
    def test___init__(self):
        cke = ClientKeyExchange(CipherSuite.TLS_RSA_WITH_AES_128_CBC_SHA)

        self.assertIsNotNone(cke)
        self.assertIsNone(cke.version)
        self.assertEqual(0, cke.srp_A)
        self.assertEqual(CipherSuite.TLS_RSA_WITH_AES_128_CBC_SHA,
                         cke.cipherSuite)
        self.assertEqual(bytearray(0), cke.encryptedPreMasterSecret)

    def test_createSRP(self):
        cke = ClientKeyExchange(CipherSuite.TLS_SRP_SHA_WITH_AES_128_CBC_SHA)

        cke.createSRP(2**128+3)

        bts = cke.write()

        self.assertEqual(bts, bytearray(
            b'\x10' +           # CKE
            b'\x00\x00\x13' +   # Handshake message length
            b'\x00\x11' +       # length of value
            b'\x01' +           # 2...
            b'\x00'*15 +        # ...**128...
            b'\x03'))           # ...+3

    def test_createRSA(self):
        cke = ClientKeyExchange(CipherSuite.TLS_RSA_WITH_AES_256_CBC_SHA,
                                (3, 3))

        cke.createRSA(bytearray(12))

        bts = cke.write()

        self.assertEqual(bts, bytearray(
            b'\x10' +           # CKE
            b'\x00\x00\x0e' +   # Handshake message length
            b'\x00\x0c' +       # length of encrypted value
            b'\x00'*12))

    def test_createRSA_with_SSL3(self):
        cke = ClientKeyExchange(CipherSuite.TLS_RSA_WITH_AES_256_CBC_SHA,
                                (3, 0))

        cke.createRSA(bytearray(12))

        bts = cke.write()

        self.assertEqual(bts, bytearray(
            b'\x10' +           # CKE
            b'\x00\x00\x0c' +   # Handshake message length
            b'\x00'*12))

    def test_createDH(self):
        cke = ClientKeyExchange(CipherSuite.TLS_DH_ANON_WITH_AES_128_CBC_SHA)

        cke.createDH(2**64+3)

        bts = cke.write()

        self.assertEqual(bts, bytearray(
            b'\x10' +
            b'\x00\x00\x0b' +
            b'\x00\x09' +
            b'\x01' + b'\x00'*7 + b'\x03'))

    def test_createECDH(self):
        cke = ClientKeyExchange(CipherSuite.TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA)

        cke.createECDH(bytearray(b'\x04\xff\xab'))

        bts = cke.write()

        self.assertEqual(bts, bytearray(
            b'\x10'         # type - CKE
            b'\x00\x00\x04' # overall length
            b'\x03'         # length of point encoding
            b'\x04\xff\xab' # point encoding
            ))

    def test_createRSA_with_unset_protocol(self):
        cke = ClientKeyExchange(CipherSuite.TLS_RSA_WITH_AES_128_CBC_SHA)

        cke.createRSA(bytearray(12))

        with self.assertRaises(AssertionError):
            cke.write()

    def test_write_with_unknown_cipher_suite(self):
        cke = ClientKeyExchange(0)

        with self.assertRaises(AssertionError):
            cke.write()

    def test_write_with_DHE_RSA(self):
        cke = ClientKeyExchange(CipherSuite.TLS_DHE_RSA_WITH_AES_128_CBC_SHA,
                                (3, 1))

        cke.createDH(2**64+3)

        self.assertEqual(cke.write(), bytearray(
            b'\x10' +
            b'\x00\x00\x0b' +
            b'\x00\x09' +
            b'\x01' + b'\x00'*7 + b'\x03'))

    def test_parse_with_RSA(self):
        cke = ClientKeyExchange(CipherSuite.TLS_RSA_WITH_3DES_EDE_CBC_SHA,
                                (3, 1))

        parser = Parser(bytearray(
            b'\x00\x00\x0e' +
            b'\x00\x0c' +
            b'\x00'*12))

        cke.parse(parser)

        self.assertEqual(bytearray(12), cke.encryptedPreMasterSecret)

    def test_parse_with_RSA_in_SSL3(self):
        cke = ClientKeyExchange(CipherSuite.TLS_RSA_WITH_3DES_EDE_CBC_SHA,
                                (3, 0))

        parser = Parser(bytearray(
            b'\x00\x00\x0c' +
            b'\x00'*12))

        cke.parse(parser)

        self.assertEqual(bytearray(12), cke.encryptedPreMasterSecret)

    def test_parse_with_RSA_and_unset_protocol(self):
        cke = ClientKeyExchange(CipherSuite.TLS_RSA_WITH_3DES_EDE_CBC_SHA)

        parser = Parser(bytearray(
            b'\x00\x00\x0c' +
            b'x\00'*12))

        with self.assertRaises(AssertionError):
            cke.parse(parser)

    def test_parse_with_SRP(self):
        cke = ClientKeyExchange(CipherSuite.TLS_SRP_SHA_WITH_AES_128_CBC_SHA)

        parser = Parser(bytearray(
            b'\x00\x00\x0a' +
            b'\x00\x08' +
            b'\x00'*7 + b'\xff'))

        cke.parse(parser)

        self.assertEqual(255, cke.srp_A)

    def test_parse_with_DH(self):
        cke = ClientKeyExchange(CipherSuite.TLS_DH_ANON_WITH_AES_128_CBC_SHA)

        parser = Parser(bytearray(
            b'\x00\x00\x0a' +
            b'\x00\x08' +
            b'\x01' + b'\x00'*7))

        cke.parse(parser)

        self.assertEqual(2**56, cke.dh_Yc)

    def test_parse_with_ECDH(self):
        cke = ClientKeyExchange(CipherSuite.TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA)

        parser = Parser(bytearray(
            b'\x00\x00\x04'
            b'\x03'
            b'\x04\xff\xcd'
            ))

        cke.parse(parser)

        self.assertEqual(cke.ecdh_Yc, bytearray(b'\x04\xff\xcd'))

    def test_parse_with_unknown_cipher(self):
        cke = ClientKeyExchange(0)

        parser = Parser(bytearray(
            b'\x00\x00\x00'))

        with self.assertRaises(AssertionError):
            cke.parse(parser)

class TestClientMasterKey(unittest.TestCase):
    def test___init__(self):
        cmk = ClientMasterKey()

        self.assertIsNotNone(cmk)
        self.assertEqual(cmk.handshakeType,
                         SSL2HandshakeType.client_master_key)

    def test_create(self):
        cmk = ClientMasterKey()
        cmk = cmk.create(1, bytearray(b'\x02'), bytearray(b'\x03\x04'),
                         bytearray(b'\x05\x06\x07'))

        self.assertEqual(cmk.cipher, 1)
        self.assertEqual(cmk.clear_key, bytearray(b'\x02'))
        self.assertEqual(cmk.encrypted_key, bytearray(b'\x03\x04'))
        self.assertEqual(cmk.key_argument, bytearray(b'\x05\x06\x07'))

    def test_write(self):
        cmk = ClientMasterKey()
        cmk = cmk.create(1, bytearray(b'\x02'), bytearray(b'\x03\x04'),
                         bytearray(b'\x05\x06\x07'))

        self.assertEqual(bytearray(
            b'\x02' +           # message type
            b'\x00\x00\x01' +   # cipher spec
            b'\x00\x01' +       # clear key length
            b'\x00\x02' +       # encrypted key length
            b'\x00\x03' +       # key argument length
            b'\x02' +           # clear key
            b'\x03\x04' +       # encrypted key
            b'\x05\x06\x07'     # key argument
            ), cmk.write())

    def test_parse(self):
        cmk = ClientMasterKey()

        parser = Parser(bytearray(
            # type is handled by handshake protocol
            #b'\x02' +           # message type
            b'\x00\x00\x01' +   # cipher spec
            b'\x00\x01' +       # clear key length
            b'\x00\x02' +       # encrypted key length
            b'\x00\x03' +       # key argument length
            b'\x02' +           # clear key
            b'\x03\x04' +       # encrypted key
            b'\x05\x06\x07'))   # key argument

        cmk = cmk.parse(parser)

        self.assertEqual(cmk.cipher, 1)
        self.assertEqual(cmk.clear_key, bytearray(b'\x02'))
        self.assertEqual(cmk.encrypted_key, bytearray(b'\x03\x04'))
        self.assertEqual(cmk.key_argument, bytearray(b'\x05\x06\x07'))

class TestServerKeyExchange(unittest.TestCase):
    def test___init__(self):
        ske = ServerKeyExchange(CipherSuite.TLS_RSA_WITH_AES_128_CBC_SHA,
                                (3, 1))

        self.assertIsNotNone(ske)
        self.assertEqual(ske.cipherSuite,
                         CipherSuite.TLS_RSA_WITH_AES_128_CBC_SHA)
        self.assertEqual(ske.srp_N, 0)
        self.assertEqual(ske.srp_g, 0)
        self.assertEqual(ske.srp_s, bytearray(0))
        self.assertEqual(ske.srp_B, 0)
        self.assertEqual(ske.dh_p, 0)
        self.assertEqual(ske.dh_g, 0)
        self.assertEqual(ske.dh_Ys, 0)
        self.assertEqual(ske.signature, bytearray(0))
        self.assertEqual(ske.version, (3, 1))

    def test___repr__(self):
        ske = ServerKeyExchange(CipherSuite.TLS_DH_ANON_WITH_AES_128_CBC_SHA,
                                (3, 1))

        self.assertEqual("ServerKeyExchange("
                "cipherSuite=CipherSuite.TLS_DH_ANON_WITH_AES_128_CBC_SHA, "
                "version=(3, 1))",
                repr(ske))

    def test__repr___with_ADH(self):
        ske = ServerKeyExchange(CipherSuite.TLS_DH_ANON_WITH_AES_128_CBC_SHA,
                                (3, 1))

        ske.createDH(dh_p=31,
                     dh_g=2,
                     dh_Ys=16)

        self.assertEqual("ServerKeyExchange("
                "cipherSuite=CipherSuite.TLS_DH_ANON_WITH_AES_128_CBC_SHA, "
                "version=(3, 1), dh_p=31, dh_g=2, dh_Ys=16)",
                repr(ske))

    def test___repr___with_DHE(self):
        ske = ServerKeyExchange(CipherSuite.TLS_DHE_RSA_WITH_AES_128_CBC_SHA256,
                                (3, 3))

        ske.createDH(dh_p=31,
                     dh_g=2,
                     dh_Ys=16)
        ske.signature = bytearray(b'\xff'*4)
        ske.signAlg = SignatureAlgorithm.rsa
        ske.hashAlg = HashAlgorithm.sha384

        self.assertEqual("ServerKeyExchange("
                "cipherSuite=CipherSuite.TLS_DHE_RSA_WITH_AES_128_CBC_SHA256, "
                "version=(3, 3), dh_p=31, dh_g=2, dh_Ys=16, "
                "hashAlg=5, signAlg=1, "
                "signature=bytearray(b'\\xff\\xff\\xff\\xff'))",
                repr(ske))

    def test___repr___with_SRP(self):
        ske = ServerKeyExchange(CipherSuite.TLS_SRP_SHA_WITH_AES_128_CBC_SHA,
                                (3, 3))

        ske.createSRP(srp_N=1,
                      srp_g=2,
                      srp_s=bytearray(3),
                      srp_B=4)

        self.assertEqual("ServerKeyExchange("
                "cipherSuite=CipherSuite.TLS_SRP_SHA_WITH_AES_128_CBC_SHA, "
                "version=(3, 3), "
                "srp_N=1, srp_g=2, "
                "srp_s=bytearray(b'\\x00\\x00\\x00'), srp_B=4)",
                repr(ske))

    def test_createSRP(self):
        ske = ServerKeyExchange(CipherSuite.TLS_SRP_SHA_WITH_AES_128_CBC_SHA,
                                (3, 3))

        ske.createSRP(srp_N=1,
                      srp_g=2,
                      srp_s=bytearray(3),
                      srp_B=4)

        self.assertEqual(ske.write(), bytearray(
            b'\x0c' +               # message type
            b'\x00\x00\x0d' +       # overall length
            b'\x00\x01' +           # N parameter length
            b'\x01' +               # N value
            b'\x00\x01' +           # g parameter length
            b'\x02' +               # g value
            b'\x03' +               # s parameter length
            b'\x00'*3 +             # s value
            b'\x00\x01' +           # B parameter length
            b'\x04'                 # B value
            ))

    def test_createSRP_with_signature(self):
        ske = ServerKeyExchange(
                CipherSuite.TLS_SRP_SHA_RSA_WITH_AES_128_CBC_SHA,
                (3, 1))

        ske.createSRP(srp_N=1,
                      srp_g=2,
                      srp_s=bytearray(3),
                      srp_B=4)
        ske.signature = bytearray(b'\xc0\xff\xee')

        self.assertEqual(ske.write(), bytearray(
            b'\x0c' +               # message type
            b'\x00\x00\x12' +       # overall length
            b'\x00\x01' +           # N parameter length
            b'\x01' +               # N value
            b'\x00\x01' +           # g parameter length
            b'\x02' +               # g value
            b'\x03' +               # s parameter length
            b'\x00'*3 +             # s value
            b'\x00\x01' +           # B parameter length
            b'\x04'                 # B value
            b'\x00\x03' +           # signature length
            b'\xc0\xff\xee'         # signature value
            ))

    def test_createSRP_with_signature_in_TLS_v1_2(self):
        ske = ServerKeyExchange(
                CipherSuite.TLS_SRP_SHA_RSA_WITH_AES_128_CBC_SHA,
                (3, 3))

        ske.createSRP(srp_N=1,
                      srp_g=2,
                      srp_s=bytearray(3),
                      srp_B=4)
        ske.hashAlg = HashAlgorithm.sha512
        ske.signAlg = SignatureAlgorithm.rsa
        ske.signature = bytearray(b'\xc0\xff\xee')

        self.assertEqual(ske.write(), bytearray(
            b'\x0c' +               # message type
            b'\x00\x00\x14' +       # overall length
            b'\x00\x01' +           # N parameter length
            b'\x01' +               # N value
            b'\x00\x01' +           # g parameter length
            b'\x02' +               # g value
            b'\x03' +               # s parameter length
            b'\x00'*3 +             # s value
            b'\x00\x01' +           # B parameter length
            b'\x04' +               # B value
            b'\x06\x01' +           # SHA512+RSA
            b'\x00\x03' +           # signature length
            b'\xc0\xff\xee'         # signature value
            ))

    def test_createDH(self):
        ske = ServerKeyExchange(CipherSuite.TLS_DH_ANON_WITH_AES_128_CBC_SHA,
                                (3, 3))

        ske.createDH(dh_p=31,
                     dh_g=2,
                     dh_Ys=16)

        self.assertEqual(ske.write(), bytearray(
            b'\x0c' +               # message type
            b'\x00\x00\x09' +       # overall length
            b'\x00\x01' +           # p parameter length
            b'\x1f' +               # p value
            b'\x00\x01' +           # g parameter length
            b'\x02' +               # g value
            b'\x00\x01' +           # Ys parameter length
            b'\x10'                 # Ys value
            ))

    def test_createECDH(self):
        ske = ServerKeyExchange(CipherSuite.TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA,
                                (3, 3))

        point = bytearray(b'\x04\x0a\x0a\x0b\x0b')
        ske.createECDH(ECCurveType.named_curve,
                       named_curve=GroupName.secp256r1,
                       point=point)
        ske.hashAlg = HashAlgorithm.sha1
        ske.signAlg = SignatureAlgorithm.rsa
        ske.signature = bytearray(b'\xff'*16)

        self.assertEqual(ske.write(), bytearray(
            b'\x0c'                 # message type - SKE
            b'\x00\x00\x1d'         # overall length
            b'\x03'                 # named_curve
            b'\x00\x17'             # secp256r1
            b'\x05'                 # length of point encoding
            b'\x04\x0a\x0a\x0b\x0b' # point
            b'\x02\x01'             # RSA+SHA1
            b'\x00\x10'             # length of signature
            # signature:
            b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'
            ))

    def test_parse_with_unknown_cipher(self):
        ske = ServerKeyExchange(0, (3, 1))

        parser = Parser(bytearray(
            b'\x00\x00\x03' +
            b'\x00\x01' +
            b'\xff'
            ))

        with self.assertRaises(AssertionError):
            ske.parse(parser)

    def test_parse_with_read_past_message_end(self):
        ske = ServerKeyExchange(\
                CipherSuite.TLS_SRP_SHA_RSA_WITH_AES_128_CBC_SHA,
                (3, 1))

        parser = Parser(bytearray(
            b'\x00\x00\x13' +       # overall length
            b'\x00\x01' +           # N parameter length
            b'\x01' +               # N value
            b'\x00\x01' +           # g parameter length
            b'\x02' +               # g value
            b'\x03' +               # s parameter length
            b'\x00'*3 +             # s value
            b'\x00\x01' +           # B parameter length
            b'\x04' +               # B value
            b'\x00\x06' +           # signature length
            b'\xff'*4))

        with self.assertRaises(SyntaxError):
            ske.parse(parser)

    def test_parse_with_SRP(self):
        ske = ServerKeyExchange(CipherSuite.TLS_SRP_SHA_WITH_AES_128_CBC_SHA,
                                (3, 3))

        parser = Parser(bytearray(
            b'\x00\x00\x0d' +       # overall length
            b'\x00\x01' +           # N parameter length
            b'\x01' +               # N value
            b'\x00\x01' +           # g parameter length
            b'\x02' +               # g value
            b'\x03' +               # s parameter length
            b'\x00'*3 +             # s value
            b'\x00\x01' +           # B parameter length
            b'\x04'                 # B value
            ))

        ske.parse(parser)

        self.assertEqual(ske.srp_N, 1)
        self.assertEqual(ske.srp_g, 2)
        self.assertEqual(ske.srp_s, bytearray(3))
        self.assertEqual(ske.srp_B, 4)

    def test_parser_with_SRP_RSA(self):
        ske = ServerKeyExchange(
                CipherSuite.TLS_SRP_SHA_RSA_WITH_AES_128_CBC_SHA,
                (3, 1))

        parser = Parser(bytearray(
            b'\x00\x00\x12' +       # overall length
            b'\x00\x01' +           # N parameter length
            b'\x01' +               # N value
            b'\x00\x01' +           # g parameter length
            b'\x02' +               # g value
            b'\x03' +               # s parameter length
            b'\x00'*3 +             # s value
            b'\x00\x01' +           # B parameter length
            b'\x04'                 # B value
            b'\x00\x03' +           # signature length
            b'\xc0\xff\xee'         # signature value
            ))

        ske.parse(parser)

        self.assertEqual(ske.srp_N, 1)
        self.assertEqual(ske.srp_g, 2)
        self.assertEqual(ske.srp_s, bytearray(3))
        self.assertEqual(ske.srp_B, 4)
        self.assertEqual(ske.signature, bytearray(b'\xc0\xff\xee'))

    def test_parser_with_SRP_RSA_in_TLS_v1_2(self):
        ske = ServerKeyExchange(
                CipherSuite.TLS_SRP_SHA_RSA_WITH_AES_128_CBC_SHA,
                (3, 3))

        parser = Parser(bytearray(
            b'\x00\x00\x14' +       # overall length
            b'\x00\x01' +           # N parameter length
            b'\x01' +               # N value
            b'\x00\x01' +           # g parameter length
            b'\x02' +               # g value
            b'\x03' +               # s parameter length
            b'\x00'*3 +             # s value
            b'\x00\x01' +           # B parameter length
            b'\x04'                 # B value
            b'\x06\x01' +           # SHA512+RSA
            b'\x00\x03' +           # signature length
            b'\xc0\xff\xee'         # signature value
            ))

        ske.parse(parser)

        self.assertEqual(ske.srp_N, 1)
        self.assertEqual(ske.srp_g, 2)
        self.assertEqual(ske.srp_s, bytearray(3))
        self.assertEqual(ske.srp_B, 4)
        self.assertEqual(ske.signature, bytearray(b'\xc0\xff\xee'))
        self.assertEqual(ske.hashAlg, HashAlgorithm.sha512)
        self.assertEqual(ske.signAlg, SignatureAlgorithm.rsa)

    def test_parser_with_DH(self):
        ske = ServerKeyExchange(CipherSuite.TLS_DH_ANON_WITH_AES_128_CBC_SHA,
                                (3, 3))

        parser = Parser(bytearray(
            b'\x00\x00\x09' +       # overall length
            b'\x00\x01' +           # p parameter length
            b'\x1f' +               # p value
            b'\x00\x01' +           # g parameter length
            b'\x02' +               # g value
            b'\x00\x01' +           # Ys parameter length
            b'\x10'                 # Ys value
            ))

        ske.parse(parser)

        self.assertEqual(ske.dh_p, 31)
        self.assertEqual(ske.dh_g, 2)
        self.assertEqual(ske.dh_Ys, 16)

    def test_parser_with_ECDH(self):
        ske = ServerKeyExchange(CipherSuite.TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA,
                                (3, 3))

        parser = Parser(bytearray(
            b'\x00\x00\x1d'         # overall length
            b'\x03'                 # named_curve
            b'\x00\x17'             # secp256r1
            b'\x05'                 # length of point encoding
            b'\x04\x0a\x0a\x0b\x0b' # point
            b'\x02\x01'             # RSA+SHA1
            b'\x00\x10'             # length of signature
            # signature:
            b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'
            ))

        ske.parse(parser)

        self.assertEqual(ske.curve_type, ECCurveType.named_curve)
        self.assertEqual(ske.named_curve, GroupName.secp256r1)
        self.assertEqual(ske.ecdh_Ys, bytearray(b'\x04\x0a\x0a\x0b\x0b'))
        self.assertEqual(ske.signature, bytearray(b'\xff'*16))

    def test_hash(self):
        ske = ServerKeyExchange(
                CipherSuite.TLS_SRP_SHA_RSA_WITH_AES_128_CBC_SHA,
                (3, 1))

        ske.createSRP(srp_N=1,
                      srp_g=2,
                      srp_s=bytearray(3),
                      srp_B=4)

        hash1 = ske.hash(bytearray(32), bytearray(32))

        self.assertEqual(hash1, bytearray(
            b'\xcb\xe6\xd3=\x8b$\xff\x97e&\xb2\x89\x1dA\xab>' +
            b'\x8e?YW\xcd\xad\xc6\x83\x91\x1d.fe,\x17y' +
            b'=\xc4T\x89'))

    def test_hash_with_invalid_ciphersuite(self):
        ske = ServerKeyExchange(0, (3, 1))

        with self.assertRaises(AssertionError):
            ske.hash(bytearray(32), bytearray(32))

    def test_hash_with_sha1_hash_algorithm_for_TLS_v1_2(self):
        ske = ServerKeyExchange(
                CipherSuite.TLS_SRP_SHA_RSA_WITH_AES_128_CBC_SHA,
                (3, 3))

        ske.createSRP(srp_N=1,
                      srp_g=2,
                      srp_s=bytearray(3),
                      srp_B=4)
        ske.hashAlg = HashAlgorithm.sha1

        hash1 = ske.hash(bytearray(32), bytearray(32))

        self.assertEqual(hash1, bytearray(
            b'\x8e?YW\xcd\xad\xc6\x83\x91\x1d.fe,\x17y=\xc4T\x89'
            ))

    def test_hash_with_invalid_hash_algorithm(self):
       ske = ServerKeyExchange(
               CipherSuite.TLS_DHE_RSA_WITH_AES_128_CBC_SHA,
               (3, 3))

       ske.createDH(1, 2, 3)
       ske.hashAlg = 300

       with self.assertRaises(AssertionError):
           ske.hash(bytearray(32), bytearray(32))

class TestCertificateRequest(unittest.TestCase):
    def test___init__(self):
        cr = CertificateRequest((3, 0))

        self.assertIsNotNone(cr)
        self.assertEqual(cr.version, (3, 0))
        self.assertEqual(cr.certificate_types, [])
        self.assertEqual(cr.certificate_authorities, [])
        self.assertEqual(cr.supported_signature_algs, [])

    def test_create(self):
        cr = CertificateRequest((3, 0))
        cr.create([ClientCertificateType.rsa_sign], [])

        self.assertEqual(cr.certificate_authorities, [])
        self.assertEqual(cr.certificate_types, [ClientCertificateType.rsa_sign])

        # XXX type change from array!
        self.assertEqual(cr.supported_signature_algs, tuple())

    def test_parse(self):
        cr = CertificateRequest((3, 1))

        parser = Parser(bytearray(
            b'\x00\x00\x04' +       # overall length
            b'\x01' +               # length of certificate types
            b'\x01' +               # type rsa_sign
            b'\x00\x00'             # length of CA list
            ))

        cr.parse(parser)

        self.assertEqual(cr.certificate_authorities, [])
        self.assertEqual(cr.certificate_types,
                         [ClientCertificateType.rsa_sign])

    def test_parse_with_TLSv1_2(self):
        cr = CertificateRequest((3, 3))

        parser = Parser(bytearray(
            b'\x00\x00\x1a' +       # overall length
            b'\x01' +               # length of certificate types
            b'\x01' +               # type rsa_sign
            b'\x00\x0a' +           # length of signature types
            b'\x06\x01' +           # SHA512+RSA
            b'\x05\x01' +           # SHA384+RSA
            b'\x04\x01' +           # SHA256+RSA
            b'\x03\x01' +           # SHA224+RSA
            b'\x02\x01' +           # SHA1+RSA
            b'\x00\x0a' +           # length of CA list
            b'\x00'*10              # opaque data type
            ))

        cr.parse(parser)

        self.assertEqual(cr.certificate_types, [ClientCertificateType.rsa_sign])
        self.assertEqual(cr.supported_signature_algs,
                         [(HashAlgorithm.sha512, SignatureAlgorithm.rsa),
                          (HashAlgorithm.sha384, SignatureAlgorithm.rsa),
                          (HashAlgorithm.sha256, SignatureAlgorithm.rsa),
                          (HashAlgorithm.sha224, SignatureAlgorithm.rsa),
                          (HashAlgorithm.sha1, SignatureAlgorithm.rsa)])

        self.assertEqual(len(cr.certificate_authorities), 5)
        for cert_auth in cr.certificate_authorities:
            self.assertEqual(cert_auth, bytearray(0))

    def test_write(self):
        cr = CertificateRequest((3, 1))
        cr.create([ClientCertificateType.rsa_sign], [bytearray(b'\xff\xff')])

        self.assertEqual(cr.write(), bytearray(
            b'\x0d' +               # type
            b'\x00\x00\x08' +       # overall length
            b'\x01' +               # length of certificate types
            b'\x01' +               # type rsa sign
            b'\x00\x04' +           # length of CA list
            b'\x00\x02' +           # length of entry
            b'\xff\xff'             # opaque
            ))

    def test_write_in_TLS_v1_2(self):
        cr = CertificateRequest((3, 3))
        self.assertEqual(cr.version, (3, 3))
        cr.create([ClientCertificateType.rsa_sign],
                  [],
                  [(6, 1), (4, 1), (2, 1)])

        self.assertEqual(cr.write(), bytearray(
            b'\x0d' +               # type
            b'\x00\x00\x0c' +       # overall length
            b'\x01' +               # length of certificate types
            b'\x01' +               # type rsa sign
            b'\x00\x06' +           # signature types
            b'\x06\x01' +           # SHA512+RSA
            b'\x04\x01' +           # SHA256+RSA
            b'\x02\x01' +           # SHA1+RSA
            b'\x00\x00'             # length of CA list
            ))

class TestCertificateVerify(unittest.TestCase):
    def test___init__(self):
        cv = CertificateVerify((3, 1))

        self.assertIsNotNone(cv)
        self.assertEqual(cv.signature, bytearray(0))

    def test_create(self):
        cv = CertificateVerify((3, 1))

        cv.create(bytearray(b'\xf0\x0f'))

        self.assertEqual(cv.signature, bytearray(b'\xf0\x0f'))

    def test_write(self):
        cv = CertificateVerify((3, 1))

        cv.create(bytearray(b'\xf0\x0f'))

        self.assertEqual(cv.write(), bytearray(
            b'\x0f' +               # type
            b'\x00\x00\x04' +       # overall length
            b'\x00\x02' +           # length of signature
            b'\xf0\x0f'             # signature
            ))

    def test_parse(self):
        cv = CertificateVerify((3, 1))

        parser = Parser(bytearray(
            b'\x00\x00\x04' +       # length
            b'\x00\x02' +           # length of signature
            b'\xf0\x0f'             # signature
            ))

        cv.parse(parser)

        self.assertEqual(cv.signature, bytearray(b'\xf0\x0f'))

    def test_parse_with_TLSv1_2(self):
        cv = CertificateVerify((3, 3))

        parser = Parser(bytearray(
            b'\x00\x00\x06' +       # length
            b'\x02\x01' +           # SHA1 + RSA
            b'\x00\x02' +           # length of signature
            b'\xab\xcd'             # signature
            ))

        cv.parse(parser)

        self.assertEqual(cv.signature, bytearray(b'\xab\xcd'))
        self.assertEqual(cv.signatureAlgorithm, (HashAlgorithm.sha1,
                                                 SignatureAlgorithm.rsa))

    def test_write_with_TLSv1_2(self):
        cv = CertificateVerify((3, 3))

        cv.create(bytearray(b'\xff\xba'), (HashAlgorithm.sha512,
                                           SignatureAlgorithm.rsa))

        self.assertEqual(cv.write(), bytearray(
            b'\x0f' +               # type
            b'\x00\x00\x06' +       # overall length
            b'\x06\x01' +           # SHA512+RSA
            b'\x00\x02' +           # signature length
            b'\xff\xba'             # signature
            ))

class TestServerHelloDone(unittest.TestCase):
    def test___init__(self):
        shd = ServerHelloDone()

        self.assertIsNotNone(shd)

    def test___repr__(self):
        shd = ServerHelloDone()

        self.assertEqual("ServerHelloDone()", repr(shd))

class TestClientFinished(unittest.TestCase):
    def test___init__(self):
        fin = ClientFinished()

        self.assertIsNotNone(fin)
        self.assertEqual(fin.handshakeType, SSL2HandshakeType.client_finished)

    def test_create(self):
        fin = ClientFinished()
        fin.create(bytearray(b'\xc0\xfe'))

        self.assertEqual(fin.verify_data, bytearray(b'\xc0\xfe'))

    def test_write(self):
        fin = ClientFinished()
        fin = fin.create(bytearray(b'\xc0\xfe'))

        self.assertEqual(bytearray(
            b'\x03' +   # message type
            b'\xc0\xfe' # message payload
            ), fin.write())

    def test_parse(self):
        parser = Parser(bytearray(
            # type is handled by higher protocol level
            b'\xc0\xfe'))

        fin = ClientFinished()
        fin = fin.parse(parser)

        self.assertEqual(fin.verify_data, bytearray(b'\xc0\xfe'))
        self.assertEqual(fin.handshakeType, SSL2HandshakeType.client_finished)

class TestServerFinished(unittest.TestCase):
    def test___init__(self):
        fin = ServerFinished()

        self.assertIsNotNone(fin)
        self.assertEqual(fin.handshakeType, SSL2HandshakeType.server_finished)

    def test_create(self):
        fin = ServerFinished()
        fin = fin.create(bytearray(b'\xc0\xfe'))

        self.assertEqual(fin.verify_data, bytearray(b'\xc0\xfe'))

    def test_write(self):
        fin = ServerFinished()
        fin.create(bytearray(b'\xc0\xfe'))

        self.assertEqual(bytearray(
            b'\x06' +   # message type
            b'\xc0\xfe' # message payload
            ), fin.write())

    def test_parse(self):
        parser = Parser(bytearray(
            # type is handled by higher protocol level
            b'\xc0\xfe'))

        fin = ServerFinished()
        fin = fin.parse(parser)

        self.assertEqual(fin.verify_data, bytearray(b'\xc0\xfe'))
        self.assertEqual(fin.handshakeType, SSL2HandshakeType.server_finished)

if __name__ == '__main__':
    unittest.main()
