
import socket
import ifaddr
import time
import random
import asyncio
from uuid import uuid4
from zeroconf import Zeroconf, ServiceBrowser, ServiceListener, ServiceInfo
from pathlib import Path
from socketio import SimpleClient, AsyncServer
from threading import Thread
from typing import TYPE_CHECKING

from config import PREFERRED_ADAPTER, DEBUG_MODE, SOCKETIO_LOGGING

if TYPE_CHECKING:
    from show import Show

# https://forums.balena.io/t/discover-avahi-zeroconf-services-inside-container/48665/4

class Peer:
    def __init__(self, network_manager: "P2PNetworkManager", ip_address: str, port: int, hostname: str, uuid: str):
        self.network_manager: "P2PNetworkManager" = network_manager
        self.ip_address: str = ip_address
        self.port: int = port
        self.hostname: str = hostname
        self.uuid: str = uuid

        if DEBUG_MODE:
            print(f"Connected to peer {hostname} with UUID {uuid} at {ip_address}:{port}")

        self.sio = SimpleClient(logger=SOCKETIO_LOGGING, engineio_logger=SOCKETIO_LOGGING)
        self.sio.connect(f"http://{ip_address}:{port}")

        if self.network_manager.master_node == self.network_manager.host: # if this host is the master node, fill in the new peer
            self.send("master_node", {"master_uuid": self.network_manager.master_node.uuid if self.network_manager.master_node else "", "fallback_master_uuid": self.network_manager.fallback_master.uuid if self.network_manager.fallback_master else ""})
            if self.network_manager.show:
                self.send("selected_show", {"title": self.network_manager.show.title})
                self.send("blackout_state_changed", {"new_state": self.network_manager.show.blackout})
                self.send("cue_list_changed", {"cue_list": self.network_manager.show.cue_list.serialize()})
                self.send("current_cue_changed", {"current_cue": self.network_manager.show.current_cue})
                # TODO: synchronize subsystem states
                # TODO: synchronize audio and background libraries
                # TODO: synchronize things like timed cues

    def send(self, event: str, data: dict | None = None):
        if DEBUG_MODE:
            print(f"Sending peer {self.hostname} message {event}: {data}")
        if data:
            self.sio.emit(event, data)
        else:
            self.sio.emit(event)

    def close(self):
        if DEBUG_MODE:
            print(f"Disconnected from peer {self.hostname} with UUID {self.uuid} at {self.ip_address}:{self.port}")

        self.sio.disconnect()

class Host: # implements Peer class for the host for simplicity
    def __init__(self, network_manager: "P2PNetworkManager"):
        self.network_manager: "P2PNetworkManager" = network_manager
        self.ip_address: str = self.network_manager.find_ip_addresses()[0]
        self.port: int = 8383
        self.hostname: str = self.network_manager.get_hostname()
        self.uuid: str = self.network_manager.uuid
    
    def send(self, event: str, data: dict | None = None):
        pass

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

                if peer == self.network_manager.master_node: # if the master node just disconnected
                    self.network_manager.set_master_node(self.network_manager.fallback_master.uuid if self.network_manager.fallback_master else "", None) # make the fallback master the new master, and force reselection of a new fallback

                if peer == self.network_manager.fallback_master: # if the fallback master just disconnected
                    self.network_manager.set_master_node(self.network_manager.master_node.uuid, None) # remove the fallback master (the function selects a new one if possible)

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = self.get_info(zc, type_, name)
        if info["uuid"] != self.network_manager.service_info.properties[b"uuid"].decode("utf-8") and socket.inet_aton(info["ip_address"]) not in self.network_manager.service_info.addresses: # if the detected peer isn't this device
            self.network_manager.peers.append(Peer(self.network_manager, **info))

            if self.network_manager.master_node == self.network_manager.host and (self.network_manager.fallback_master == self.network_manager.master_node or not self.network_manager.fallback_master): # if the host is the master and there is no unique fallback master
                self.network_manager.set_master_node(self.network_manager.master_node.uuid, self.network_manager.peers[-1].uuid) # make this node the fallback master

class P2PNetworkManager:
    def __init__(self):
        self.sio: AsyncServer = None # type: ignore

        self.show: "Show" | None = None

        self.uuid = str(uuid4())

        self.host = Host(self)
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

        self.master_node: Peer | Host | None = None
        self.fallback_master: Peer | Host | None = None

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

    def get_peer_by_uuid(self, uuid: str) -> Peer | None:
        for peer in self.peers:
            if peer.uuid == uuid:
                return peer
        return None

    def set_master_node(self, master_uuid: str | None, fallback_master_uuid: str | None):
        self.master_node = self.host if master_uuid == self.uuid else self.get_peer_by_uuid(master_uuid)
        self.fallback_master = self.host if fallback_master_uuid == self.uuid else self.get_peer_by_uuid(fallback_master_uuid)

        if self.master_node == self.host: # if this node is the new master
            if (self.fallback_master == self.host or not self.fallback_master) and self.peers: # if this node is both the master and fallback master or there is no fallback master when other peers are available
                self.fallback_master = random.choice(self.peers) # pick a new fallback master

            self.broadcast_to_servers("master_node", {"master_uuid": self.master_node.uuid if self.master_node else "", "fallback_master_uuid": self.fallback_master.uuid if self.fallback_master else ""})
            self.broadcast_to_client("master_node", {"master_uuid": self.master_node.uuid if self.master_node else "", "fallback_master_uuid": self.fallback_master.uuid if self.fallback_master else ""})

        if DEBUG_MODE:
            print(f"Master node: {self.master_node.hostname if self.master_node else 'None'}")
            print(f"Fallback master: {self.fallback_master.hostname if self.fallback_master else 'None'}")

    @property
    def is_master_node(self):
        return self.master_node == self.host

    def broadcast_to_servers(self, event: str, data: dict | None = None) -> None:
        for peer in self.peers:
            if data:
                peer.send(event, data)
            else:
                peer.send(event)

    def broadcast_to_client(self, event: str, data: dict | None = None) -> None:
        try:
            asyncio.get_running_loop()
            if data:
                asyncio.create_task(self.sio.emit(event, data))
            else:
                asyncio.create_task(self.sio.emit(event))
        except RuntimeError:
            if data:
                asyncio.run(self.sio.emit(event, data))
            else:
                asyncio.run(self.sio.emit(event))

    async def broadcast_to_client_async(self, event: str, data: dict | None = None) -> None:
        if data:
            await self.sio.emit(event, data)
        else:
            await self.sio.emit(event)

# we have to do this because when instantiating the class in the same python file as the fastapi app, the zeroconf event loop is blocked.
# why is it blocked? i have no idea. but it is, so we have to do this.
p2p_network_manager: P2PNetworkManager = P2PNetworkManager()
