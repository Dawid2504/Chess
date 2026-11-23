import chess
import pygame

# --- EINSTELLUNGEN ---
BREITE, HOEHE = 640, 640
FELD_GROESSE = BREITE // 8

HELL = (240, 217, 181)
DUNKEL = (181, 136, 99)
MARKIERUNG = (130, 151, 105)
SCHACH_FARBE = (220, 70, 70)

# Fallback-Buchstaben, falls Unicode-Symbole auf einem System nicht dargestellt werden
FIGUREN_TEXT = {
    "P": "♙", "N": "♘", "B": "♗", "R": "♖", "Q": "♕", "K": "♔",
    "p": "♟", "n": "♞", "b": "♝", "r": "♜", "q": "♛", "k": "♚",
}

# --- PYGAME STARTEN ---
pygame.init()
fenster = pygame.display.set_mode((BREITE, HOEHE))
pygame.display.set_caption("Schachbrett - Engine Testumgebung")

# Schriftart sicher laden
if "segoeuisymbol" in pygame.font.get_fonts():
    schrift = pygame.font.SysFont("segoeuisymbol", 54)
else:
    schrift = pygame.font.SysFont(None, 54)


# --- PLATZHALTER FÜR DEINE SPÄTERE ENGINE ---
def meine_engine_zug(board: chess.Board) -> chess.Move | None:
    """
    Hier kommt später deine eigene Engine rein!
    Solange hier None zurückgegeben wird, spielst du beide Seiten selbst.
    """
    return None


# --- GRAFIK-FUNKTIONEN ---
def zeichne_brett(board: chess.Board, ausgewaehlt: int | None):
    erlaubte_ziele = []
    if ausgewaehlt is not None:
        erlaubte_ziele = [
            zug.to_square for zug in board.legal_moves if zug.from_square == ausgewaehlt
        ]

    koenig_feld = board.king(board.turn) if board.is_check() else None

    for zeile in range(8):
        for spalte in range(8):
            feld = chess.square(spalte, 7 - zeile)
            rect = pygame.Rect(
                spalte * FELD_GROESSE, zeile * FELD_GROESSE, FELD_GROESSE, FELD_GROESSE
            )

            # Feldfarbe wählen
            if feld == koenig_feld:
                farbe = SCHACH_FARBE
            elif feld == ausgewaehlt:
                farbe = MARKIERUNG
            else:
                farbe = HELL if (zeile + spalte) % 2 == 0 else DUNKEL

            pygame.draw.rect(fenster, farbe, rect)

            # Punkt für erlaubte Züge
            if feld in erlaubte_ziele:
                mitte = (
                    spalte * FELD_GROESSE + FELD_GROESSE // 2,
                    zeile * FELD_GROESSE + FELD_GROESSE // 2,
                )
                pygame.draw.circle(fenster, MARKIERUNG, mitte, 12)

            # Figur zeichnen
            figur = board.piece_at(feld)
            if figur:
                symbol = FIGUREN_TEXT[figur.symbol()]
                text_surface = schrift.render(symbol, True, (20, 20, 20))
                text_rect = text_surface.get_rect(center=rect.center)
                fenster.blit(text_surface, text_rect)


# --- HAUPTSCHLEIFE ---
def main():
    board = chess.Board()
    ausgewaehlt = None
    uhr = pygame.time.Clock()
    laeuft = True

    print("Fenster gestartet! Steuerung: Mausklick zum Ziehen | R = Reset | Z = Zug zurück")

    while laeuft:
        uhr.tick(60)  # Begrenzt auf 60 FPS (spart CPU-Last)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                laeuft = False

            # Tastatur-Shortcuts zum Testen
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:  # R -> Brett zurücksetzen
                    board.reset()
                    ausgewaehlt = None
                elif event.key == pygame.K_z and len(board.move_stack) > 0:  # Z -> Zug zurück
                    board.pop()
                    ausgewaehlt = None

            # Mausklick verarbeiten
            elif event.type == pygame.MOUSEBUTTONDOWN and not board.is_game_over():
                x, y = event.pos
                geklickt = chess.square(x // FELD_GROESSE, 7 - (y // FELD_GROESSE))

                if ausgewaehlt is None:
                    figur = board.piece_at(geklickt)
                    if figur and figur.color == board.turn:
                        ausgewaehlt = geklickt
                else:
                    zug = chess.Move(ausgewaehlt, geklickt)
                    # Bauernumwandlung automatisch zur Dame
                    if chess.Move(ausgewaehlt, geklickt, promotion=chess.QUEEN) in board.legal_moves:
                        zug.promotion = chess.QUEEN

                    if zug in board.legal_moves:
                        board.push(zug)
                        ausgewaehlt = None
                    else:
                        figur = board.piece_at(geklickt)
                        ausgewaehlt = geklickt if (figur and figur.color == board.turn) else None

        # Wenn Schwarz dran ist und deine Engine einen Zug liefert, wird er ausgeführt
        if not board.is_game_over() and board.turn == chess.BLACK:
            engine_zug = meine_engine_zug(board)
            if engine_zug in board.legal_moves:
                board.push(engine_zug)

        zeichne_brett(board, ausgewaehlt)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()