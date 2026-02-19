import asyncio
import ssl
import socket

async def proxy_data(reader, writer):
    try:
        while True:
            data = await reader.read(8192)
            if not data: break
            writer.write(data)
            await writer.drain()
    except:
        pass
    finally:
        writer.close()

async def handle_socks5(reader, writer):
    try:
        # 1. Handshake
        await reader.read(2)
        writer.write(b"\x05\x00")
        await writer.drain()

        # 2. Request
        data = await reader.read(4)
        print(data)
        if not data: return
        print(data)
        mode = data[1]
        addr_type = data[3]

        if addr_type == 1: # IPv4
            addr = socket.inet_ntoa(await reader.read(4))
        elif addr_type == 3: # Domain
            length = (await reader.read(1))[0]
            addr = (await reader.read(length)).decode()
        else:
            raise ValueError(f"Unknown addr type:{addr_type}")
        
        port = int.from_bytes(await reader.read(2), 'big')

        # 3. Connect to destination
        remote_reader, remote_writer = await asyncio.open_connection(addr, port)
        writer.write(b"\x05\x00\x00\x01" + socket.inet_aton("0.0.0.0") + (0).to_bytes(2, 'big'))
        await writer.drain()

        # 4. Forwarding
        await asyncio.gather(
            proxy_data(reader, remote_writer),
            proxy_data(remote_reader, writer)
        )
    except Exception:
        writer.close()

async def main():
    # Укажите пути к вашим SSL сертификатам
    
    server = await asyncio.start_server(handle_socks5, '0.0.0.0', 8443)
    async with server:
        print("cat")
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())
