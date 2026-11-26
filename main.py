"""
Schachbrett & Engine-Testumgebung
Entwickelt mit Pygame und python-chess.

Steuerung:
  - Startseite:              Spielmodus wählen (Freund oder Bot)
  - Linksklick:              Figur auswählen / Ziel wählen (erneuter Klick deselektiert)
  - [Z]:                     Zug rückgängig machen (Undo)
  - [R]:                     Partie zurücksetzen (Reset)
  - [E]:                     Engine-Modus für Schwarz ein-/ausschalten
  - [ESC]:                   Zurück zur Startseite
"""

from __future__ import annotations

import queue
import threading

import chess
import pygame

from engine import berechne_zug, bewerte_stellung
from figuren import erstelle_figuren_surfaces

# --- KONFIGURATION & GEOMETRIE ---
FELD_GROESSE = 80
BRETT_GROESSE = FELD_GROESSE * 8
BRETT_RAND = 18
EVAL_BAR_BREITE = 28
EVAL_BAR_ABSTAND = 14
SIDEBAR_BREITE = 264

BREITE = BRETT_RAND * 2 + BRETT_GROESSE + EVAL_BAR_ABSTAND + EVAL_BAR_BREITE + SIDEBAR_BREITE
HOEHE = BRETT_RAND * 2 + BRETT_GROESSE
BRETT_RECT = pygame.Rect(BRETT_RAND, BRETT_RAND, BRETT_GROESSE, BRETT_GROESSE)
EVAL_BAR_RECT = pygame.Rect(
    BRETT_RECT.right + EVAL_BAR_ABSTAND, BRETT_RAND, EVAL_BAR_BREITE, BRETT_GROESSE
)
BRETT_MITTE_X = BRETT_RECT.centerx
BRETT_MITTE_Y = BRETT_RECT.centery

# --- FARBPALETTE ---
FARBE_HINTERGRUND = (24, 26, 30)
FARBE_RAHMEN = (52, 42, 36)
FARBE_RAHMEN_HELL = (76, 63, 54)
FARBE_RAHMEN_DUNKEL = (30, 24, 20)

FARBE_FELD_HELL = (238, 219, 184)
FARBE_FELD_DUNKEL = (176, 132, 95)

FARBE_KARTE = (34, 37, 44)
FARBE_KARTE_HOVER = (48, 52, 62)
FARBE_KARTE_RAND = (58, 63, 74)

FARBE_AKZENT = (146, 184, 72)
FARBE_AKZENT_HELL = (176, 214, 96)
FARBE_WARNUNG = (225, 75, 75)
FARBE_TEXT_HELL = (242, 244, 248)
FARBE_TEXT_GEDIMMT = (158, 165, 178)

# Button-Geometrie (Startseite)
BTN_FREUND_RECT = pygame.Rect((BREITE - 390) // 2, 295, 390, 92)
BTN_BOT_RECT = pygame.Rect((BREITE - 390) // 2, 408, 390, 92)

# Sidebar-Buttons
_SB_X = EVAL_BAR_RECT.right + BRETT_RAND
_SB_W = SIDEBAR_BREITE - BRETT_RAND * 2 + 6
_BTN_W = (_SB_W - 8) // 2
BTN_SB_UNDO = pygame.Rect(_SB_X, HOEHE - 104, _BTN_W, 38)
BTN_SB_RESET = pygame.Rect(_SB_X + _BTN_W + 8, HOEHE - 104, _BTN_W, 38)
BTN_SB_BOT = pygame.Rect(_SB_X, HOEHE - 58, _BTN_W, 38)
BTN_SB_MENU = pygame.Rect(_SB_X + _BTN_W + 8, HOEHE - 58, _BTN_W, 38)

# Game-Over-Buttons (über dem Brett zentriert)
BTN_GO_NEU = pygame.Rect(BRETT_MITTE_X - 155, BRETT_MITTE_Y + 26, 145, 38)
BTN_GO_MENU = pygame.Rect(BRETT_MITTE_X + 10, BRETT_MITTE_Y + 26, 145, 38)

START_ANZAHL = {
    chess.PAWN: 8,
    chess.KNIGHT: 2,
    chess.BISHOP: 2,
    chess.ROOK: 2,
    chess.QUEEN: 1,
}
FIGUR_WERTE = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
}


# --- ENGINE-SCHNITTSTELLE ---
def meine_engine_zug(board: chess.Board) -> chess.Move | None:
    """Ruft die starke Schach-Engine aus engine.py auf."""
    return berechne_zug(board)


# --- RESSOURCEN & EFFEKTE ---
def erstelle_schriften() -> dict[str, pygame.font.Font]:
    """Initialisiert Schriftarten für UI, Titel, Züge und Koordinaten."""
    verfuegbar = set(pygame.font.get_fonts())
    ui_font = "segoeui" if "segoeui" in verfuegbar else "arial"
    mono_font = "consolas" if "consolas" in verfuegbar else "couriernew"

    return {
        "titel": pygame.font.SysFont(ui_font, 46, bold=True),
        "untertitel": pygame.font.SysFont(ui_font, 17),
        "banner": pygame.font.SysFont(ui_font, 26, bold=True),
        "karte_titel": pygame.font.SysFont(ui_font, 21, bold=True),
        "info": pygame.font.SysFont(ui_font, 16, bold=True),
        "klein": pygame.font.SysFont(ui_font, 14),
        "winzig": pygame.font.SysFont(ui_font, 12, bold=True),
        "zuege": pygame.font.SysFont(mono_font, 14),
        "koordinaten": pygame.font.SysFont(ui_font, 11, bold=True),
        "eval": pygame.font.SysFont(ui_font, 10, bold=True),
    }


def erstelle_effekt_surfaces() -> dict[str, pygame.Surface]:
    """Erstellt vorgerenderte, kantengeglättete Overlays (Glow, Punkte, Ringe)."""
    # 1. Schach-Radial-Glow
    schach_glow = pygame.Surface((FELD_GROESSE, FELD_GROESSE), pygame.SRCALPHA)
    mitte = FELD_GROESSE // 2
    max_r = FELD_GROESSE // 2
    for r in range(max_r, 0, -1):
        t = 1.0 - (r / max_r)
        alpha = int(215 * (t ** 1.35))
        pygame.draw.circle(schach_glow, (230, 45, 45, alpha), (mitte, mitte), r)

    # 2. Punkt für ruhige Züge (2x Supersampling)
    s2 = FELD_GROESSE * 2
    punkt_hi = pygame.Surface((s2, s2), pygame.SRCALPHA)
    pygame.draw.circle(punkt_hi, (35, 45, 30, 88), (FELD_GROESSE, FELD_GROESSE), int(s2 * 0.155))
    zug_punkt = pygame.transform.smoothscale(punkt_hi, (FELD_GROESSE, FELD_GROESSE))

    # 3. Ring für Schlagzüge (2x Supersampling)
    ring_hi = pygame.Surface((s2, s2), pygame.SRCALPHA)
    pygame.draw.circle(
        ring_hi,
        (220, 62, 62, 185),
        (FELD_GROESSE, FELD_GROESSE),
        int(s2 * 0.44),
        width=max(6, int(s2 * 0.055)),
    )
    zug_ring = pygame.transform.smoothscale(ring_hi, (FELD_GROESSE, FELD_GROESSE))

    # 4. Halbtransparente Feld-Overlays
    letzter_zug_overlay = pygame.Surface((FELD_GROESSE, FELD_GROESSE), pygame.SRCALPHA)
    letzter_zug_overlay.fill((205, 210, 75, 105))

    auswahl_overlay = pygame.Surface((FELD_GROESSE, FELD_GROESSE), pygame.SRCALPHA)
    auswahl_overlay.fill((128, 178, 62, 130))

    hover_overlay = pygame.Surface((FELD_GROESSE, FELD_GROESSE), pygame.SRCALPHA)
    hover_overlay.fill((255, 255, 255, 30))

    return {
        "schach_glow": schach_glow,
        "zug_punkt": zug_punkt,
        "zug_ring": zug_ring,
        "letzter_zug": letzter_zug_overlay,
        "auswahl": auswahl_overlay,
        "hover": hover_overlay,
    }


def erstelle_mini_figuren(figuren_surfaces: dict[str, pygame.Surface]) -> dict[str, pygame.Surface]:
    """Erstellt verkleinerte Figuren-Icons (22x22) für geschlagene Figuren in der Sidebar."""
    return {
        sym: pygame.transform.smoothscale(surf, (22, 22))
        for sym, surf in figuren_surfaces.items()
    }


def erstelle_start_hintergrund() -> pygame.Surface:
    """Erzeugt einen dezenten Schachbrett-Hintergrund mit Vignette für die Startseite."""
    bg = pygame.Surface((BREITE, HOEHE))
    bg.fill(FARBE_HINTERGRUND)

    kachel = 64
    for y in range(0, HOEHE, kachel):
        for x in range(0, BREITE, kachel):
            if ((x // kachel) + (y // kachel)) % 2 == 0:
                pygame.draw.rect(bg, (29, 32, 38), (x, y, kachel, kachel))

    # Weiche Vignette zum Abdunkeln der Ränder
    vignette = pygame.Surface((BREITE, HOEHE), pygame.SRCALPHA)
    mitte = (BREITE // 2, HOEHE // 2)
    max_dist = int((BREITE ** 2 + HOEHE ** 2) ** 0.5 / 2)
    for r in range(max_dist, 120, -18):
        t = (r - 120) / (max_dist - 120)
        alpha = int(170 * (t ** 1.4))
        pygame.draw.circle(vignette, (14, 15, 18, min(195, alpha)), mitte, r, width=22)
    bg.blit(vignette, (0, 0))
    return bg


# --- HILFSFUNKTIONEN FÜR SPIELZUSTAND ---
def berechne_geschlagene_und_vorteil(board: chess.Board) -> tuple[list[str], list[str], int]:
    """
    Liefert (von_weiss_geschlagene_schwarze, von_schwarz_geschlagene_weisse, material_vorteil_weiss).
    """
    order = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT, chess.PAWN]
    von_weiss_geschlagen: list[str] = []
    von_schwarz_geschlagen: list[str] = []
    weiss_punkte = 0
    schwarz_punkte = 0

    for typ in order:
        w_cnt = len(board.pieces(typ, chess.WHITE))
        b_cnt = len(board.pieces(typ, chess.BLACK))
        weiss_punkte += w_cnt * FIGUR_WERTE[typ]
        schwarz_punkte += b_cnt * FIGUR_WERTE[typ]

        sym = chess.piece_symbol(typ)
        von_weiss_geschlagen.extend([sym.lower()] * max(0, START_ANZAHL[typ] - b_cnt))
        von_schwarz_geschlagen.extend([sym.upper()] * max(0, START_ANZAHL[typ] - w_cnt))

    return von_weiss_geschlagen, von_schwarz_geschlagen, weiss_punkte - schwarz_punkte


def erzeuge_san_liste(board: chess.Board) -> list[str]:
    """Erzeugt SAN-Notation für alle Züge in board.move_stack."""
    temp = chess.Board()
    san_liste: list[str] = []
    for zug in board.move_stack:
        san_liste.append(temp.san(zug))
        temp.push(zug)
    return san_liste


def feld_zu_pixel(feld: int) -> tuple[int, int]:
    spalte = chess.square_file(feld)
    zeile = 7 - chess.square_rank(feld)
    return (BRETT_RAND + spalte * FELD_GROESSE, BRETT_RAND + zeile * FELD_GROESSE)


def pixel_zu_feld(pos: tuple[int, int]) -> int | None:
    x, y = pos
    if not BRETT_RECT.collidepoint(x, y):
        return None
    spalte = (x - BRETT_RAND) // FELD_GROESSE
    zeile = (y - BRETT_RAND) // FELD_GROESSE
    return chess.square(spalte, 7 - zeile)


# --- GRAFIK-FUNKTIONEN ---
def zeichne_brett(
    fenster: pygame.Surface,
    board: chess.Board,
    ausgewaehlt: int | None,
    maus_pos: tuple[int, int],
    interaktiv: bool,
    schriften: dict,
    figuren_surfaces: dict[str, pygame.Surface],
    effekte: dict[str, pygame.Surface],
    anim_zug: dict | None,
) -> None:
    # Äußerer Holz-/Schieferrahmen mit feiner Kante
    rahmen_rect = pygame.Rect(
        BRETT_RAND - 8, BRETT_RAND - 8, BRETT_GROESSE + 16, BRETT_GROESSE + 16
    )
    pygame.draw.rect(fenster, FARBE_RAHMEN, rahmen_rect, border_radius=8)
    pygame.draw.rect(fenster, FARBE_RAHMEN_HELL, rahmen_rect, width=2, border_radius=8)
    pygame.draw.rect(fenster, FARBE_RAHMEN_DUNKEL, BRETT_RECT.inflate(2, 2), width=2)

    letzter_zug = board.peek() if board.move_stack else None
    koenig_im_schach = board.king(board.turn) if board.is_check() else None
    hover_feld = pixel_zu_feld(maus_pos) if interaktiv else None

    erlaubte_ziele: dict[int, bool] = {}
    if ausgewaehlt is not None:
        for zug in board.legal_moves:
            if zug.from_square == ausgewaehlt:
                erlaubte_ziele[zug.to_square] = board.is_capture(zug)

    # 1. Felder, Highlights und Koordinaten
    koordinaten_schrift = schriften["koordinaten"]
    for zeile in range(8):
        for spalte in range(8):
            feld = chess.square(spalte, 7 - zeile)
            px = BRETT_RAND + spalte * FELD_GROESSE
            py = BRETT_RAND + zeile * FELD_GROESSE
            rect = pygame.Rect(px, py, FELD_GROESSE, FELD_GROESSE)

            ist_hell = (zeile + spalte) % 2 == 0
            basis_farbe = FARBE_FELD_HELL if ist_hell else FARBE_FELD_DUNKEL
            pygame.draw.rect(fenster, basis_farbe, rect)

            if letzter_zug and feld in (letzter_zug.from_square, letzter_zug.to_square):
                fenster.blit(effekte["letzter_zug"], (px, py))

            if feld == ausgewaehlt:
                fenster.blit(effekte["auswahl"], (px, py))
                pygame.draw.rect(fenster, FARBE_AKZENT_HELL, rect, width=2)
            elif feld == hover_feld and (
                feld in erlaubte_ziele or board.color_at(feld) == board.turn
            ):
                fenster.blit(effekte["hover"], (px, py))

            if feld == koenig_im_schach:
                fenster.blit(effekte["schach_glow"], (px, py))

            # Koordinaten (a-h unten rechts, 1-8 oben links)
            text_farbe = FARBE_FELD_DUNKEL if ist_hell else FARBE_FELD_HELL
            if zeile == 7:
                lbl = koordinaten_schrift.render(chr(ord("a") + spalte), True, text_farbe)
                fenster.blit(lbl, (rect.right - lbl.get_width() - 4, rect.bottom - lbl.get_height() - 2))
            if spalte == 0:
                lbl = koordinaten_schrift.render(str(8 - zeile), True, text_farbe)
                fenster.blit(lbl, (rect.left + 4, rect.top + 2))

    # 2. Zug-Indikatoren unter/über leeren Feldern
    for ziel_feld, ist_schlagzug in erlaubte_ziele.items():
        px, py = feld_zu_pixel(ziel_feld)
        if not ist_schlagzug:
            fenster.blit(effekte["zug_punkt"], (px, py))

    # 3. Statische Figuren zeichnen (Zielfeld der laufenden Animation auslassen)
    anim_ziel = anim_zug["to"] if anim_zug is not None else None
    for feld in chess.SQUARES:
        if feld == anim_ziel:
            continue
        figur = board.piece_at(feld)
        if figur:
            fenster.blit(figuren_surfaces[figur.symbol()], feld_zu_pixel(feld))

    # 4. Laufende Zug-Animation (Cubic Ease-Out)
    if anim_zug is not None:
        t = (pygame.time.get_ticks() - anim_zug["start"]) / anim_zug["dauer"]
        t = max(0.0, min(1.0, t))
        ease = 1.0 - (1.0 - t) ** 3
        sx, sy = feld_zu_pixel(anim_zug["from"])
        ex, ey = feld_zu_pixel(anim_zug["to"])
        ax = int(sx + (ex - sx) * ease)
        ay = int(sy + (ey - sy) * ease)
        fenster.blit(figuren_surfaces[anim_zug["symbol"]], (ax, ay))

    # 5. Schlag-Ringe über den gegnerischen Figuren zeichnen
    for ziel_feld, ist_schlagzug in erlaubte_ziele.items():
        if ist_schlagzug:
            fenster.blit(effekte["zug_ring"], feld_zu_pixel(ziel_feld))


def zeichne_klein_button(
    fenster: pygame.Surface,
    rect: pygame.Rect,
    label: str,
    maus_pos: tuple[int, int],
    schriften: dict,
    aktiv: bool = False,
) -> None:
    hover = rect.collidepoint(maus_pos)
    if aktiv:
        bg = (64, 84, 42) if not hover else (78, 102, 50)
        rand = FARBE_AKZENT
    else:
        bg = FARBE_KARTE_HOVER if hover else FARBE_KARTE
        rand = FARBE_AKZENT if hover else FARBE_KARTE_RAND

    pygame.draw.rect(fenster, bg, rect, border_radius=8)
    pygame.draw.rect(fenster, rand, rect, width=1, border_radius=8)
    txt = schriften["klein"].render(label, True, FARBE_TEXT_HELL)
    fenster.blit(txt, txt.get_rect(center=rect.center))


def zeichne_sidebar(
    fenster: pygame.Surface,
    board: chess.Board,
    zustand: str,
    engine_aktiv: bool,
    bot_denkt: bool,
    san_liste: list[str],
    maus_pos: tuple[int, int],
    schriften: dict,
    mini_figuren: dict[str, pygame.Surface],
) -> None:
    x = _SB_X
    w = _SB_W

    # 1. Status-Karte (Modus + Wer ist am Zug)
    status_rect = pygame.Rect(x, BRETT_RAND, w, 108)
    pygame.draw.rect(fenster, FARBE_KARTE, status_rect, border_radius=10)
    pygame.draw.rect(fenster, FARBE_KARTE_RAND, status_rect, width=1, border_radius=10)

    modus_txt = "Gegen Schach-Bot" if zustand == "bot" else "Lokal (2 Spieler)"
    modus_surf = schriften["winzig"].render(modus_txt.upper(), True, FARBE_TEXT_GEDIMMT)
    fenster.blit(modus_surf, (x + 14, BRETT_RAND + 12))

    # Zug-Indikator mit Farbpunkt
    am_zug_weiss = board.turn == chess.WHITE
    kreis_farbe = (248, 245, 236) if am_zug_weiss else (38, 38, 42)
    kreis_rand = (70, 70, 70) if am_zug_weiss else (175, 175, 185)
    pygame.draw.circle(fenster, kreis_farbe, (x + 25, BRETT_RAND + 50), 10)
    pygame.draw.circle(fenster, kreis_rand, (x + 25, BRETT_RAND + 50), 10, width=2)

    if bot_denkt:
        zug_label = "Bot überlegt ..."
    elif board.is_game_over():
        zug_label = "Partie beendet"
    else:
        zug_label = "Weiß am Zug" if am_zug_weiss else "Schwarz am Zug"

    zug_surf = schriften["info"].render(zug_label, True, FARBE_TEXT_HELL)
    fenster.blit(zug_surf, (x + 44, BRETT_RAND + 40))

    # Schach-Badge oder Halbzug-Anzeige
    if board.is_check() and not board.is_game_over():
        badge = pygame.Rect(x + 14, BRETT_RAND + 73, 84, 22)
        pygame.draw.rect(fenster, (130, 34, 34), badge, border_radius=6)
        pygame.draw.rect(fenster, FARBE_WARNUNG, badge, width=1, border_radius=6)
        b_txt = schriften["winzig"].render("SCHACH!", True, (255, 230, 230))
        fenster.blit(b_txt, b_txt.get_rect(center=badge.center))
    else:
        zug_nr = schriften["klein"].render(f"Zug {board.fullmove_number}", True, FARBE_TEXT_GEDIMMT)
        fenster.blit(zug_nr, (x + 14, BRETT_RAND + 74))

    # 2. Geschlagene Figuren & Materialvorteil
    von_w, von_b, diff = berechne_geschlagene_und_vorteil(board)
    mat_rect = pygame.Rect(x, BRETT_RAND + 120, w, 92)
    pygame.draw.rect(fenster, FARBE_KARTE, mat_rect, border_radius=10)
    pygame.draw.rect(fenster, FARBE_KARTE_RAND, mat_rect, width=1, border_radius=10)

    def zeichne_reihe(y_pos: int, titel: str, icons: list[str], vorteil: int) -> None:
        lbl = schriften["winzig"].render(titel, True, FARBE_TEXT_GEDIMMT)
        fenster.blit(lbl, (x + 12, y_pos))
        if vorteil > 0:
            v_lbl = schriften["winzig"].render(f"+{vorteil}", True, FARBE_AKZENT_HELL)
            fenster.blit(v_lbl, (x + w - v_lbl.get_width() - 12, y_pos))
        ix = x + 10
        for idx, sym in enumerate(icons[:9]):
            fenster.blit(mini_figuren[sym], (ix + idx * 17, y_pos + 15))
        if len(icons) > 9:
            rest = schriften["winzig"].render(f"+{len(icons) - 9}", True, FARBE_TEXT_GEDIMMT)
            fenster.blit(rest, (ix + 9 * 17 + 4, y_pos + 19))

    zeichne_reihe(BRETT_RAND + 128, "WEISS", von_w, diff)
    zeichne_reihe(BRETT_RAND + 168, "SCHWARZ", von_b, -diff)

    # 3. Zugverlauf (letzte Züge)
    hist_top = BRETT_RAND + 224
    hist_h = HOEHE - hist_top - 118
    hist_rect = pygame.Rect(x, hist_top, w, hist_h)
    pygame.draw.rect(fenster, FARBE_KARTE, hist_rect, border_radius=10)
    pygame.draw.rect(fenster, FARBE_KARTE_RAND, hist_rect, width=1, border_radius=10)

    hist_titel = schriften["winzig"].render("ZUGVERLAUF", True, FARBE_TEXT_GEDIMMT)
    fenster.blit(hist_titel, (x + 12, hist_top + 10))

    if not san_liste:
        leer = schriften["klein"].render("Noch keine Züge", True, FARBE_TEXT_GEDIMMT)
        fenster.blit(leer, (x + 12, hist_top + 38))
    else:
        paare = []
        for i in range(0, len(san_liste), 2):
            nr = i // 2 + 1
            w_san = san_liste[i]
            b_san = san_liste[i + 1] if i + 1 < len(san_liste) else ""
            paare.append((nr, w_san, b_san))

        max_zeilen = max(1, (hist_h - 42) // 24)
        sichtbar = paare[-max_zeilen:]
        for idx, (nr, w_san, b_san) in enumerate(sichtbar):
            zy = hist_top + 34 + idx * 24
            if idx % 2 == 0:
                pygame.draw.rect(fenster, (40, 44, 52), (x + 8, zy - 2, w - 16, 22), border_radius=4)
            nr_s = schriften["zuege"].render(f"{nr:>2}.", True, FARBE_TEXT_GEDIMMT)
            w_s = schriften["zuege"].render(w_san, True, FARBE_TEXT_HELL)
            b_s = schriften["zuege"].render(b_san, True, (210, 215, 225))
            fenster.blit(nr_s, (x + 14, zy + 1))
            fenster.blit(w_s, (x + 50, zy + 1))
            fenster.blit(b_s, (x + 132, zy + 1))

    # 4. Aktions-Buttons
    zeichne_klein_button(fenster, BTN_SB_UNDO, "Zurück [Z]", maus_pos, schriften)
    zeichne_klein_button(fenster, BTN_SB_RESET, "Neu [R]", maus_pos, schriften)
    zeichne_klein_button(fenster, BTN_SB_BOT, "Bot [E]", maus_pos, schriften, aktiv=engine_aktiv)
    zeichne_klein_button(fenster, BTN_SB_MENU, "Menü [ESC]", maus_pos, schriften)


def zeichne_eval_bar(
    fenster: pygame.Surface,
    anzeige_prob: float,
    score_white: int,
    mate_in: int | None,
    maus_pos: tuple[int, int],
    schriften: dict,
) -> None:
    """Zeichnet den vertikalen Chess.com-ähnlichen Bewertungsbalken rechts neben dem Brett."""
    rect = EVAL_BAR_RECT
    prob = max(0.0, min(1.0, anzeige_prob))

    # Schwarzer Hintergrund (oben)
    pygame.draw.rect(fenster, (38, 40, 46), rect, border_radius=5)

    # Weißer Anteil (unten)
    weiss_h = int(round(rect.height * prob))
    if weiss_h > 0:
        weiss_rect = pygame.Rect(rect.x, rect.bottom - weiss_h, rect.width, weiss_h)
        top_r = 5 if weiss_h >= rect.height - 2 else 0
        pygame.draw.rect(
            fenster,
            (244, 241, 234),
            weiss_rect,
            border_top_left_radius=top_r,
            border_top_right_radius=top_r,
            border_bottom_left_radius=5,
            border_bottom_right_radius=5,
        )

    # Dezente 50%-Markierung in der Mitte
    mitte_y = rect.centery
    pygame.draw.line(
        fenster,
        (132, 136, 145),
        (rect.x + 2, mitte_y),
        (rect.right - 3, mitte_y),
        1,
    )

    # Äußerer Rahmen
    pygame.draw.rect(fenster, (74, 78, 88), rect, width=1, border_radius=5)

    # Bewertungstext (Pawns oder Matt)
    if mate_in is not None:
        eval_txt = "#" if mate_in == 0 else f"M{mate_in}"
    else:
        bauern = abs(score_white) / 100.0
        eval_txt = "0.0" if bauern < 0.05 else f"{bauern:.1f}"

    weiss_vorne = (score_white > 0) if mate_in is not None else (score_white >= 0)
    if weiss_vorne:
        txt_farbe = (30, 32, 36) if prob >= 0.08 else (238, 240, 244)
        txt_pos = (rect.centerx, rect.bottom - 11)
    else:
        txt_farbe = (238, 240, 244) if prob <= 0.92 else (30, 32, 36)
        txt_pos = (rect.centerx, rect.top + 11)

    lbl = schriften["eval"].render(eval_txt, True, txt_farbe)
    fenster.blit(lbl, lbl.get_rect(center=txt_pos))

    # Hover-Tooltip mit exakter Gewinnwahrscheinlichkeit
    if rect.collidepoint(maus_pos):
        w_pct = int(round(prob * 100))
        b_pct = 100 - w_pct
        if mate_in is not None:
            zusatz = "Matt!" if mate_in == 0 else f"Matt in {mate_in}"
        else:
            vorz = "+" if score_white >= 0 else "-"
            zusatz = f"{vorz}{abs(score_white) / 100.0:.2f}"
        tip_text = f"Weiß {w_pct}% • Schwarz {b_pct}% ({zusatz})"
        tip_surf = schriften["klein"].render(tip_text, True, FARBE_TEXT_HELL)
        tip_w = tip_surf.get_width() + 18
        tip_h = 28
        tip_x = rect.x - tip_w - 8
        tip_y = max(BRETT_RAND, min(maus_pos[1] - tip_h // 2, rect.bottom - tip_h))
        tip_rect = pygame.Rect(tip_x, tip_y, tip_w, tip_h)
        pygame.draw.rect(fenster, (28, 30, 36), tip_rect, border_radius=6)
        pygame.draw.rect(fenster, FARBE_AKZENT, tip_rect, width=1, border_radius=6)
        fenster.blit(tip_surf, tip_surf.get_rect(center=tip_rect.center))


def ermittle_game_over_text(board: chess.Board) -> tuple[str, str]:
    """Gibt Haupttitel und Erklärung für den Spielende-Dialog zurück."""
    if board.is_checkmate():
        gewinner = "Schwarz" if board.turn == chess.WHITE else "Weiß"
        return "Schachmatt!", f"{gewinner} gewinnt die Partie"
    if board.is_stalemate():
        return "Patt!", "Unentschieden (Remis)"
    if board.is_insufficient_material():
        return "Remis!", "Ungenügend Material zum Mattsetzen"
    if board.is_fifty_moves():
        return "Remis!", "50-Züge-Regel erreicht"
    if board.is_repetition(3):
        return "Remis!", "Dreifache Stellungswiederholung"
    return "Partie beendet", f"Ergebnis: {board.result()}"


def zeichne_game_over_banner(
    fenster: pygame.Surface,
    board: chess.Board,
    maus_pos: tuple[int, int],
    schriften: dict,
) -> None:
    """Zeigt einen modernen Spielende-Dialog zentriert über dem Brett."""
    titel, untertitel = ermittle_game_over_text(board)

    # Brett leicht abdunkeln
    overlay = pygame.Surface((BRETT_GROESSE, BRETT_GROESSE), pygame.SRCALPHA)
    overlay.fill((12, 14, 18, 135))
    fenster.blit(overlay, BRETT_RECT.topleft)

    kasten_b, kasten_h = 380, 178
    rect = pygame.Rect(0, 0, kasten_b, kasten_h)
    rect.center = (BRETT_MITTE_X, BRETT_MITTE_Y)

    # Schlagschatten
    schatten = pygame.Surface((kasten_b + 16, kasten_h + 16), pygame.SRCALPHA)
    pygame.draw.rect(schatten, (0, 0, 0, 110), schatten.get_rect(), border_radius=16)
    fenster.blit(schatten, (rect.x - 8, rect.y - 4))

    pygame.draw.rect(fenster, (32, 35, 42), rect, border_radius=14)
    pygame.draw.rect(fenster, FARBE_AKZENT, rect, width=2, border_radius=14)

    titel_surf = schriften["banner"].render(titel, True, FARBE_TEXT_HELL)
    sub_surf = schriften["klein"].render(untertitel, True, FARBE_TEXT_GEDIMMT)
    fenster.blit(titel_surf, titel_surf.get_rect(center=(BRETT_MITTE_X, rect.y + 38)))
    fenster.blit(sub_surf, sub_surf.get_rect(center=(BRETT_MITTE_X, rect.y + 72)))

    zeichne_klein_button(fenster, BTN_GO_NEU, "Nochmal [R]", maus_pos, schriften, aktiv=True)
    zeichne_klein_button(fenster, BTN_GO_MENU, "Menü [ESC]", maus_pos, schriften)


def zeichne_start_button(
    fenster: pygame.Surface,
    rect: pygame.Rect,
    titel: str,
    untertitel: str,
    icon_surf: pygame.Surface,
    maus_pos: tuple[int, int],
    schriften: dict,
) -> None:
    """Zeichnet eine moderne Modus-Karte mit Icon, Schatten und Hover-Effekt."""
    ist_hover = rect.collidepoint(maus_pos)
    hintergrund = FARBE_KARTE_HOVER if ist_hover else FARBE_KARTE
    rahmen = FARBE_AKZENT if ist_hover else FARBE_KARTE_RAND

    # Dezenter Schatten
    schatten = pygame.Surface((rect.width + 10, rect.height + 10), pygame.SRCALPHA)
    pygame.draw.rect(schatten, (0, 0, 0, 85), schatten.get_rect(), border_radius=14)
    fenster.blit(schatten, (rect.x - 5, rect.y - 2))

    pygame.draw.rect(fenster, hintergrund, rect, border_radius=12)
    pygame.draw.rect(fenster, rahmen, rect, width=2, border_radius=12)

    # Linkes Icon-Feld
    icon_box = pygame.Rect(rect.x + 14, rect.y + 14, 64, 64)
    pygame.draw.rect(fenster, (28, 30, 36), icon_box, border_radius=10)
    icon_klein = pygame.transform.smoothscale(icon_surf, (52, 52))
    fenster.blit(icon_klein, icon_klein.get_rect(center=icon_box.center))

    titel_surf = schriften["karte_titel"].render(titel, True, FARBE_TEXT_HELL)
    sub_surf = schriften["klein"].render(untertitel, True, FARBE_TEXT_GEDIMMT)
    fenster.blit(titel_surf, (rect.x + 94, rect.y + 20))
    fenster.blit(sub_surf, (rect.x + 94, rect.y + 50))


def zeichne_startseite(
    fenster: pygame.Surface,
    hintergrund: pygame.Surface,
    schriften: dict,
    figuren_surfaces: dict[str, pygame.Surface],
    maus_pos: tuple[int, int],
) -> None:
    """Zeichnet die Startseite zur Auswahl des Spielmodus."""
    fenster.blit(hintergrund, (0, 0))

    # Emblem (weißer König) über dem Titel
    koenig_icon = pygame.transform.smoothscale(figuren_surfaces["K"], (72, 72))
    fenster.blit(koenig_icon, koenig_icon.get_rect(center=(BREITE // 2, 118)))

    titel_surf = schriften["titel"].render("SCHACH", True, FARBE_FELD_HELL)
    sub_surf = schriften["untertitel"].render(
        "Klassisches Brettspiel mit Alpha-Beta Engine", True, FARBE_TEXT_GEDIMMT
    )
    fenster.blit(titel_surf, titel_surf.get_rect(center=(BREITE // 2, 182)))
    fenster.blit(sub_surf, sub_surf.get_rect(center=(BREITE // 2, 224)))

    zeichne_start_button(
        fenster,
        BTN_FREUND_RECT,
        "Mit Freund spielen",
        "Lokal auf einem Gerät gegeneinander",
        figuren_surfaces["N"],
        maus_pos,
        schriften,
    )
    zeichne_start_button(
        fenster,
        BTN_BOT_RECT,
        "Gegen Bot spielen",
        "Herausforderung gegen die Schach-Engine",
        figuren_surfaces["k"],
        maus_pos,
        schriften,
    )

    hinweis = schriften["klein"].render(
        "Tastatur im Spiel:  [Z] Zurück   •   [R] Neustart   •   [E] Bot An/Aus   •   [ESC] Menü",
        True,
        FARBE_TEXT_GEDIMMT,
    )
    fenster.blit(hinweis, hinweis.get_rect(center=(BREITE // 2, HOEHE - 40)))


# --- HAUPTSCHLEIFE ---
def main() -> None:
    pygame.init()
    fenster = pygame.display.set_mode((BREITE, HOEHE))
    schriften = erstelle_schriften()
    figuren_surfaces = erstelle_figuren_surfaces(FELD_GROESSE)
    mini_figuren = erstelle_mini_figuren(figuren_surfaces)
    effekte = erstelle_effekt_surfaces()
    start_hintergrund = erstelle_start_hintergrund()

    board = chess.Board()
    ausgewaehlt: int | None = None
    zustand = "start"  # "start", "freund", "bot"
    engine_aktiv = False
    anim_zug: dict | None = None
    san_cache: list[str] = []
    san_cache_len = -1
    uhr = pygame.time.Clock()
    laeuft = True

    bot_denkt = False
    bot_request_id = 0
    bot_ergebnisse: queue.SimpleQueue[tuple[int, chess.Move | None]] = queue.SimpleQueue()
    bot_lock = threading.Lock()

    eval_request_id = 0
    eval_ergebnisse: queue.SimpleQueue[tuple[int, int, int | None, float]] = queue.SimpleQueue()
    eval_lock = threading.Lock()
    eval_letzter_key: tuple[int, str] | None = None
    eval_score_white = 0
    eval_mate_in: int | None = None
    eval_ziel_prob = 0.5
    eval_anzeige_prob = 0.5

    def aktualisiere_san_cache() -> None:
        nonlocal san_cache, san_cache_len
        if len(board.move_stack) != san_cache_len:
            san_cache = erzeuge_san_liste(board)
            san_cache_len = len(board.move_stack)

    def aktualisiere_titel() -> None:
        if zustand == "start":
            titel = "Schach - Startseite"
        elif zustand == "bot":
            modus = "Gegen Bot (Schwarz)" if engine_aktiv else "Bot pausiert (Lokal)"
            titel = f"Schach - {modus}"
        else:
            modus = "Engine aktiv (Schwarz)" if engine_aktiv else "Freund (Lokal)"
            titel = f"Schach - {modus}"
        pygame.display.set_caption(titel)

    def starte_animation(zug: chess.Move, symbol: str) -> None:
        nonlocal anim_zug
        anim_zug = {
            "from": zug.from_square,
            "to": zug.to_square,
            "symbol": symbol,
            "start": pygame.time.get_ticks(),
            "dauer": 140,
        }

    def brich_bot_suche_ab() -> None:
        nonlocal bot_denkt, bot_request_id
        bot_request_id += 1
        bot_denkt = False

    def starte_bot_suche() -> None:
        nonlocal bot_denkt, bot_request_id
        bot_request_id += 1
        req_id = bot_request_id
        board_kopie = board.copy()
        bot_denkt = True

        def _worker() -> None:
            with bot_lock:
                zug = meine_engine_zug(board_kopie)
            bot_ergebnisse.put((req_id, zug))

        threading.Thread(target=_worker, daemon=True).start()

    def starte_eval_suche() -> None:
        nonlocal eval_request_id, eval_letzter_key
        eval_letzter_key = (len(board.move_stack), board.fen())
        eval_request_id += 1
        req_id = eval_request_id
        board_kopie = board.copy()

        def _eval_worker() -> None:
            with eval_lock:
                score_w, mate_in, prob_w = bewerte_stellung(board_kopie)
            eval_ergebnisse.put((req_id, score_w, mate_in, prob_w))

        threading.Thread(target=_eval_worker, daemon=True).start()

    def fuehre_szene_zeichen() -> None:
        aktualisiere_san_cache()
        fenster.fill(FARBE_HINTERGRUND)
        maus_pos = pygame.mouse.get_pos()
        interaktiv = not board.is_game_over() and not (engine_aktiv and board.turn == chess.BLACK)
        zeichne_brett(
            fenster, board, ausgewaehlt, maus_pos, interaktiv,
            schriften, figuren_surfaces, effekte, anim_zug,
        )
        zeichne_eval_bar(
            fenster, eval_anzeige_prob, eval_score_white, eval_mate_in, maus_pos, schriften
        )
        zeichne_sidebar(
            fenster, board, zustand, engine_aktiv, bot_denkt,
            san_cache, maus_pos, schriften, mini_figuren,
        )
        if board.is_game_over():
            zeichne_game_over_banner(fenster, board, maus_pos, schriften)

    def mache_undo() -> None:
        nonlocal ausgewaehlt, anim_zug
        brich_bot_suche_ab()
        if engine_aktiv:
            if board.turn == chess.WHITE and len(board.move_stack) >= 2:
                board.pop()
                board.pop()
            elif board.turn == chess.BLACK and len(board.move_stack) >= 1:
                board.pop()
        elif len(board.move_stack) >= 1:
            board.pop()
        ausgewaehlt = None
        anim_zug = None

    def mache_reset() -> None:
        nonlocal ausgewaehlt, anim_zug
        brich_bot_suche_ab()
        board.reset()
        ausgewaehlt = None
        anim_zug = None

    aktualisiere_titel()

    print("=" * 64)
    print("Schachbrett erfolgreich gestartet!")
    print("Steuerung:")
    print("  - Startseite:  Freund oder Bot auswählen")
    print("  - Linksklick:  Figur auswählen & ziehen (erneuter Klick deselektiert)")
    print("  - [Z]:         Zug rückgängig machen (Undo)")
    print("  - [R]:         Brett zurücksetzen (Reset)")
    print("  - [E]:         Engine für Schwarz umschalten (An/Aus)")
    print("  - [ESC]:       Zurück zur Startseite")
    print("=" * 64)

    while laeuft:
        uhr.tick(60)
        maus_pos = pygame.mouse.get_pos()

        if anim_zug is not None:
            if pygame.time.get_ticks() - anim_zug["start"] >= anim_zug["dauer"]:
                anim_zug = None

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                laeuft = False

            elif zustand == "start":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if BTN_FREUND_RECT.collidepoint(event.pos):
                        mache_reset()
                        engine_aktiv = False
                        zustand = "freund"
                        aktualisiere_titel()
                    elif BTN_BOT_RECT.collidepoint(event.pos):
                        mache_reset()
                        engine_aktiv = True
                        zustand = "bot"
                        aktualisiere_titel()

            elif zustand in ("freund", "bot"):
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        brich_bot_suche_ab()
                        anim_zug = None
                        zustand = "start"
                        aktualisiere_titel()
                    elif event.key == pygame.K_r:
                        mache_reset()
                    elif event.key == pygame.K_e:
                        engine_aktiv = not engine_aktiv
                        if not engine_aktiv:
                            brich_bot_suche_ab()
                        aktualisiere_titel()
                    elif event.key == pygame.K_z:
                        mache_undo()

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # 1. Klick auf Game-Over-Buttons
                    if board.is_game_over():
                        if BTN_GO_NEU.collidepoint(event.pos):
                            mache_reset()
                            continue
                        if BTN_GO_MENU.collidepoint(event.pos):
                            brich_bot_suche_ab()
                            anim_zug = None
                            zustand = "start"
                            aktualisiere_titel()
                            continue

                    # 2. Klick auf Sidebar-Buttons
                    if BTN_SB_UNDO.collidepoint(event.pos):
                        mache_undo()
                        continue
                    if BTN_SB_RESET.collidepoint(event.pos):
                        mache_reset()
                        continue
                    if BTN_SB_BOT.collidepoint(event.pos):
                        engine_aktiv = not engine_aktiv
                        if not engine_aktiv:
                            brich_bot_suche_ab()
                        aktualisiere_titel()
                        continue
                    if BTN_SB_MENU.collidepoint(event.pos):
                        brich_bot_suche_ab()
                        anim_zug = None
                        zustand = "start"
                        aktualisiere_titel()
                        continue

                    # 3. Klick aufs Schachbrett
                    if not board.is_game_over() and not (engine_aktiv and board.turn == chess.BLACK):
                        geklickt = pixel_zu_feld(event.pos)
                        if geklickt is None:
                            continue

                        if ausgewaehlt is None:
                            figur = board.piece_at(geklickt)
                            if figur and figur.color == board.turn:
                                ausgewaehlt = geklickt
                        elif geklickt == ausgewaehlt:
                            ausgewaehlt = None
                        else:
                            zug = chess.Move(ausgewaehlt, geklickt)
                            if chess.Move(ausgewaehlt, geklickt, promotion=chess.QUEEN) in board.legal_moves:
                                zug = chess.Move(ausgewaehlt, geklickt, promotion=chess.QUEEN)

                            if zug in board.legal_moves:
                                gezogene_figur = board.piece_at(ausgewaehlt)
                                symbol = gezogene_figur.symbol() if gezogene_figur else "P"
                                board.push(zug)
                                ausgewaehlt = None
                                starte_animation(zug, symbol)
                            else:
                                figur = board.piece_at(geklickt)
                                if figur and figur.color == board.turn:
                                    ausgewaehlt = geklickt
                                else:
                                    ausgewaehlt = None

        # Bot-Ergebnisse verarbeiten, sobald keine Animation mehr läuft
        if anim_zug is None:
            while not bot_ergebnisse.empty():
                req_id, engine_zug = bot_ergebnisse.get_nowait()
                if req_id != bot_request_id:
                    continue
                bot_denkt = False
                if (
                    zustand in ("freund", "bot")
                    and engine_aktiv
                    and not board.is_game_over()
                    and board.turn == chess.BLACK
                    and engine_zug is not None
                    and engine_zug in board.legal_moves
                ):
                    figur = board.piece_at(engine_zug.from_square)
                    symbol = figur.symbol() if figur else "p"
                    board.push(engine_zug)
                    starte_animation(engine_zug, symbol)

            if (
                anim_zug is None
                and zustand in ("freund", "bot")
                and engine_aktiv
                and not bot_denkt
                and not board.is_game_over()
                and board.turn == chess.BLACK
            ):
                starte_bot_suche()

        # Stellungsbewertung im Hintergrund aktualisieren & Balken sanft animieren
        if zustand in ("freund", "bot"):
            aktueller_key = (len(board.move_stack), board.fen())
            if aktueller_key != eval_letzter_key:
                starte_eval_suche()

            while not eval_ergebnisse.empty():
                req_id, score_w, mate_in, prob_w = eval_ergebnisse.get_nowait()
                if req_id != eval_request_id:
                    continue
                eval_score_white = score_w
                eval_mate_in = mate_in
                eval_ziel_prob = prob_w

            diff_prob = eval_ziel_prob - eval_anzeige_prob
            if abs(diff_prob) < 0.001:
                eval_anzeige_prob = eval_ziel_prob
            else:
                eval_anzeige_prob += diff_prob * 0.18

        if zustand == "start":
            zeichne_startseite(fenster, start_hintergrund, schriften, figuren_surfaces, maus_pos)
        else:
            fuehre_szene_zeichen()

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
