from securesystemslib import interface
from in_toto.models.layout import Layout
from in_toto.models.metadata import Metablock

def main():
  # Load Alice's private key to later sign the layout
  key_alice = interface.import_rsa_privatekey_from_file("alice")
  # Fetch and load Bob's and Carl's public keys
  # to specify that they are authorized to perform certain step in the layout
  key_bob = interface.import_rsa_publickey_from_file("../functionary_bob/bob.pub")
  key_carl = interface.import_rsa_publickey_from_file("../functionary_carl/carl.pub")

  layout = Layout.read({
      "_type": "layout",
      "keys": {
          key_bob["keyid"]: key_bob,
          key_carl["keyid"]: key_carl,
      },
      "steps": [{
          "name": "setup-project",
          "expected_materials": [],
          "expected_products": [["CREATE", "project.meta"],
              ["CREATE", "package.meta"]],
          "pubkeys": [key_bob["keyid"]],
          "expected_command": [],
          "threshold": 1,
        },{
          "name": "clone",
          "expected_materials": [],
          "expected_products": [["CREATE", "connman/_service"],
              ["CREATE", "connman/connman-1.30.tar.gz"],
              ["CREATE", "connman/connman-1.30.tar.sign"],
              ["CREATE", "connman/connman-rpmlintrc"],
              ["CREATE", "connman/connman.changes"],
              ["CREATE", "connman/connman.keyring"],
              ["CREATE", "connman/connman.spec"]],
          "pubkeys": [key_bob["keyid"]],
          "expected_command": [],
          "threshold": 1,
        },{
          "name": "update-changelog",
          "expected_materials": [["MATCH", "connman/connman.changes", "WITH", "PRODUCTS", "FROM", "clone"]],
          "expected_products": [["ALLOW", "connman/connman.changes"]],
          "pubkeys": [key_bob["keyid"]],
          "expected_command": [],
          "threshold": 1,
        },{
          "name": "test",
          "expected_materials": [],
          "expected_products": [],
          "pubkeys": [key_carl["keyid"]],
          "expected_command": [
              "osc",
              "build",
              "--clean",
              "--trust-all-projects",
              "openSUSE_Tumbleweed",
              "x86_64",
          ],
          "threshold": 1,
        },{
          "name": "package",
          "expected_materials": [
              ["MATCH", "connman/_service", "WITH", "PRODUCTS", "FROM", "clone"],
              ["MATCH", "connman/connman-1.30.tar.gz", "WITH", "PRODUCTS", "FROM", "clone"],
              ["MATCH", "connman/connman-1.30.tar.sign", "WITH", "PRODUCTS", "FROM", "clone"],
              ["MATCH", "connman/connman-rpmlintrc", "WITH", "PRODUCTS", "FROM", "clone"],
              ["MATCH", "connman/connman.changes", "WITH", "PRODUCTS", "FROM", "update-changelog"],
              ["MATCH", "connman/connman.keyring", "WITH", "PRODUCTS", "FROM", "clone"],
              ["MATCH", "connman/connman.spec", "WITH", "PRODUCTS", "FROM", "clone"],
          ],
          "expected_products": [
              ["CREATE", "connman-1.30-1.1.src.rpm"],
          ],
          "pubkeys": [key_carl["keyid"]],
          "expected_command": [],
          "threshold": 1,
        }],
      "inspect": [{
          "name": "unpack",
          "expected_materials": [
              ["MATCH", "connman-1.30-1.1.src.rpm", "WITH", "PRODUCTS", "FROM", "package"],
              # FIXME: If the routine running inspections would gather the
              # materials/products to record from the rules we wouldn't have to
              # ALLOW other files that we aren't interested in.
              ["ALLOW", ".keep"],
              ["ALLOW", "alice.pub"],
              ["ALLOW", "verify-signature.sh"],
              ["ALLOW", "root.layout"],
          ],
          "expected_products": [
              ["MATCH", "connman-1.30-1.1.src.rpm", "WITH", "PRODUCTS", "FROM", "package"],
              ["MATCH", "connman-1.30.tar.gz", "WITH", "PRODUCTS", "IN", "connman", "FROM", "clone"],
              ["MATCH", "_service", "WITH", "PRODUCTS", "IN", "connman", "FROM", "clone"],
              ["MATCH", "connman-1.30.tar.sign", "WITH", "PRODUCTS", "IN", "connman", "FROM", "clone"],
              ["MATCH", "connman-rpmlintrc", "WITH", "PRODUCTS", "IN", "connman", "FROM", "clone"],
              ["MATCH", "connman.changes", "WITH", "PRODUCTS", "IN", "connman", "FROM", "update-changelog"],
              ["MATCH", "connman.keyring", "WITH", "PRODUCTS", "IN", "connman", "FROM", "clone"],
              # FIXME: hash doesn't match for this file because connman.spec in
              # rpm has changelog appended to it and release number incremented.
              ["ALLOW", "connman.spec"],
              ["ALLOW", ".keep"],
              ["ALLOW", "alice.pub"],
              ["ALLOW", "verify-signature.sh"],
              ["ALLOW", "root.layout"],
          ],
          "run": [
              "unrpm",
              "connman-1.30-1.1.src.rpm",
          ]
        },{
          "name": "verify-signature",
          "expected_materials": [["ALLOW", "*"]],
          "expected_products": [["ALLOW", "*"]],
          "run": [
              "./verify-signature.sh",
          ],
        }],
  })

  metadata = Metablock(signed=layout)

  # Sign and dump layout to "root.layout"
  metadata.sign(key_alice)
  metadata.dump("root.layout")
  print('Created demo in-toto layout as "root.layout".')

if __name__ == '__main__':
  main()
