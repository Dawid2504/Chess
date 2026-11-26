"""
Hochauflösende Staunton-Schachfiguren mit 4x-Supersampling (Anti-Aliasing)
und weichem Schlagschatten für Pygame.
"""

from __future__ import annotations

import pygame

# Farbschema für die Figuren
WEISS_FUELLUNG = (252, 249, 242)
WEISS_KONTUR = (42, 38, 34)
WEISS_DETAIL = (175, 166, 152)

SCHWARZ_FUELLUNG = (44, 44, 48)
SCHWARZ_KONTUR = (16, 16, 18)
SCHWARZ_DETAIL = (170, 172, 182)


def _pt(x: float, y: float, s: int) -> tuple[int, int]:
    return (int(round(x * s)), int(round(y * s)))


def _pts(coords: list[tuple[float, float]], s: int) -> list[tuple[int, int]]:
    return [_pt(x, y, s) for x, y in coords]


def _zeichne_gefuelltes_polygon(
    surf: pygame.Surface,
    punkte: list[tuple[int, int]],
    fuellung: tuple[int, int, int],
    kontur: tuple[int, int, int],
    kontur_breite: int,
) -> None:
    pygame.draw.polygon(surf, fuellung, punkte)
    pygame.draw.polygon(surf, kontur, punkte, width=kontur_breite)


def _zeichne_sockel(
    surf: pygame.Surface,
    s: int,
    fuellung: tuple[int, int, int],
    kontur: tuple[int, int, int],
    detail: tuple[int, int, int],
    kb: int,
) -> None:
    """Zeichnet den gemeinsamen zweistufigen Staunton-Sockel."""
    # Oberer Sockelring
    ober_rect = pygame.Rect(int(0.25 * s), int(0.76 * s), int(0.50 * s), int(0.075 * s))
    pygame.draw.rect(surf, fuellung, ober_rect, border_radius=int(0.03 * s))
    pygame.draw.rect(surf, kontur, ober_rect, width=kb, border_radius=int(0.03 * s))

    # Unterer Standfuß
    unter_rect = pygame.Rect(int(0.19 * s), int(0.82 * s), int(0.62 * s), int(0.085 * s))
    pygame.draw.rect(surf, fuellung, unter_rect, border_radius=int(0.035 * s))
    pygame.draw.rect(surf, kontur, unter_rect, width=kb, border_radius=int(0.035 * s))

    # Feine Glanz-/Trennlinie auf dem Sockel
    pygame.draw.line(
        surf,
        detail,
        _pt(0.27, 0.805, s),
        _pt(0.73, 0.805, s),
        max(2, kb // 2),
    )


def _zeichne_kragen(
    surf: pygame.Surface,
    s: int,
    y_mitte: float,
    halb_breite: float,
    fuellung: tuple[int, int, int],
    kontur: tuple[int, int, int],
    kb: int,
) -> None:
    h = 0.055
    rect = pygame.Rect(
        int((0.50 - halb_breite) * s),
        int((y_mitte - h / 2) * s),
        int(halb_breite * 2 * s),
        int(h * s),
    )
    pygame.draw.rect(surf, fuellung, rect, border_radius=int(0.025 * s))
    pygame.draw.rect(surf, kontur, rect, width=kb, border_radius=int(0.025 * s))


def _zeichne_bauer(surf: pygame.Surface, s: int, fuellung, kontur, detail, kb: int) -> None:
    # Körper
    koerper = _pts([(0.41, 0.45), (0.59, 0.45), (0.68, 0.77), (0.32, 0.77)], s)
    _zeichne_gefuelltes_polygon(surf, koerper, fuellung, kontur, kb)

    # Kragen
    _zeichne_kragen(surf, s, 0.44, 0.145, fuellung, kontur, kb)

    # Kopf
    zentrum = _pt(0.50, 0.31, s)
    radius = int(0.125 * s)
    pygame.draw.circle(surf, fuellung, zentrum, radius)
    pygame.draw.circle(surf, kontur, zentrum, radius, width=kb)

    _zeichne_sockel(surf, s, fuellung, kontur, detail, kb)


def _zeichne_turm(surf: pygame.Surface, s: int, fuellung, kontur, detail, kb: int) -> None:
    # Turmschaft
    schaft = _pts([(0.34, 0.38), (0.66, 0.38), (0.70, 0.77), (0.30, 0.77)], s)
    _zeichne_gefuelltes_polygon(surf, schaft, fuellung, kontur, kb)

    # Zinnenkrone als geschlossenes Polygon
    krone = _pts([
        (0.27, 0.20), (0.37, 0.20), (0.37, 0.27),
        (0.45, 0.27), (0.45, 0.20), (0.55, 0.20),
        (0.55, 0.27), (0.63, 0.27), (0.63, 0.20),
        (0.73, 0.20), (0.73, 0.35), (0.66, 0.40),
        (0.34, 0.40), (0.27, 0.35),
    ], s)
    _zeichne_gefuelltes_polygon(surf, krone, fuellung, kontur, kb)

    # Innere Zierlinie
    pygame.draw.line(surf, detail, _pt(0.33, 0.35, s), _pt(0.67, 0.35, s), max(2, kb // 2))
    _zeichne_sockel(surf, s, fuellung, kontur, detail, kb)


def _zeichne_laeufer(surf: pygame.Surface, s: int, fuellung, kontur, detail, kb: int) -> None:
    # Körper
    koerper = _pts([(0.38, 0.50), (0.62, 0.50), (0.70, 0.77), (0.30, 0.77)], s)
    _zeichne_gefuelltes_polygon(surf, koerper, fuellung, kontur, kb)

    # Kragen
    _zeichne_kragen(surf, s, 0.49, 0.16, fuellung, kontur, kb)

    # Mitra (Kopf)
    mitra = _pts([
        (0.50, 0.20),
        (0.61, 0.28),
        (0.65, 0.39),
        (0.59, 0.48),
        (0.41, 0.48),
        (0.35, 0.39),
        (0.39, 0.28),
    ], s)
    _zeichne_gefuelltes_polygon(surf, mitra, fuellung, kontur, kb)

    # Charakteristischer Diagonal-Schlitz der Mitra
    pygame.draw.line(surf, detail, _pt(0.43, 0.41, s), _pt(0.57, 0.29, s), max(3, int(kb * 0.85)))

    # Obere Kugel
    spitze = _pt(0.50, 0.155, s)
    r = int(0.048 * s)
    pygame.draw.circle(surf, fuellung, spitze, r)
    pygame.draw.circle(surf, kontur, spitze, r, width=kb)

    _zeichne_sockel(surf, s, fuellung, kontur, detail, kb)


def _zeichne_springer(surf: pygame.Surface, s: int, fuellung, kontur, detail, kb: int) -> None:
    # Klassische Pferdekopf-Silhouette nach links blickend
    pferd = _pts([
        (0.30, 0.77),
        (0.34, 0.62),
        (0.45, 0.50),
        (0.39, 0.46),
        (0.28, 0.50),
        (0.22, 0.44),
        (0.25, 0.37),
        (0.34, 0.27),
        (0.41, 0.20),
        (0.43, 0.12),
        (0.50, 0.18),
        (0.58, 0.20),
        (0.68, 0.29),
        (0.74, 0.44),
        (0.73, 0.63),
        (0.69, 0.77),
    ], s)
    _zeichne_gefuelltes_polygon(surf, pferd, fuellung, kontur, kb)

    # Auge und Mähnen-Akzent
    pygame.draw.circle(surf, detail, _pt(0.38, 0.31, s), max(3, int(0.024 * s)))
    pygame.draw.circle(surf, detail, _pt(0.27, 0.43, s), max(2, int(0.014 * s)))
    pygame.draw.line(surf, detail, _pt(0.57, 0.26, s), _pt(0.66, 0.44, s), max(2, kb // 2))
    pygame.draw.line(surf, detail, _pt(0.66, 0.44, s), _pt(0.64, 0.65, s), max(2, kb // 2))

    _zeichne_sockel(surf, s, fuellung, kontur, detail, kb)


def _zeichne_dame(surf: pygame.Surface, s: int, fuellung, kontur, detail, kb: int) -> None:
    # Körper
    koerper = _pts([(0.34, 0.48), (0.66, 0.48), (0.71, 0.77), (0.29, 0.77)], s)
    _zeichne_gefuelltes_polygon(surf, koerper, fuellung, kontur, kb)

    # 5-zackige Krone
    krone = _pts([
        (0.32, 0.46),
        (0.20, 0.29),
        (0.34, 0.37),
        (0.35, 0.21),
        (0.44, 0.35),
        (0.50, 0.17),
        (0.56, 0.35),
        (0.65, 0.21),
        (0.66, 0.37),
        (0.80, 0.29),
        (0.68, 0.46),
    ], s)
    _zeichne_gefuelltes_polygon(surf, krone, fuellung, kontur, kb)

    # Perlen auf den Kronenspitzen
    for px, py in [(0.20, 0.29), (0.35, 0.21), (0.50, 0.17), (0.65, 0.21), (0.80, 0.29)]:
        pos = _pt(px, py, s)
        r = int(0.036 * s)
        pygame.draw.circle(surf, fuellung, pos, r)
        pygame.draw.circle(surf, kontur, pos, r, width=max(2, int(kb * 0.8)))

    _zeichne_kragen(surf, s, 0.47, 0.18, fuellung, kontur, kb)
    _zeichne_sockel(surf, s, fuellung, kontur, detail, kb)


def _zeichne_koenig(surf: pygame.Surface, s: int, fuellung, kontur, detail, kb: int) -> None:
    # Kreuz auf der Spitze
    kreuz_v = pygame.Rect(int(0.47 * s), int(0.10 * s), int(0.06 * s), int(0.15 * s))
    kreuz_h = pygame.Rect(int(0.415 * s), int(0.135 * s), int(0.17 * s), int(0.055 * s))
    pygame.draw.rect(surf, fuellung, kreuz_v)
    pygame.draw.rect(surf, kontur, kreuz_v, width=max(2, int(kb * 0.85)))
    pygame.draw.rect(surf, fuellung, kreuz_h)
    pygame.draw.rect(surf, kontur, kreuz_h, width=max(2, int(kb * 0.85)))
    # Kreuzmitte sauber überfüllen, damit keine innere Linie bleibt
    inner_rect = pygame.Rect(int(0.478 * s), int(0.143 * s), int(0.044 * s), int(0.04 * s))
    pygame.draw.rect(surf, fuellung, inner_rect)

    # Körper
    koerper = _pts([(0.34, 0.48), (0.66, 0.48), (0.71, 0.77), (0.29, 0.77)], s)
    _zeichne_gefuelltes_polygon(surf, koerper, fuellung, kontur, kb)

    # Königskrone (geschwungene Bögen)
    krone = _pts([
        (0.32, 0.46),
        (0.24, 0.34),
        (0.31, 0.25),
        (0.43, 0.25),
        (0.50, 0.22),
        (0.57, 0.25),
        (0.69, 0.25),
        (0.76, 0.34),
        (0.68, 0.46),
    ], s)
    _zeichne_gefuelltes_polygon(surf, krone, fuellung, kontur, kb)

    # Innere Kronen-Linien
    pygame.draw.line(surf, detail, _pt(0.50, 0.24, s), _pt(0.50, 0.43, s), max(2, kb // 2))
    pygame.draw.line(surf, detail, _pt(0.36, 0.35, s), _pt(0.64, 0.35, s), max(2, kb // 2))

    _zeichne_kragen(surf, s, 0.47, 0.18, fuellung, kontur, kb)
    _zeichne_sockel(surf, s, fuellung, kontur, detail, kb)


_ZEICHNER = {
    "p": _zeichne_bauer,
    "r": _zeichne_turm,
    "n": _zeichne_springer,
    "b": _zeichne_laeufer,
    "q": _zeichne_dame,
    "k": _zeichne_koenig,
}


def erstelle_figuren_surfaces(feld_groesse: int) -> dict[str, pygame.Surface]:
    """
    Erzeugt für alle 12 Figurentypen (P, N, B, R, Q, K, p, n, b, r, q, k)
    hochaufgelöste, weich kantengeglättete Surfaces inkl. Schlagschatten.
    """
    supersample = 4
    s = feld_groesse * supersample
    kontur_breite = max(6, int(0.024 * s))
    surfaces: dict[str, pygame.Surface] = {}

    for typ, zeichner in _ZEICHNER.items():
        for ist_weiss in (True, False):
            symbol = typ.upper() if ist_weiss else typ.lower()
            fuellung = WEISS_FUELLUNG if ist_weiss else SCHWARZ_FUELLUNG
            kontur = WEISS_KONTUR if ist_weiss else SCHWARZ_KONTUR
            detail = WEISS_DETAIL if ist_weiss else SCHWARZ_DETAIL

            # 1. Figur in 4x-Auflösung zeichnen
            hi_res = pygame.Surface((s, s), pygame.SRCALPHA)
            zeichner(hi_res, s, fuellung, kontur, detail, kontur_breite)
            figur_klein = pygame.transform.smoothscale(hi_res, (feld_groesse, feld_groesse))

            # 2. Weichen Schlagschatten aus der Alpha-Maske erzeugen
            schatten_hi = pygame.Surface((s, s), pygame.SRCALPHA)
            zeichner(schatten_hi, s, (0, 0, 0, 72), (0, 0, 0, 72), (0, 0, 0, 0), kontur_breite)
            schatten_klein = pygame.transform.smoothscale(schatten_hi, (feld_groesse, feld_groesse))

            # 3. Schatten + Figur kombinieren
            kombi = pygame.Surface((feld_groesse, feld_groesse), pygame.SRCALPHA)
            kombi.blit(schatten_klein, (2, 3))
            kombi.blit(figur_klein, (0, 0))

            surfaces[symbol] = kombi

    return surfaces
