
openssl genrsa -out server.key 2096
openssl req -new -key server.key -out - -config openssl.cnf -batch | openssl x509 -req -days 365 -in - -signkey server.key -out server.crt
