"""Download uitsluitend de zes openbare, ongewijzigde archiefpreviews."""
import json
from pathlib import Path
from urllib.request import Request, urlopen

STUDIE = Path(__file__).resolve().parents[1] / "documentatie/studie/turner-jozef"


def main():
    bronnen = json.loads((STUDIE / "bronnen.json").read_text())
    verslag = []
    for item in bronnen["items"]:
        doel = STUDIE / item["file"]
        try:
            request = Request(item["preview"], headers={"User-Agent": "TurnerStudy/1.0"})
            with urlopen(request, timeout=30) as response:
                data = response.read()
                if not response.headers.get_content_type().startswith("image/"):
                    raise ValueError("Antwoord is geen afbeelding")
            if not data.startswith(b"\xff\xd8\xff"):
                raise ValueError("Antwoord is geen JPEG-preview")
            doel.parent.mkdir(parents=True, exist_ok=True)
            doel.write_bytes(data)
            status = "opgeslagen"
        except Exception as exc:
            status = f"niet opgeslagen: {exc}"
        print(item["id"], status)
        verslag.append({"id": item["id"], "status": status})
    (STUDIE / "downloadverslag.json").write_text(
        json.dumps(verslag, ensure_ascii=False, indent=2) + "\n"
    )
    return 0 if all(x["status"] == "opgeslagen" for x in verslag) else 1


if __name__ == "__main__":
    raise SystemExit(main())
