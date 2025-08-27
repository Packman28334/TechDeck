
import socket
import ifaddr
from uuid import uuid4
from zeroconf import Zeroconf, ServiceBrowser, ServiceListener, ServiceInfo
from websockets.sync.client import connect, ClientConnection

from config import PREFERRED_ADAPTER

# https://forums.balena.io/t/discover-avahi-zeroconf-services-inside-container/48665/4

class Peer:
    def __init__(self, ip_address: str, port: int, uuid: str):
        self.ip_address: str = ip_address
        self.port: int = port
        self.uuid: str = uuid

        self.websocket: ClientConnection = connect(f"ws://{self.ip_address}:{self.port}/api/websocket")
        self.websocket.send("cues")

class TechDeckServiceListener(ServiceListener):
    def __init__(self, manager: "P2PNetworkManager"):
        self.network_manager: P2PNetworkManager = manager

    def parse_info(self, info: ServiceInfo):
        return {"ip_address": socket.inet_ntoa(info.addresses[0]), "port": info.port, "uuid": info.properties[b"uuid"].decode("utf-8")}

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        pass

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = self.parse_info(zc.get_service_info(type_, name))
        for peer in self.network_manager.peers:
            if peer.ip_address == info["ip_address"] and peer.port == info["port"] and peer.uuid == info["uuid"]:
                self.network_manager.peers.remove(peer)

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = self.parse_info(zc.get_service_info(type_, name))
        self.network_manager.peers.append(Peer(**info))

class P2PNetworkManager:
    def __init__(self):
        self.uuid = str(uuid4())

        self.peers: list[Peer] = []

        self.service_info: ServiceInfo = ServiceInfo(
            "_techdeck._tcp.local.",
            "Tech Deck Node._techdeck._tcp.local.",
            port=8383,
            addresses=[socket.inet_aton(ip) for ip in self.find_ip_addresses()],
            properties={"uuid": self.uuid}
        )

        self.zeroconf: Zeroconf = Zeroconf()
        self.listener: TechDeckServiceListener = TechDeckServiceListener(self)
        self.browser: ServiceBrowser = ServiceBrowser(self.zeroconf, "_techdeck._tcp.local.", self.listener)
        self.zeroconf.register_service(self.service_info)

    def find_ip_addresses(self) -> list[str]:
        adapters: list[ifaddr.Adapter] = ifaddr.get_adapters()
        for adapter in adapters: # try to find preferred adapter
            if adapter.name == PREFERRED_ADAPTER:
                ips = [ip.ip for ip in adapter.ips if isinstance(ip.ip, str) and ip.is_IPv4]
                ips.extend([ip.ip[0] for ip in adapter.ips if isinstance(ip.ip, tuple) and ip.is_IPv4])
                return ips
        for adapter in adapters: # if preferred adapter isn't found, look for ethernet
            if "eth" in adapter.name or "en" in adapter.name:
                ips = [ip.ip for ip in adapter.ips if isinstance(ip.ip, str) and ip.is_IPv4]
                ips.extend([ip.ip[0] for ip in adapter.ips if isinstance(ip.ip, tuple) and ip.is_IPv4])
                return ips
        for adapter in adapters: # if no ethernet adapter is found, look for any adapter that's not loopback
            if adapter.name != "lo":
                ips = [ip.ip for ip in adapter.ips if isinstance(ip.ip, str) and ip.is_IPv4]
                ips.extend([ip.ip[0] for ip in adapter.ips if isinstance(ip.ip, tuple) and ip.is_IPv4])
                return ips
            raise Exception("No network adapter found.") # if no external network adapter is found