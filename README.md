# in-toto openSUSE demo
In this demo, we will use in-toto to secure a software supply chain for OpenSUSE. Bob is a developer for a project, Carl tests the software before packaging, and Alice oversees the project. So, using in-toto's names for the parties, Alice is the project owner — she creates and signs the software supply chain layout with her private key — and Bob and Carl are project functionaries — they carry out the steps of the software supply chain as defined in the layout.

For the sake of demonstrating in-toto, we will have you run all parts of the software supply chain. That is, you will perform the commands on behalf of Alice, Bob and Carl as well as the client who verifies the final product.

# Setup
Install docker
https://docs.docker.com/engine/installation/

Pull and run the docker image for this demo
```shell
docker pull intoto/opensuse-demo
docker run --privileged -i -t intoto/opensuse-demo:latest
```

This demo requires an account on opensuse build service. If you don't have an account you could either sign up for one easily to continue. Or you could try our [offline demo](Offline-demo.md).

Signup for an account on opensuse build service at
https://build.opensuse.org/ICSLogin/

Set your username as environment variable so that you can copy paste the demo commands
```shell
username=<username>
```

# Change into the demo directory and you are ready to start
```shell
cd demo-opensuse/
```

Inside the demo-opensuse directory you will find four directories: `owner_alice`,
`functionary_bob`, `functionary_carl` and `final_product`. Alice, Bob and Carl
already have RSA keys in each of their directories. This is what you see:
```shell
tree  # If you don't have tree, try 'find .' instead
# the tree command gives you the following output
# ├── Dockerfile
# ├── Offline-demo.md
# ├── README.md
# ├── final_product
# ├── functionary_bob
# │   ├── bob
# │   └── bob.pub
# ├── functionary_carl
# │   ├── carl
# │   └── carl.pub
# └── owner_alice
#     ├── alice
#     ├── alice.pub
#     ├── create_layout.py
#     ├── create_layout_offline.py
#     └── verify-signature.sh
```

### Define software supply chain layout (Alice)
First, we will create a new package on openSUSE's open build server. Next we will define the software supply chain layout. To simplify this process, we provide a script that generates a simple layout for the purpose of the demo.

Three people participate in this software supply chain, Alice, Bob and Carl. Alice is the project owner that creates the root layout. Bob is the developer, and he clones the project's repo and performs some pre-packaging edits. Carl then tests the sources and verifies that its fit to ship. Carl then commits the package which triggers open build server to build the RPMs.

Create and sign the software supply chain layout on behalf of Alice
```shell
cd owner_alice/
python create_layout.py
```
The script will create a layout, add Bob's and Carl's public keys (fetched from
their directories), sign it with Alice's private key and dump it to `root.layout`.
In `root.layout`, you will find that (besides the signature and other information)
there are five steps, `setup-project`, `clone`, `update-changelog`, `test` and
`package`, that the functionaries Bob and Carl, identified by their public keys,
are authorized to perform.

### Setup project (Bob)
Execute the following commands to change to Bob's directory and perform the step.

Checkout your default project. You will be prompted for your username and password which is stored in `~/.oscrc` as plain text.
```shell
cd ../functionary_bob
osc checkout home:$username
```

Specify the build target
```shell
osc meta prj -e home:$username
```

This will open a template xml in your favourite editor. For this demo uncomment the first one.
```shell
<repository name="openSUSE_Factory">
   <path project="openSUSE:Factory" repository="standard" />
   <arch>x86_64</arch>
   <arch>i586</arch>
 </repository>
```

Create a new package named connman in your home project
```shell
cd home:$username
osc meta pkg -e home:$username connman
```

osc will open a template xml, fill out name, title, description.
You can see your package here https://build.opensuse.org/package/show/home:$username/connman (replace $username in url with actual username).

Update the local copy from the central server. you will get a new connman directory
```shell
osc up
```

Now we will create a link file as a proof that Bob created the meta files for the project and package.
The link will contain the hashes of both the meta files so in the future if something goes wrong we
can figure out if Bob made a mistake or someone else changed the file.
```shell
in-toto-record --step-name setup-project --key ../bob start
osc meta prj home:$username >> project.meta
osc meta pkg home:$username connman >> package.meta
in-toto-record --step-name setup-project --key ../bob stop --products project.meta package.meta
```

### Clone project source code (Bob)
Now, we will take the role of the functionary Bob and perform the step
`clone` on his behalf, that is we use in-toto to clone the project repo from GitHub and
record metadata for what we do.
```shell
in-toto-record --step-name clone --key ../bob start
git clone file:///home/connman/.git/ connman-src
mv connman-src/* connman/
rm -r connman-src
in-toto-record --step-name clone --key ../bob stop --products connman/_service connman/connman-1.30.tar.gz connman/connman-1.30.tar.sign connman/connman-rpmlintrc connman/connman.changes connman/connman.keyring connman/connman.spec
```

Here is what happens behind the scenes:
 1. In-toto wraps the work of Bob,
 1. hashes the contents of the source code,
 1. adds the hash together with other information to a metadata file,
 1. signs the metadata with Bob's private key, and
 1. stores everything to `clone.[Bob's keyid].link`.

### Update-changelog (Bob)
Before Carl tests and commits the source code, Bob will update the changelog saved in `connman.changes`. He does this using the `in-toto-record` command, which produces the same link metadata file as above but does not require Bob to wrap his action in a single command. So first Bob records the state of the files he will modify:
```shell
in-toto-record --step-name update-changelog --key ../bob start --materials connman/connman.changes
```

Then Bob uses an editor of his choice to update the changelog e.g.:
```shell
vim connman/connman.changes
```

And finally he records the state of files after the modification and produces
a link metadata file called `update-changelog.[Bob's keyid].link`.
```shell
in-toto-record --step-name update-changelog --key ../bob stop --products connman/connman.changes
```

Bob has done his work and can send over the sources to Carl.
```shell
cd ..
mv home:$username/ ../functionary_carl/
```

### Test (Carl)
Now, we will perform Carl’s `test` step by executing the following commands to change to Carl's directory.

```shell
cd ../functionary_carl/home:$username/
in-toto-run --step-name test --key ../carl -- osc build openSUSE_Factory x86_64 connman/connman.spec
```
It will prompt you to trust the gpg key for `openSUSE:Factory`, Choose 1
```shell
Would you like to ...
0 - quit (default)
1 - always trust packages from 'openSUSE:Factory'
2 - trust packages just this time
? 1
```

This will create a step link metadata file, called `test.[Carl's keyid].link`.

### Package (Carl)
Now we will execute the package step.
```shell
in-toto-record --step-name package --key ../carl start --materials connman/*
```

Commit changes, this would trigger an automatic build on open build server.
```shell
cd connman
osc add *
osc commit
```

Download the build RPM from server
```shell
cd ../
wget http://download.opensuse.org/repositories/home:/$username/openSUSE_Factory/src/connman-1.30-1.1.src.rpm
```

And finally he records the state of files after the modification and produces
a link metadata file, called `package.[Carl's keyid].link`.
```shell
in-toto-record --step-name package --key ../carl stop --products connman-1.30-1.1.src.rpm
```

### Verify final product (client)
Let's first copy all relevant files into the `final_product` that is
our software package `<srcpackage.rpm>` and the related metadata files `root.layout`,
`clone.[Bob's keyid].link`, `update-changelog.[Bob's keyid].link`, `test.[Carl's keyid].link` and `package.[Carl's keyid].link`:
```shell
cd ../../
cp owner_alice/root.layout owner_alice/verify-signature.sh functionary_carl/home:$username/setup-project.0c6c50a1.link functionary_carl/home:$username/clone.0c6c50a1.link functionary_carl/home:$username/update-changelog.0c6c50a1.link functionary_carl/home:$username/test.c1ae1e51.link functionary_carl/home:$username/package.c1ae1e51.link functionary_carl/home:$username/connman-1.30-1.1.src.rpm final_product/
```
And now run verification on behalf of the client:
```shell
cd final_product
# Fetch Alice's public key from a trusted source to verify the layout signature
# Note: The functionary public keys are fetched from the layout
cp ../owner_alice/alice.pub .
in-toto-verify --layout root.layout --layout-key alice.pub
```

This command will verify that
 1. the layout has not expired,
 2. was signed with Alice’s private key, and that according to the definitions in the layout
 3. each step was performed and signed by the authorized functionary
 4. the recorded materials and products follow the artifact rules and
 5. the inspection `unpack` finds what it expects.
 6. the inspection `verify-signature` checks that the signature for connman tarball is correct.

From it, you will see the meaningful output `PASSING` and a return value
of `0`, that indicates verification was successful:
```shell
echo $?
# should output 0
```

### Wrapping up
Congratulations! You have completed the in-toto opensuse demo!

Your package can now be installed in openSUSE systems. Instructions to do so can be found here https://software.opensuse.org//download.html?project=home%3A$username&package=connman (replace $username in url with actual username). If in-toto was integrated with Open Build System and `zypper`, testing and packaging step would be done on Open Build System. In-toto meta data would be hosted on http://download.opensuse.org/repositories/home:/$username/ (replace $username in url with actual username) along with the build RPMs. `zypper` would download and verify in-toto metadata along with the downloaded RPMs.

This exercise shows a very simple case in how in-toto can protect the different steps within the software supply chain. More complex software supply chains that contain more steps can be created in a similar way. You can read more about what in-toto protects against and how to use it on [in-toto's Github page](https://in-toto.github.io/).

### Clean up
We will delete the connman package from your home project now.
```shell
cd ../functionary_carl/home:$username
osc delete connman
osc ci -m "remove package"
```
