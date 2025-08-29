
import socket
import ifaddr
import time
from uuid import uuid4
from zeroconf import Zeroconf, ServiceBrowser, ServiceListener, ServiceInfo
from pathlib import Path
from socketio import SimpleClient
from threading import Thread

from config import PREFERRED_ADAPTER

# https://forums.balena.io/t/discover-avahi-zeroconf-services-inside-container/48665/4

class Peer:
    def __init__(self, ip_address: str, port: int, hostname: str, uuid: str):
        self.ip_address: str = ip_address
        self.port: int = port
        self.hostname: str = hostname
        self.uuid: str = uuid

        self.sio = SimpleClient()
        self.sio.connect(f"http://{ip_address}:{port}")
        self.sio.emit("hello", {"hostname": Path('/etc/hostname').read_text()})

    def close(self):
        pass

class TechDeckServiceListener(ServiceListener):
    def __init__(self, manager: "P2PNetworkManager"):
        self.network_manager: P2PNetworkManager = manager

    def get_info(self, zc: Zeroconf, type_: str, name: str):
        info = zc.get_service_info(type_, name)
        return {"ip_address": socket.inet_ntoa(info.addresses[0]), "port": info.port, "hostname": name.split(".")[0], "uuid": info.properties[b"uuid"].decode("utf-8")}

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        pass

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        for peer in self.network_manager.peers:
            if peer.hostname == name.split(".")[0]:
                peer.close()
                self.network_manager.peers.remove(peer)

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = self.get_info(zc, type_, name)
        if info["uuid"] != self.network_manager.service_info.properties[b"uuid"].decode("utf-8") and socket.inet_aton(info["ip_address"]) not in self.network_manager.service_info.addresses: # if the detected peer isn't this device
            self.network_manager.peers.append(Peer(**info))

class P2PNetworkManager:
    def __init__(self):
        self.uuid = str(uuid4())

        self.peers: list[Peer] = []

        self.service_info: ServiceInfo = ServiceInfo(
            "_techdeck._tcp.local.",
            f"{self.get_hostname()}._techdeck._tcp.local.",
            port=8383,
            addresses=[socket.inet_aton(ip) for ip in self.find_ip_addresses()],
            properties={"uuid": self.uuid}
        )

        self.zeroconf: Zeroconf = Zeroconf()
        self.listener: TechDeckServiceListener = TechDeckServiceListener(self)
        self.browser: ServiceBrowser = ServiceBrowser(self.zeroconf, "_techdeck._tcp.local.", self.listener)
        t = Thread(target=self.make_discoverable_after_timeout) # other nodes will attempt to connect as soon as the node is made discoverable and they can't until fastapi is accepting requests
        t.start()

    def make_discoverable(self):
        self.zeroconf.register_service(self.service_info)

    def make_discoverable_after_timeout(self):
        time.sleep(5)
        self.make_discoverable()

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

    def get_hostname(self):
        return "".join([char for char in Path('/etc/hostname').read_text() if char.isalnum()])

    def shutdown(self):
        self.zeroconf.close()

# we have to do this because when instantiating the class in the same python file as the fastapi app, the zeroconf event loop is blocked.
# why is it blocked? i have no idea. but it is, so we have to do this.
p2p_network_manager: P2PNetworkManager = P2PNetworkManager()