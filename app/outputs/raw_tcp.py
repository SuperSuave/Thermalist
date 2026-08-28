from __future__ import annotations
import socket
from app.core.models import RenderedReceipt
from app.outputs.base import OutputBackend


class RawTcpOutput(OutputBackend):
    name = "raw_tcp"

    def send(
        self,
        receipt: RenderedReceipt,
        host: str,
        port: int = 9100,
        timeout: int = 5,
        dry_run: bool = True,
        cut: bool = False,
        initialize: bool = True,
        font: str = "A",
    ) -> dict:
        parts: list[bytes] = []

        if initialize:
            parts.append(b"\x1b\x40")  # ESC @

        if receipt.raw_bytes is not None:
            # Use pre-built ESC/POS bytes directly
            parts.append(receipt.raw_bytes)
        else:
            # Fall back to text encoding
            if font == "A":
                parts.append(b"\x1b\x4d\x00")  # ESC M 0 — Font A
            elif font == "B":
                parts.append(b"\x1b\x4d\x01")  # ESC M 1 — Font B

            normalized = receipt.text_preview.replace("\r\n", "\n").replace("\r", "\n")
            for line in normalized.split("\n"):
                parts.append(line.encode("utf-8", errors="replace"))
                parts.append(b"\x0a")

            parts.append(b"\x0a")

        if cut:
            parts.append(b"\x1d\x56\x00")

        payload = b"".join(parts)

        if dry_run:
            return {
                "status": "ok",
                "backend": self.name,
                "mode": "dry_run",
                "bytes": len(payload),
                "preview_text": receipt.text_preview,
                "payload_hex": payload.hex(" "),
                "font": font,
            }

        with socket.create_connection((host, port), timeout=timeout) as sock:
            sock.sendall(payload)

        return {
            "status": "ok",
            "backend": self.name,
            "mode": "network",
            "host": host,
            "port": port,
            "bytes": len(payload),
            "cut": cut,
            "initialize": initialize,
            "font": font,
        }
