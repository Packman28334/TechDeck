
# Tech Deck Networking Architecture

## Hastily assembled and informal, just to allow future myself and others with an existing partial understanding of the project to understand the networking architecture a little more.

Tech Deck is made up of interconnected backends, with each having an associated frontend.

Every backend has a SocketIO server running, and has a SocketIO client connected to every detected backend peer. Every frontend has only one SocketIO client running (connected to it's local backend) and no server.

Inter-backend communication is structured as client-to-server. If Backend A wants to send a message to Backend B, Backend A's client connected to Backend B sends the message to Backend B's server.

Frontend-to-backend communications are structured as client-to-server as well. If Frontend A wants to send a message to Backend A, Frontend A's client will send a message to Backend A's server.

Backend-to-frontend communications are structured as server-to-client. If Backend A wants to send a message to Frontend A, Backend A's server will broadcast a message which will be recieved by Frontend A's client.

Inter-backend communication will never use server-to-client. Any messages broadcast by Backend A's server will be completely ignored by the clients of all other backends, and will only be acknowledged by Frontend A.