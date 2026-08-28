from __future__ import annotations
from escpos.printer import Dummy, Network
from app.core.models import RenderedReceipt
from app.outputs.base import OutputBackend


class EscposPythonOutput(OutputBackend):
    name = "escpos"

    def _write_lines(self, printer, text: str) -> None:
        for line in text.splitlines():
            printer.text(line)
            printer.ln()
        printer.ln()

    def send(
        self,
        receipt: RenderedReceipt,
        host: str | None = None,
        port: int = 9100,
        profile: str | None = None,
        dry_run: bool = True,
    ) -> dict:
        if dry_run or not host:
            printer = Dummy()
            self._write_lines(printer, receipt.text_preview)
            printer.cut()
            return {
                "status": "ok",
                "backend": self.name,
                "mode": "dummy",
                "bytes": len(printer.output),
            }

        printer = Network(host=host, port=port, profile=profile) if profile else Network(host=host, port=port)
        self._write_lines(printer, receipt.text_preview)
        printer.cut()
        return {
            "status": "ok",
            "backend": self.name,
            "mode": "network",
            "host": host,
            "port": port,
        }
