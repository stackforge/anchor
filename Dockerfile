FROM hyakuhei/anchor:base
MAINTAINER Robert Clark <hyakuhei@gmail.com>
WORKDIR /root
RUN git clone git://git.openstack.org/openstack/anchor
WORKDIR /root/anchor
RUN pip install .
RUN cp config.py /home/anchor/
RUN cp config.json /home/anchor/
RUN chown anchor:anchor /home/anchor/config.py
RUN chown anchor:anchor /home/anchor/config.json
RUN su - anchor
WORKDIR /home/anchor
RUN mkdir CA
RUN openssl req -out CA/root-ca.crt \
  -keyout CA/root-ca-unwrapped.key \
  -newkey rsa:4096 \
  -subj "/CN=Anchor Test CA" \
  -nodes \
  -x509 \
  -days 365
RUN chmod 0400 CA/root-ca-unwrapped.key
