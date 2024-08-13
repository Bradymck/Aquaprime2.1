import asyncio
import os
import signal
import sys
import subprocess

def install_package(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

async def main():
    packages = [
        "aiohttp==3.10.3"
    ]

    for package in packages:
        try:
            install_package(package)
        except subprocess.CalledProcessError:
            print(f"Failed to install {package}. Trying to resolve conflicts...")

            # Attempt to install without version constraints
            package_name = package.split("==")[0]
            install_package(package_name)

    loop = asyncio.get_event_loop()

    if os.name != 'nt':
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(shutdown(s, loop)))
    else:
        # Windows specific signal handling
        import threading

        def win_shutdown():
            asyncio.run_coroutine_threadsafe(shutdown(signal.SIGINT, loop), loop)

        def win_signal_handler(signal, frame):
            threading.Thread(target=win_shutdown).start()

        signal.signal(signal.SIGINT, win_signal_handler)
        signal.signal(signal.SIGTERM, win_signal_handler)

async def shutdown(signal, loop):
    print(f"Received exit signal {signal.name}...")
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]

    for task in tasks:
        task.cancel()

    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()

if __name__ == "__main__":
    asyncio.run(main())