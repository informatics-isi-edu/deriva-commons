host=tutorial.derivacloud.org
isrd_systems="https://auth.globus.org/3938e0d0-ed35-11e5-8641-22000ab4b42b"

deriva-hatrac-cli --host $host mkdir --parents /hatrac/resources
deriva-hatrac-cli --host $host setacl /hatrac/resources owner $isrd_systems
deriva-hatrac-cli --host $host setacl /hatrac/resources subtree-owner $isrd_systems
deriva-hatrac-cli --host $host setacl /hatrac/resources subtree-read "*"

