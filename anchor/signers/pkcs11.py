from cryptography.hazmat import backends as cio_backends
from cryptography.hazmat.primitives import hashes
from pyasn1.codec.der import encoder
from pyasn1.type import univ as asn1_univ
from pyasn1_modules import rfc2315

from anchor import errors
from anchor import signers
from anchor import util


def conf_validator(name, ca_conf):
    # mandatory CA settings
    ca_config_requirements = ["cert_path", "output_path", "signing_hash",
                              "valid_hours", "slot", "pin", "key_id",
                              "pkcs11_path"]

    for requirement in ca_config_requirements:
        if requirement not in ca_conf.keys():
            raise errors.ConfigValidationException(
                "CA config missing: %s (for signing CA %s)" % (requirement,
                                                               name))

    # all are specified, check the CA certificate and key are readable with
    # sane permissions
    util.check_file_exists(ca_conf['cert_path'])
    util.check_file_exists(ca_conf['pkcs11_path'])


def make_signer(key_id, slot, pin, pkcs11_path, md):
    HASH_OIDS = {
        'SHA256': asn1_univ.ObjectIdentifier('2.16.840.1.101.3.4.2.1'),
        'SHA384': asn1_univ.ObjectIdentifier('2.16.840.1.101.3.4.2.2'),
        'SHA512': asn1_univ.ObjectIdentifier('2.16.840.1.101.3.4.2.3'),
        'SHA224': asn1_univ.ObjectIdentifier('2.16.840.1.101.3.4.2.4'),
    }

    import PyKCS11
    l = PyKCS11.PyKCS11Lib()
    l.load(pkcs11_path)
    s = l.openSession(slot)
    s.login(pin)
    keys = s.findObjects((
        (PyKCS11.CKA_CLASS, PyKCS11.CKO_PRIVATE_KEY),
        (PyKCS11.CKA_KEY_TYPE, PyKCS11.CKK_RSA),
        (PyKCS11.CKA_SIGN, True),
        (PyKCS11.CKA_ID, key_id),
        ))
    if not keys:
        raise signers.SigningError("Cannot find the requested key")
    key = keys[0]
    cio_hash = getattr(hashes, md)
    h = hashes.Hash(cio_hash(), cio_backends.default_backend())

    def pkcs11_signer(to_sign):
        l.getInfo  # just to keep it in scope, it's a NOOP
        h.update(to_sign)
        di = rfc2315.DigestInfo()
        di['digestAlgorithm'] = None
        di['digestAlgorithm'][0] = HASH_OIDS[md]
        di['digest'] = h.finalize()
        signature = bytes(s.sign(key, encoder.encode(di),
                                 PyKCS11.MechanismRSAPKCS1))
        s.logout()
        return signature

    return pkcs11_signer


@signers.config_validator(conf_validator)
def sign(csr, ca_conf):
    slot = ca_conf['slot']
    pin = ca_conf['pin']
    pkcs11_path = ca_conf['pkcs11_path']
    key_id = [int(ca_conf['key_id'][i:i+2], 16) for
              i in range(0, len(ca_conf['key_id']), 2)]
    signing_hash = ca_conf['signing_hash'].upper()

    signer = make_signer(key_id, slot, pin, pkcs11_path, signing_hash)
    return signers.sign_generic(csr, ca_conf, 'RSA', signer)
