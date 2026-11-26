"""
Schachbrett & Engine-Testumgebung
Entwickelt mit Pygame und python-chess.

Steuerung:
  - Startseite:              Spielmodus wählen (Freund oder Bot)
  - Linksklick:              Figur auswählen / Ziel wählen (erneuter Klick auf Auswahl deselektiert)
  - [Z]:                     Zug rückgängig machen (Undo)
  - [R]:                     Partie zurücksetzen (Reset)
  - [E]:                     Engine-Modus für Schwarz ein-/ausschalten
  - [ESC]:                   Zurück zur Startseite
"""

import chess
import pygame

# --- KONFIGURATION & FARBEN ---
BREITE, HOEHE = 640, 640
FELD_GROESSE = BREITE // 8

# Palette (angelehnt an moderne Schach-Plattformen wie Lichess)
FARBE_FELD_HELL = (240, 217, 181)
FARBE_FELD_DUNKEL = (181, 136, 99)
FARBE_AUSWAHL = (186, 202, 68)          # Aktuell ausgewählte Figur
FARBE_LETZTER_ZUG = (205, 210, 106)     # Start- und Zielfeld des letzten Zugs
FARBE_SCHACH = (225, 65, 65)            # König im Schach
FARBE_PUNKT = (100, 110, 64)            # Möglicher Zug (leeres Feld)
FARBE_SCHLAGEN = (220, 65, 65)          # Schlagbarer Gegner (Ring)

FARBE_WEISS_FIGUR = (250, 250, 250)
FARBE_WEISS_KONTUR = (35, 35, 35)
FARBE_SCHWARZ_FIGUR = (30, 30, 30)
FARBE_SCHWARZ_KONTUR = (195, 195, 195)

# UI-Farben für Startseite und Platzhalter
FARBE_HINTERGRUND = (28, 28, 28)
FARBE_KARTE = (42, 42, 42)
FARBE_KARTE_HOVER = (58, 58, 58)
FARBE_TEXT_HELL = (240, 240, 240)
FARBE_TEXT_GEDIMMT = (175, 175, 175)

# Button-Geometrie (Startseite & Platzhalter)
BTN_FREUND_RECT = pygame.Rect((BREITE - 340) // 2, 245, 340, 88)
BTN_BOT_RECT = pygame.Rect((BREITE - 340) // 2, 355, 340, 88)
BTN_ZURUECK_RECT = pygame.Rect((BREITE - 260) // 2, 380, 260, 52)

# Solide Unicode-Figuren für konsistente Füllung beider Farben
FIGUREN_UNICODE = {
    "P": "♟", "N": "♞", "B": "♝", "R": "♜", "Q": "♛", "K": "♚",
    "p": "♟", "n": "♞", "b": "♝", "r": "♜", "q": "♛", "k": "♚",
}

# Fallback (SAN-Buchstaben), falls eine Plattform keine Unicode-Schachsymbole unterstützt
FIGUREN_FALLBACK = {
    "P": "P", "N": "N", "B": "B", "R": "R", "Q": "Q", "K": "K",
    "p": "P", "n": "N", "b": "B", "r": "R", "q": "Q", "k": "K",
}


# --- ENGINE-SCHNITTSTELLE ---
def meine_engine_zug(board: chess.Board) -> chess.Move | None:
    """
    Hier kommt deine eigene Schach-Engine / Bewertungsfunktion rein!

    Rückgabe:
      - Ein gültiger chess.Move (wenn Schwarz dran ist)
      - None (falls du beide Seiten manuell spielen möchtest)

    Beispiel für Zufallszüge (zum schnellen Testen):
        import random
        return random.choice(list(board.legal_moves))
    """
    return None


# --- RESSOURCEN-VERWALTUNG ---
def erstelle_schriften():
    """Initialisiert passende Schriftarten für Figuren, Text und Koordinaten."""
    kandidaten = ["segoeuisymbol", "segoeuiemoji", "dejavusans", "arial"]
    verfuegbar = pygame.font.get_fonts()

    font_name = None
    for k in kandidaten:
        if k in verfuegbar:
            font_name = k
            break

    haupt_schrift = pygame.font.SysFont(font_name, int(FELD_GROESSE * 0.76))
    titel_schrift = pygame.font.SysFont("arial", 42, bold=True)
    info_schrift = pygame.font.SysFont("arial", 19, bold=True)
    klein_schrift = pygame.font.SysFont("arial", 15)
    banner_schrift = pygame.font.SysFont("arial", 28, bold=True)
    koordinaten_schrift = pygame.font.SysFont("arial", 12, bold=True)

    # Prüfen, ob Glyphen gerendert werden können
    test_surf = haupt_schrift.render(FIGUREN_UNICODE["P"], True, (0, 0, 0))
    benutze_fallback = test_surf.get_width() <= 2

    return {
        "haupt": haupt_schrift,
        "titel": titel_schrift,
        "info": info_schrift,
        "klein": klein_schrift,
        "banner": banner_schrift,
        "koordinaten": koordinaten_schrift,
        "fallback": benutze_fallback,
    }


def pre_render_figuren(schriften) -> dict[str, pygame.Surface]:
    """
    Rendert alle Figuren einmalig mit sauberer Kontur in transparente Surfaces vor.
    Verhindert tausende Render-Aufrufe pro Sekunde in der Hauptschleife.
    """
    schrift = schriften["haupt"]
    benutze_fallback = schriften["fallback"]
    quellen = FIGUREN_FALLBACK if benutze_fallback else FIGUREN_UNICODE

    surfaces = {}
    offsets = [(-1, -1), (-1, 1), (1, -1), (1, 1), (0, -1), (0, 1), (-1, 0), (1, 0)]

    for symbol, zeichen in quellen.items():
        ist_weiss = symbol.isupper()
        farbe_figur = FARBE_WEISS_FIGUR if ist_weiss else FARBE_SCHWARZ_FIGUR
        farbe_kontur = FARBE_WEISS_KONTUR if ist_weiss else FARBE_SCHWARZ_KONTUR

        surf = pygame.Surface((FELD_GROESSE, FELD_GROESSE), pygame.SRCALPHA)
        center = (FELD_GROESSE // 2, FELD_GROESSE // 2)

        # Kontur rendern
        for dx, dy in offsets:
            k_surf = schrift.render(zeichen, True, farbe_kontur)
            k_rect = k_surf.get_rect(center=(center[0] + dx, center[1] + dy))
            surf.blit(k_surf, k_rect)

        # Kernfigur rendern
        f_surf = schrift.render(zeichen, True, farbe_figur)
        f_rect = f_surf.get_rect(center=center)
        surf.blit(f_surf, f_rect)

        surfaces[symbol] = surf

    return surfaces


# --- GRAFIK-FUNKTIONEN ---
def zeichne_brett(fenster, board: chess.Board, ausgewaehlt: int | None,
                  schriften: dict, figuren_surfaces: dict):
    letzter_zug = board.peek() if board.move_stack else None
    koenig_im_schach = board.king(board.turn) if board.is_check() else None

    # Mögliche Züge des ausgewählten Feldes sammeln
    erlaubte_ziele = {}
    if ausgewaehlt is not None:
        for zug in board.legal_moves:
            if zug.from_square == ausgewaehlt:
                erlaubte_ziele[zug.to_square] = board.is_capture(zug)

    # 1. Felder und Koordinaten zeichnen
    koordinaten_schrift = schriften["koordinaten"]
    for zeile in range(8):
        for spalte in range(8):
            feld = chess.square(spalte, 7 - zeile)
            rect = pygame.Rect(
                spalte * FELD_GROESSE, zeile * FELD_GROESSE, FELD_GROESSE, FELD_GROESSE
            )

            ist_hell = (zeile + spalte) % 2 == 0
            basis_farbe = FARBE_FELD_HELL if ist_hell else FARBE_FELD_DUNKEL

            # Farb-Priorität: Schach > Auswahl > Letzter Zug > Grundfarbe
            if feld == koenig_im_schach:
                farbe = FARBE_SCHACH
            elif feld == ausgewaehlt:
                farbe = FARBE_AUSWAHL
            elif letzter_zug and feld in (letzter_zug.from_square, letzter_zug.to_square):
                farbe = FARBE_LETZTER_ZUG
            else:
                farbe = basis_farbe

            pygame.draw.rect(fenster, farbe, rect)

            # Koordinaten (a-h unten, 1-8 links)
            text_farbe = FARBE_FELD_DUNKEL if ist_hell else FARBE_FELD_HELL
            if zeile == 7:
                buchstabe = chr(ord('a') + spalte)
                lbl = koordinaten_schrift.render(buchstabe, True, text_farbe)
                fenster.blit(lbl, (rect.right - 12, rect.bottom - 15))
            if spalte == 0:
                nummer = str(8 - zeile)
                lbl = koordinaten_schrift.render(nummer, True, text_farbe)
                fenster.blit(lbl, (rect.left + 3, rect.top + 2))

    # 2. Figuren zeichnen (blitting der gecachten Surfaces)
    for feld in chess.SQUARES:
        figur = board.piece_at(feld)
        if figur:
            spalte = chess.square_file(feld)
            zeile = 7 - chess.square_rank(feld)
            pos = (spalte * FELD_GROESSE, zeile * FELD_GROESSE)
            fenster.blit(figuren_surfaces[figur.symbol()], pos)

    # 3. Zug-Indikatoren zeichnen
    for ziel_feld, ist_schlagzug in erlaubte_ziele.items():
        spalte = chess.square_file(ziel_feld)
        zeile = 7 - chess.square_rank(ziel_feld)
        mitte = (
            spalte * FELD_GROESSE + FELD_GROESSE // 2,
            zeile * FELD_GROESSE + FELD_GROESSE // 2,
        )

        if ist_schlagzug:
            # Roter Zielkreis um schlagbare Figur
            pygame.draw.circle(fenster, FARBE_SCHLAGEN, mitte, FELD_GROESSE // 2 - 4, 4)
        else:
            # Dezenter Punkt auf freiem Zielfeld
            pygame.draw.circle(fenster, FARBE_PUNKT, mitte, FELD_GROESSE // 6)


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


def zeichne_game_over_banner(fenster, board: chess.Board, schriften: dict):
    """Zeigt eine saubere Box bei Spielende."""
    info_schrift = schriften["info"]
    banner_schrift = schriften["banner"]
    titel, untertitel = ermittle_game_over_text(board)

    # Halbtransparenter Schattierungs-Layer
    overlay = pygame.Surface((BREITE, HOEHE), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 110))
    fenster.blit(overlay, (0, 0))

    # Dialog-Box
    kasten_b, kasten_h = 420, 135
    kasten_x = (BREITE - kasten_b) // 2
    kasten_y = (HOEHE - kasten_h) // 2
    rect = pygame.Rect(kasten_x, kasten_y, kasten_b, kasten_h)

    pygame.draw.rect(fenster, (30, 30, 30), rect, border_radius=12)
    pygame.draw.rect(fenster, FARBE_AUSWAHL, rect, width=2, border_radius=12)

    titel_surf = banner_schrift.render(titel, True, (255, 255, 255))
    sub_surf = info_schrift.render(untertitel, True, (215, 215, 215))
    tipp_surf = info_schrift.render("Drücke [R] für Neustart", True, FARBE_AUSWAHL)

    fenster.blit(titel_surf, titel_surf.get_rect(center=(BREITE // 2, kasten_y + 32)))
    fenster.blit(sub_surf, sub_surf.get_rect(center=(BREITE // 2, kasten_y + 68)))
    fenster.blit(tipp_surf, tipp_surf.get_rect(center=(BREITE // 2, kasten_y + 102)))


def zeichne_button(fenster, rect: pygame.Rect, titel: str, untertitel: str | None,
                   maus_pos: tuple[int, int], schriften: dict,
                   akzent_farbe: tuple[int, int, int] = FARBE_AUSWAHL):
    """Zeichnet einen interaktiven Button mit Hover-Effekt."""
    ist_hover = rect.collidepoint(maus_pos)
    hintergrund = FARBE_KARTE_HOVER if ist_hover else FARBE_KARTE
    rahmen = akzent_farbe if ist_hover else FARBE_FELD_DUNKEL

    pygame.draw.rect(fenster, hintergrund, rect, border_radius=12)
    pygame.draw.rect(fenster, rahmen, rect, width=2, border_radius=12)

    titel_surf = schriften["banner"].render(titel, True, FARBE_TEXT_HELL)
    if untertitel:
        sub_surf = schriften["klein"].render(untertitel, True, FARBE_TEXT_GEDIMMT)
        fenster.blit(titel_surf, titel_surf.get_rect(center=(rect.centerx, rect.centery - 13)))
        fenster.blit(sub_surf, sub_surf.get_rect(center=(rect.centerx, rect.centery + 18)))
    else:
        fenster.blit(titel_surf, titel_surf.get_rect(center=rect.center))


def zeichne_startseite(fenster, schriften: dict, maus_pos: tuple[int, int]):
    """Zeichnet die Startseite zur Auswahl des Spielmodus (ohne Schachbrett)."""
    fenster.fill(FARBE_HINTERGRUND)

    titel_surf = schriften["titel"].render("Schach", True, FARBE_FELD_HELL)
    sub_surf = schriften["info"].render("Wähle deinen Spielmodus", True, FARBE_TEXT_GEDIMMT)
    fenster.blit(titel_surf, titel_surf.get_rect(center=(BREITE // 2, 130)))
    fenster.blit(sub_surf, sub_surf.get_rect(center=(BREITE // 2, 182)))

    zeichne_button(
        fenster,
        BTN_FREUND_RECT,
        "Mit Freund spielen",
        "Auf einem Gerät gegeneinander",
        maus_pos,
        schriften,
    )
    zeichne_button(
        fenster,
        BTN_BOT_RECT,
        "Gegen Bot spielen",
        "Platzhalter für später",
        maus_pos,
        schriften,
        akzent_farbe=FARBE_FELD_DUNKEL,
    )


def zeichne_bot_platzhalter(fenster, schriften: dict, maus_pos: tuple[int, int]):
    """Platzhalter-Ansicht für den späteren Bot-Modus."""
    fenster.fill(FARBE_HINTERGRUND)

    karte = pygame.Rect((BREITE - 460) // 2, 165, 460, 295)
    pygame.draw.rect(fenster, FARBE_KARTE, karte, border_radius=14)
    pygame.draw.rect(fenster, FARBE_FELD_DUNKEL, karte, width=2, border_radius=14)

    titel_surf = schriften["banner"].render("Bot-Modus", True, FARBE_FELD_HELL)
    info1_surf = schriften["info"].render("Noch nicht verfügbar", True, FARBE_TEXT_HELL)
    info2_surf = schriften["klein"].render(
        "Dieser Bereich ist eine Lücke für die spätere Bot-Logik.",
        True,
        FARBE_TEXT_GEDIMMT,
    )

    fenster.blit(titel_surf, titel_surf.get_rect(center=(BREITE // 2, 220)))
    fenster.blit(info1_surf, info1_surf.get_rect(center=(BREITE // 2, 270)))
    fenster.blit(info2_surf, info2_surf.get_rect(center=(BREITE // 2, 305)))

    zeichne_button(
        fenster,
        BTN_ZURUECK_RECT,
        "Zurück",
        None,
        maus_pos,
        schriften,
    )


# --- HAUPTSCHLEIFE ---
def main():
    pygame.init()
    fenster = pygame.display.set_mode((BREITE, HOEHE))
    schriften = erstelle_schriften()
    figuren_surfaces = pre_render_figuren(schriften)

    board = chess.Board()
    ausgewaehlt: int | None = None
    zustand = "start"  # "start", "freund", "bot"
    engine_aktiv = False
    letzter_zug_von_engine = False
    uhr = pygame.time.Clock()
    laeuft = True

    def aktualisiere_titel():
        if zustand == "start":
            titel = "Schach - Startseite"
        elif zustand == "bot":
            titel = "Schach - Bot (Platzhalter)"
        else:
            modus = "Engine aktiv (Schwarz)" if engine_aktiv else "Freund (Lokal)"
            titel = f"Schachbrett - {modus}"
        pygame.display.set_caption(titel)

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

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                laeuft = False

            elif zustand == "start":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if BTN_FREUND_RECT.collidepoint(event.pos):
                        board.reset()
                        ausgewaehlt = None
                        letzter_zug_von_engine = False
                        engine_aktiv = False
                        zustand = "freund"
                        aktualisiere_titel()
                    elif BTN_BOT_RECT.collidepoint(event.pos):
                        zustand = "bot"
                        aktualisiere_titel()

            elif zustand == "bot":
                # Platzhalter für späteren Bot-Modus
                if (
                    (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE)
                    or (
                        event.type == pygame.MOUSEBUTTONDOWN
                        and event.button == 1
                        and BTN_ZURUECK_RECT.collidepoint(event.pos)
                    )
                ):
                    zustand = "start"
                    aktualisiere_titel()

            elif zustand == "freund":
                # Tastatur-Eingaben
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        zustand = "start"
                        aktualisiere_titel()

                    elif event.key == pygame.K_r:
                        board.reset()
                        ausgewaehlt = None
                        letzter_zug_von_engine = False

                    elif event.key == pygame.K_e:
                        engine_aktiv = not engine_aktiv
                        aktualisiere_titel()
                        print(f"Engine-Modus geändert: {'Aktiv' if engine_aktiv else 'Deaktiviert'}")

                    elif event.key == pygame.K_z:
                        # Falls der letzte Zug von der Engine kam, 2 Halbzüge zurücknehmen,
                        # damit Weiß direkt wieder am Zug ist.
                        if letzter_zug_von_engine and len(board.move_stack) >= 2:
                            board.pop()
                            board.pop()
                            letzter_zug_von_engine = False
                        elif len(board.move_stack) >= 1:
                            board.pop()
                            letzter_zug_von_engine = False
                        ausgewaehlt = None

                # Maus-Eingaben
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if not board.is_game_over():
                        x, y = event.pos
                        spalte = x // FELD_GROESSE
                        zeile = y // FELD_GROESSE
                        geklickt = chess.square(spalte, 7 - zeile)

                        if ausgewaehlt is None:
                            figur = board.piece_at(geklickt)
                            # Nur Figuren der aktuellen Spielerfarbe anwählen
                            if figur and figur.color == board.turn:
                                ausgewaehlt = geklickt
                        elif geklickt == ausgewaehlt:
                            # Klick auf die bereits gewählte Figur hebt Auswahl auf
                            ausgewaehlt = None
                        else:
                            # Zug zusammensetzen & Bauernumwandlung zur Dame berücksichtigen
                            zug = chess.Move(ausgewaehlt, geklickt)
                            if chess.Move(ausgewaehlt, geklickt, promotion=chess.QUEEN) in board.legal_moves:
                                zug = chess.Move(ausgewaehlt, geklickt, promotion=chess.QUEEN)

                            if zug in board.legal_moves:
                                board.push(zug)
                                ausgewaehlt = None
                                letzter_zug_von_engine = False

                                # Spielerzug sofort rendern, bevor die Engine rechnet
                                zeichne_brett(fenster, board, ausgewaehlt, schriften, figuren_surfaces)
                                pygame.display.flip()

                                # Antwortzug der Engine für Schwarz abrufen
                                if engine_aktiv and not board.is_game_over() and board.turn == chess.BLACK:
                                    engine_zug = meine_engine_zug(board)
                                    if engine_zug and engine_zug in board.legal_moves:
                                        pygame.time.delay(120)  # Kleine visuelle Verzögerung für Natürlichkeit
                                        board.push(engine_zug)
                                        letzter_zug_von_engine = True
                            else:
                                # Anderes eigenes Feld angeklickt -> Auswahl dorthin wechseln
                                figur = board.piece_at(geklickt)
                                if figur and figur.color == board.turn:
                                    ausgewaehlt = geklickt
                                else:
                                    ausgewaehlt = None

        # Aktuelle Ansicht zeichnen
        if zustand == "start":
            zeichne_startseite(fenster, schriften, maus_pos)
        elif zustand == "bot":
            zeichne_bot_platzhalter(fenster, schriften, maus_pos)
        else:
            zeichne_brett(fenster, board, ausgewaehlt, schriften, figuren_surfaces)
            if board.is_game_over():
                zeichne_game_over_banner(fenster, board, schriften)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
