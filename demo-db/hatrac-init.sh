host=tutorial.derivacloud.org
isrd_systems="https://auth.globus.org/3938e0d0-ed35-11e5-8641-22000ab4b42b"
tutorial_creator="https://auth.globus.org/ed41a320-8345-11ea-b546-0a875b138121"
tutorial_writer="https://auth.globus.org/3f4e09da-8346-11ea-8512-0e98982705c1"

deriva-hatrac-cli --host $host mkdir --parents /hatrac/resources
deriva-hatrac-cli --host $host setacl /hatrac/resources owner $isrd_systems
deriva-hatrac-cli --host $host setacl /hatrac/resources subtree-owner $isrd_systems
deriva-hatrac-cli --host $host setacl /hatrac/resources subtree-read "*"

deriva-hatrac-cli --host $host mkdir --parents /hatrac/sandbox
deriva-hatrac-cli --host $host setacl /hatrac/sandbox owner $isrd_systems
deriva-hatrac-cli --host $host setacl /hatrac/sandbox subtree-owner $isrd_systems $tutorial_creator
deriva-hatrac-cli --host $host setacl /hatrac/sandbox subtree-update $tutorial_writer
deriva-hatrac-cli --host $host setacl /hatrac/sandbox subtree-read "*"
