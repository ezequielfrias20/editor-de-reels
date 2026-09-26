#!/usr/bin/env python3
"""Una pieza pedida desde el dashboard (Cubo Marketing): su `pedido.json`, sus clips y la
unión de varias tomas en una sola fuente.

El dashboard escribe `VIDEOS ORIGINALES/<n>/pedido.json` con cada clip y su ROL:
`cuerpo` (una o más tomas del hablante, en `orden`), `cta` (una por plataforma; cada una
genera una versión), `pantalla` y `apoyo`. Ver la skill `editar-pieza`.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

ROLES = ("cuerpo", "cta", "pantalla", "apoyo")
PALETAS = ("claro", "oscuro")


class PiezaError(Exception):
    """Algo del pedido o de los clips impide seguir. El mensaje va tal cual al usuario."""


@dataclass(frozen=True)
class Clip:
    archivo: str
    rol: str
    orden: int
    plataforma: str | None = None


@dataclass(frozen=True)
class Pedido:
    pieza: int
    titulo: str
    origen: dict
    prompt: str
    paleta: str
    clips: tuple[Clip, ...]
    carpeta: Path

    def de_rol(self, rol: str) -> list[Clip]:
        return sorted((c for c in self.clips if c.rol == rol), key=lambda c: c.orden)

    @property
    def plataformas(self) -> list[str]:
        """Una versión por CTA; sin CTA, una sola versión `general`."""
        return [c.plataforma for c in self.de_rol("cta")] or ["general"]

    def ruta(self, clip: Clip) -> Path:
        return self.carpeta / clip.archivo


def carpeta(root: Path, n: int | str) -> Path:
    return Path(root) / "VIDEOS ORIGINALES" / str(n)


def cargar_pedido(root: Path, n: int) -> Pedido:
    d = carpeta(root, n)
    f = d / "pedido.json"
    if not f.exists():
        raise PiezaError(f"no existe {f}: la pieza {n} no se pidió desde el dashboard")
    raw = json.loads(f.read_text())
    problemas: list[str] = []
    clips: list[Clip] = []
    for i, c in enumerate(raw.get("clips", [])):
        rol, archivo = c.get("rol"), c.get("archivo", "")
        if rol not in ROLES:
            problemas.append(f"clip {i} ({archivo}): rol {rol!r} desconocido (van {', '.join(ROLES)})")
            continue
        if rol == "cta" and not c.get("plataforma"):
            problemas.append(f"clip {i} ({archivo}): un cta necesita plataforma")
        if not (d / archivo).is_file():
            problemas.append(f"clip {i}: no existe {archivo} en {d}")
        clips.append(Clip(archivo=archivo, rol=rol, orden=int(c.get("orden", i + 1)),
                          plataforma=c.get("plataforma")))
    if not any(c.rol == "cuerpo" for c in clips):
        problemas.append("no hay ningún clip de cuerpo")
    vistas: set[str] = set()
    for c in clips:
        if c.rol == "cta" and c.plataforma:
            if c.plataforma in vistas:
                problemas.append(f"hay dos CTA para {c.plataforma}")
            vistas.add(c.plataforma)
    if raw.get("paleta") not in PALETAS:
        problemas.append(f"paleta {raw.get('paleta')!r}: tiene que ser claro u oscuro")
    if problemas:
        raise PiezaError("; ".join(problemas))
    return Pedido(pieza=int(raw.get("pieza", n)), titulo=raw.get("titulo", ""),
                  origen=raw.get("origen") or {"tipo": "libre"}, prompt=raw.get("prompt", ""),
                  paleta=raw["paleta"], clips=tuple(clips), carpeta=d)


# ── Sondeo ──────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Info:
    codec: str
    ancho: int
    alto: int
    fps: str
    rotacion: int
    duracion: float
    audio: str | None
    color_trc: str | None
    color_primaries: str | None
    color_space: str | None

    @property
    def orientacion(self) -> str:
        """La que VE el espectador: el footage de iPhone guarda la rotación aparte."""
        w, h = (self.alto, self.ancho) if self.rotacion % 180 else (self.ancho, self.alto)
        r = w / h
        return "cuadrada" if 0.95 <= r <= 1.05 else ("horizontal" if r > 1 else "vertical")

    @property
    def firma(self) -> tuple:
        """Lo que tiene que coincidir para concatenar con `-c copy`."""
        return (self.codec, self.ancho, self.alto, self.fps, self.rotacion, self.audio,
                self.color_trc)


def probe(path: Path) -> Info:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format",
                          "-of", "json", str(path)], capture_output=True, text=True)
    if out.returncode != 0:
        raise PiezaError(f"ffprobe no puede leer {Path(path).name}: {out.stderr.strip()[:200]}")
    d = json.loads(out.stdout)
    v = next((s for s in d["streams"] if s["codec_type"] == "video"), None)
    if v is None:
        raise PiezaError(f"{Path(path).name} no tiene video")
    a = next((s for s in d["streams"] if s["codec_type"] == "audio"), None)
    rot = 0
    for sd in v.get("side_data_list", []):
        if "rotation" in sd:
            rot = int(sd["rotation"])
    rot = int(v.get("tags", {}).get("rotate", rot))
    return Info(codec=v["codec_name"], ancho=int(v["width"]), alto=int(v["height"]),
                fps=v.get("r_frame_rate", "0/0"), rotacion=abs(rot) % 360,
                duracion=float(d["format"]["duration"]), audio=a["codec_name"] if a else None,
                color_trc=v.get("color_transfer"), color_primaries=v.get("color_primaries"),
                color_space=v.get("color_space"))


# ── Unión ───────────────────────────────────────────────────────────────────────
def _ffmpeg(args: list[str]) -> None:
    r = subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-y", *args],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise PiezaError(f"ffmpeg falló: {r.stderr.strip()[-400:]}")


def unir(clips: list[Path], salida: Path) -> str:
    """Une las tomas en `salida`, en el orden dado.

    - una sola toma: enlace duro (o copia si el disco no deja), sin recodificar;
    - tomas con la misma firma: concat demuxer con `-c copy`;
    - si no: se recodifican al tamaño, fps y color de la PRIMERA.
    Falla si las orientaciones no coinciden o si una toma no tiene audio.
    """
    clips = [Path(c) for c in clips]
    infos = [probe(c) for c in clips]
    ors = {i.orientacion for i in infos}
    if len(ors) > 1:
        detalle = ", ".join(f"{c.name} {i.orientacion}" for c, i in zip(clips, infos))
        raise PiezaError(f"las tomas no tienen la misma orientación: {detalle}. "
                         f"Vuelve a grabar o quita la que no corresponde")
    sin_audio = [c.name for c, i in zip(clips, infos) if i.audio is None]
    if sin_audio:
        raise PiezaError(f"sin audio: {', '.join(sin_audio)}")
    salida = Path(salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.unlink(missing_ok=True)

    if len(clips) == 1:
        try:
            os.link(clips[0], salida)
        except OSError:
            shutil.copyfile(clips[0], salida)
        return "enlace"

    base = infos[0]
    if all(i.firma == base.firma for i in infos[1:]):
        lista = salida.with_suffix(".txt")
        lista.write_text("".join(
            "file '" + str(c.resolve()).replace("'", "'\\''") + "'\n" for c in clips))
        try:
            _ffmpeg(["-f", "concat", "-safe", "0", "-i", str(lista), "-c", "copy",
                     "-movflags", "+faststart", str(salida)])
        finally:
            lista.unlink(missing_ok=True)
        return "copia"

    # Recodificar: tamaño que VE el espectador (ffmpeg aplica la rotación al decodificar).
    w, h = (base.alto, base.ancho) if base.rotacion % 180 else (base.ancho, base.alto)
    hdr = base.color_trc == "arib-std-b67"
    entradas: list[str] = []
    filtros: list[str] = []
    for k, c in enumerate(clips):
        entradas += ["-i", str(c)]
        filtros.append(f"[{k}:v]scale={w}:{h}:force_original_aspect_ratio=decrease,"
                       f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={base.fps}[v{k}]")
        filtros.append(f"[{k}:a]aresample=48000,aformat=channel_layouts=stereo[a{k}]")
    pares = "".join(f"[v{k}][a{k}]" for k in range(len(clips)))
    filtros.append(f"{pares}concat=n={len(clips)}:v=1:a=1[v][a]")
    color: list[str] = []
    for flag, val in (("-color_trc", base.color_trc), ("-color_primaries", base.color_primaries),
                      ("-colorspace", base.color_space)):
        if val and val != "unknown":
            color += [flag, val]
    _ffmpeg([*entradas, "-filter_complex", ";".join(filtros), "-map", "[v]", "-map", "[a]",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "16",
             "-pix_fmt", "yuv420p10le" if hdr else "yuv420p", *color,
             "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(salida)])
    return "recodificado"
