"""
Starke Schach-Engine (Negamax + Alpha-Beta, Iterative Deepening,
Transposition Table, Quiescence Search, Null-Move Pruning, LMR,
Tapered Evaluation mit Piece-Square-Tables & Bauernstruktur).
"""

from __future__ import annotations

import random
import time
import chess
import chess.polyglot

# --- KONSTANTEN ---
INF = 10_000_000
MATE_SCORE = 1_000_000
MATE_THRESHOLD = 900_000

TT_EXACT = 0
TT_LOWER = 1
TT_UPPER = 2
MAX_TT_SIZE = 200_000

# Figurenwerte in Centipawns
PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000,
}

# Phasen-Gewichte für Tapered Eval (Summe = 24)
PHASE_WEIGHTS = {
    chess.PAWN: 0,
    chess.KNIGHT: 1,
    chess.BISHOP: 1,
    chess.ROOK: 2,
    chess.QUEEN: 4,
    chess.KING: 0,
}
MAX_PHASE = 24

# --- PIECE-SQUARE TABLES (aus weißer Sicht: Index 0 = a1, 63 = h8) ---
# Hinweis: python-chess nutzt square 0 = a1 (Rank 0, File 0) bis 63 = h8 (Rank 7, File 7).
# Die Tabellen unten sind visuell von Rank 8 (oben) nach Rank 1 (unten) geschrieben
# und werden beim Laden passend gespiegelt, damit Index == chess.square(file, rank).

def _flip_table(table: list[int]) -> list[int]:
    """Konvertiert eine visuell (Rank 8 -> Rank 1) notierte Tabelle in chess.Square-Reihenfolge."""
    out = [0] * 64
    for sq in range(64):
        rank = sq // 8
        file = sq % 8
        vis_idx = (7 - rank) * 8 + file
        out[sq] = table[vis_idx]
    return out


MG_PAWN_TABLE = _flip_table([
      0,   0,   0,   0,   0,   0,  0,   0,
     98, 134,  61,  95,  68, 126, 34, -11,
     -6,   7,  26,  31,  65,  56, 25, -20,
    -14,  13,   6,  21,  23,  12, 17, -23,
    -27,  -2,  -5,  12,  17,   6, 10, -25,
    -26,  -4,  -4, -10,   3,   3, 33, -12,
    -35,  -1, -20, -23, -15,  24, 38, -22,
      0,   0,   0,   0,   0,   0,  0,   0,
])

EG_PAWN_TABLE = _flip_table([
      0,   0,   0,   0,   0,   0,   0,   0,
    178, 173, 158, 134, 147, 132, 165, 187,
     94, 100,  85,  67,  56,  53,  82,  84,
     32,  24,  13,   5,  -2,   4,  17,  17,
     13,   9,  -3,  -7,  -7,  -8,   3,  -1,
      4,   7,  -6,   1,   0,  -5,  -1,  -8,
     13,   8,   8,  10,  13,   0,   2,  -7,
      0,   0,   0,   0,   0,   0,   0,   0,
])

MG_KNIGHT_TABLE = _flip_table([
    -167, -89, -34, -49,  61, -97, -15, -107,
     -73, -41,  72,  36,  23,  62,   7,  -17,
     -47,  60,  37,  65,  84, 129,  73,   44,
      -9,  17,  19,  53,  37,  69,  18,   22,
     -13,   4,  16,  13,  28,  19,  21,   -8,
     -23,  -9,  12,  10,  19,  17,  25,  -16,
     -29, -53, -12,  -3,  -1,  18, -14,  -19,
    -105, -21, -58, -33, -17, -28, -19,  -23,
])

EG_KNIGHT_TABLE = _flip_table([
    -58, -38, -13, -28, -31, -27, -63, -99,
    -25,  -8, -25,  -2,  -9, -25, -24, -52,
    -24, -20,  10,   9,  -1,  -9, -19, -41,
    -17,   3,  22,  22,  22,  11,   8, -18,
    -18,  -6,  16,  25,  16,  17,   4, -18,
    -23,  -3,  -1,  15,  10,  -3, -20, -22,
    -42, -20, -10,  -5,  -2, -20, -23, -44,
    -29, -51, -23, -15, -22, -18, -50, -64,
])

MG_BISHOP_TABLE = _flip_table([
    -29,   4, -82, -37, -25, -42,   7,  -8,
    -26,  16, -18, -13,  30,  59,  18, -47,
    -16,  37,  43,  40,  35,  50,  37,  -2,
     -4,   5,  19,  50,  37,  37,   7,  -2,
     -6,  13,  13,  26,  34,  12,  10,   4,
      0,  15,  15,  15,  14,  27,  18,  10,
      4,  15,  16,   0,   7,  21,  33,   1,
    -33,  -3, -14, -21, -13, -12, -39, -21,
])

EG_BISHOP_TABLE = _flip_table([
    -14, -21, -11,  -8, -7,  -9, -17, -24,
     -8,  -4,   7, -12, -3, -13,  -4, -14,
      2,  -8,   0,  -1, -2,   6,   0,   4,
     -3,   9,  12,   9, 14,  10,   3,   2,
     -6,   3,  13,  19,  7,  10,  -3,  -9,
    -12,  -3,   8,  10, 13,   3,  -7, -15,
    -14, -18,  -7,  -1,  4,  -9, -15, -27,
    -23,  -9, -23,  -5, -9, -16,  -5, -17,
])

MG_ROOK_TABLE = _flip_table([
     32,  42,  32,  51, 63,  9,  31,  43,
     27,  32,  58,  62, 80, 67,  26,  44,
     -5,  19,  26,  36, 17, 45,  61,  16,
    -24, -11,   7,  26, 24, 35,  -8, -20,
    -36, -26, -12,  -1,  9, -7,   6, -23,
    -45, -25, -16, -17,  3,  0,  -5, -33,
    -44, -16, -20,  -9, -1, 11,  -6, -71,
    -19, -13,   1,  17, 16,  7, -37, -26,
])

EG_ROOK_TABLE = _flip_table([
    13, 10, 18, 15, 12,  12,   8,   5,
    11, 13, 13, 11, -3,   3,   8,   3,
     7,  7,  7,  5,  4,  -3,  -5,  -3,
     4,  3, 13,  1,  2,   1,  -1,   2,
     3,  5,  8,  4, -5,  -6,  -8, -11,
    -4,  0, -5, -1, -7, -12,  -8, -16,
    -6, -6,  0,  2, -9,  -9, -11,  -3,
    -9,  2,  3, -1, -5, -13,   4, -20,
])

MG_QUEEN_TABLE = _flip_table([
    -28,   0,  29,  12,  59,  44,  43,  45,
    -24, -39,  -5,   1, -16,  57,  28,  54,
    -13, -17,   7,   8,  29,  56,  47,  57,
    -27, -27, -16, -16,  -1,  17,  -2,   1,
     -9, -26,  -9, -10,  -2,  -4,   3,  -3,
    -14,   2, -11,  -2,  -5,   2,  14,   5,
    -35,  -8,  11,   2,   8,  15,  -3,   1,
     -1, -18,  -9,  10, -15, -25, -31, -50,
])

EG_QUEEN_TABLE = _flip_table([
     -9,  22,  22,  27,  27,  19,  10,  20,
    -17,  20,  32,  41,  58,  25,  30,   0,
    -20,   6,   9,  49,  47,  35,  19,   9,
      3,  22,  24,  45,  57,  40,  57,  36,
    -18,  28,  19,  47,  31,  34,  39,  23,
    -16, -27,  15,   6,   9,  17,  10,   5,
    -22, -23, -30, -16, -16, -23, -36, -32,
    -33, -28, -22, -43,  -5, -32, -20, -41,
])

MG_KING_TABLE = _flip_table([
    -65,  23,  16, -15, -56, -34,   2,  13,
     29,  -1, -20,  -7,  -8,  -4, -38, -29,
     -9,  24,   2, -16, -20,   6,  22, -22,
    -17, -20, -12, -27, -30, -25, -14, -36,
    -49,  -1, -27, -39, -46, -44, -33, -51,
    -14, -14, -22, -46, -44, -30, -15, -27,
      1,   7,  -8, -64, -43, -16,   9,   8,
    -15,  36,  12, -54,   8, -28,  24,  14,
])

EG_KING_TABLE = _flip_table([
    -74, -35, -18, -18, -11,  15,   4, -17,
    -12,  17,  14,  17,  17,  38,  23,  11,
     10,  17,  23,  15,  20,  45,  44,  13,
     -8,  22,  24,  27,  26,  33,  26,   3,
    -18,  -4,  21,  24,  27,  23,   9, -11,
    -19,  -3,  11,  21,  23,  16,   7,  -9,
    -27, -11,   4,  13,  14,   4,  -5, -17,
    -53, -33, -21, -11, -28, -14, -24, -43,
])

MG_PST = {
    chess.PAWN: MG_PAWN_TABLE,
    chess.KNIGHT: MG_KNIGHT_TABLE,
    chess.BISHOP: MG_BISHOP_TABLE,
    chess.ROOK: MG_ROOK_TABLE,
    chess.QUEEN: MG_QUEEN_TABLE,
    chess.KING: MG_KING_TABLE,
}

EG_PST = {
    chess.PAWN: EG_PAWN_TABLE,
    chess.KNIGHT: EG_KNIGHT_TABLE,
    chess.BISHOP: EG_BISHOP_TABLE,
    chess.ROOK: EG_ROOK_TABLE,
    chess.QUEEN: EG_QUEEN_TABLE,
    chess.KING: EG_KING_TABLE,
}

# Bitmasken für benachbarte Linien (für isolierte & Freibauern)
ADJACENT_FILES_BB = [0] * 8
for _f in range(8):
    mask = 0
    if _f > 0:
        mask |= chess.BB_FILES[_f - 1]
    if _f < 7:
        mask |= chess.BB_FILES[_f + 1]
    ADJACENT_FILES_BB[_f] = mask

# Bitmasken für Freibauern-Prüfung (alle Felder vor dem Bauern auf eigener + benachbarten Linien)
PASSED_MASK_WHITE = [0] * 64
PASSED_MASK_BLACK = [0] * 64
for _sq in range(64):
    _r = _sq // 8
    _f = _sq % 8
    _files = chess.BB_FILES[_f] | ADJACENT_FILES_BB[_f]
    _w_mask = 0
    for _rr in range(_r + 1, 8):
        _w_mask |= chess.BB_RANKS[_rr]
    _b_mask = 0
    for _rr in range(0, _r):
        _b_mask |= chess.BB_RANKS[_rr]
    PASSED_MASK_WHITE[_sq] = _files & _w_mask
    PASSED_MASK_BLACK[_sq] = _files & _b_mask

PASSED_PAWN_BONUS = [0, 10, 15, 25, 45, 75, 115, 0]

# Kleines Eröffnungsbuch (Zobrist-Hash -> Liste starker Antwortzüge in UCI)
_BOOK_LINES = [
    # Sizilianisch (Najdorf / Klassisch)
    ["e2e4", "c7c5", "g1f3", "d7d6", "d2d4", "c5d4", "f3d4", "g8f6", "b1c3", "a7a6"],
    ["e2e4", "c7c5", "g1f3", "b8c6", "d2d4", "c5d4", "f3d4", "g8f6", "b1c3", "e7e5"],
    ["e2e4", "c7c5", "b1c3", "b8c6", "g2g3", "g7g6"],
    # Spanisch / Italienisch (e4 e5)
    ["e2e4", "e7e5", "g1f3", "b8c6", "f1b5", "a7a6", "b5a4", "g8f6", "e1g1", "f8e7"],
    ["e2e4", "e7e5", "g1f3", "b8c6", "f1c4", "f8c5", "c2c3", "g8f6"],
    # Damengambit Abgelehnt & Slawisch
    ["d2d4", "d7d5", "c2c4", "e7e6", "b1c3", "g8f6", "c1g5", "f8e7"],
    ["d2d4", "d7d5", "c2c4", "c7c6", "g1f3", "g8f6", "b1c3", "d5c4"],
    # Nimzo-Indisch / Königsindisch
    ["d2d4", "g8f6", "c2c4", "e7e6", "b1c3", "f8b4"],
    ["d2d4", "g8f6", "c2c4", "g7g6", "b1c3", "f8g7", "e2e4", "d7d6"],
    # Englisch
    ["c2c4", "e7e5", "b1c3", "g8f6", "g1f3", "b8c6"],
    ["g1f3", "d7d5", "d2d4", "g8f6", "c2c4", "e7e6"],
]


def _build_opening_book() -> dict[int, list[str]]:
    book: dict[int, set[str]] = {}
    for line in _BOOK_LINES:
        b = chess.Board()
        for uci in line:
            h = chess.polyglot.zobrist_hash(b)
            book.setdefault(h, set()).add(uci)
            b.push_uci(uci)
    return {k: sorted(v) for k, v in book.items()}


OPENING_BOOK = _build_opening_book()


class SearchTimeout(Exception):
    """Signalisiert das Erreichen des Zeitlimits während der Suche."""


class ChessEngine:
    """Starke Alpha-Beta-Schachengine mit Iterative Deepening und Tapered Eval."""

    def __init__(self, time_limit: float = 2.0, max_depth: int = 12):
        self.time_limit = time_limit
        self.max_depth = max_depth
        self.tt: dict[int, tuple[int, int, int, chess.Move | None]] = {}
        self.killers: list[list[chess.Move | None]] = [[None, None] for _ in range(128)]
        self.history: dict[tuple[bool, int, int], int] = {}
        self.nodes = 0
        self.start_time = 0.0
        self.stop_time = 0.0

    def _check_time(self):
        if (self.nodes & 1023) == 0:
            if time.perf_counter() >= self.stop_time:
                raise SearchTimeout()

    def evaluate(self, board: chess.Board) -> int:
        """
        Statische Stellungsbewertung aus Sicht der Seite am Zug (in Centipawns).
        """
        if board.is_insufficient_material():
            return 0

        mg_score = 0
        eg_score = 0
        phase = 0

        # Material + Piece-Square-Tables
        for piece_type in (chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN, chess.KING):
            val = PIECE_VALUES[piece_type]
            pw = PHASE_WEIGHTS[piece_type]
            mg_tbl = MG_PST[piece_type]
            eg_tbl = EG_PST[piece_type]

            w_bb = board.pieces_mask(piece_type, chess.WHITE)
            while w_bb:
                lsb = w_bb & -w_bb
                sq = lsb.bit_length() - 1
                w_bb ^= lsb
                mg_score += val + mg_tbl[sq]
                eg_score += val + eg_tbl[sq]
                phase += pw

            b_bb = board.pieces_mask(piece_type, chess.BLACK)
            while b_bb:
                lsb = b_bb & -b_bb
                sq = lsb.bit_length() - 1
                b_bb ^= lsb
                mirrored = sq ^ 56  # Horizontal spiegeln für Schwarz
                mg_score -= val + mg_tbl[mirrored]
                eg_score -= val + eg_tbl[mirrored]
                phase += pw

        # Läuferpaar-Bonus
        if chess.popcount(board.pieces_mask(chess.BISHOP, chess.WHITE)) >= 2:
            mg_score += 30
            eg_score += 45
        if chess.popcount(board.pieces_mask(chess.BISHOP, chess.BLACK)) >= 2:
            mg_score -= 30
            eg_score -= 45

        # Bauernstruktur (Doppelbauern, Isolierte Bauern, Freibauern) & Turm-Linien
        w_pawns = board.pieces_mask(chess.PAWN, chess.WHITE)
        b_pawns = board.pieces_mask(chess.PAWN, chess.BLACK)

        for f in range(8):
            file_mask = chess.BB_FILES[f]
            w_on_file = chess.popcount(w_pawns & file_mask)
            b_on_file = chess.popcount(b_pawns & file_mask)

            if w_on_file > 1:
                mg_score -= 12 * (w_on_file - 1)
                eg_score -= 18 * (w_on_file - 1)
            if b_on_file > 1:
                mg_score += 12 * (b_on_file - 1)
                eg_score += 18 * (b_on_file - 1)

            if w_on_file and not (w_pawns & ADJACENT_FILES_BB[f]):
                mg_score -= 15
                eg_score -= 20
            if b_on_file and not (b_pawns & ADJACENT_FILES_BB[f]):
                mg_score += 15
                eg_score += 20

        # Freibauern
        wp_tmp = w_pawns
        while wp_tmp:
            lsb = wp_tmp & -wp_tmp
            sq = lsb.bit_length() - 1
            wp_tmp ^= lsb
            if not (b_pawns & PASSED_MASK_WHITE[sq]):
                rank = sq // 8
                bonus = PASSED_PAWN_BONUS[rank]
                mg_score += bonus // 2
                eg_score += bonus

        bp_tmp = b_pawns
        while bp_tmp:
            lsb = bp_tmp & -bp_tmp
            sq = lsb.bit_length() - 1
            bp_tmp ^= lsb
            if not (w_pawns & PASSED_MASK_BLACK[sq]):
                rank = 7 - (sq // 8)
                bonus = PASSED_PAWN_BONUS[rank]
                mg_score -= bonus // 2
                eg_score -= bonus

        # Türme auf offenen / halboffenen Linien
        w_rooks = board.pieces_mask(chess.ROOK, chess.WHITE)
        while w_rooks:
            lsb = w_rooks & -w_rooks
            sq = lsb.bit_length() - 1
            w_rooks ^= lsb
            f_mask = chess.BB_FILES[sq % 8]
            if not (w_pawns & f_mask):
                if not (b_pawns & f_mask):
                    mg_score += 22
                    eg_score += 18
                else:
                    mg_score += 10
                    eg_score += 8

        b_rooks = board.pieces_mask(chess.ROOK, chess.BLACK)
        while b_rooks:
            lsb = b_rooks & -b_rooks
            sq = lsb.bit_length() - 1
            b_rooks ^= lsb
            f_mask = chess.BB_FILES[sq % 8]
            if not (b_pawns & f_mask):
                if not (w_pawns & f_mask):
                    mg_score -= 22
                    eg_score -= 18
                else:
                    mg_score -= 10
                    eg_score -= 8

        # Königssicherheit im Mittelspiel (Bauernschild)
        w_king_sq = board.king(chess.WHITE)
        if w_king_sq is not None:
            kf = w_king_sq % 8
            kr = w_king_sq // 8
            if kr <= 1:
                shield_rank = chess.BB_RANKS[kr + 1]
                shield_files = chess.BB_FILES[kf] | ADJACENT_FILES_BB[kf]
                mg_score += 10 * chess.popcount(w_pawns & shield_rank & shield_files)

        b_king_sq = board.king(chess.BLACK)
        if b_king_sq is not None:
            kf = b_king_sq % 8
            kr = b_king_sq // 8
            if kr >= 6:
                shield_rank = chess.BB_RANKS[kr - 1]
                shield_files = chess.BB_FILES[kf] | ADJACENT_FILES_BB[kf]
                mg_score -= 10 * chess.popcount(b_pawns & shield_rank & shield_files)

        # Tapered Eval zwischen Mittelspiel und Endspiel
        if phase > MAX_PHASE:
            phase = MAX_PHASE
        score = (mg_score * phase + eg_score * (MAX_PHASE - phase)) // MAX_PHASE

        # Kleiner Tempo-Bonus für Seite am Zug
        tempo = 10
        return (score + tempo) if board.turn == chess.WHITE else (-score + tempo)

    def _score_move(self, board: chess.Board, move: chess.Move,
                    tt_move: chess.Move | None, ply: int) -> int:
        if move == tt_move:
            return 10_000_000

        score = 0
        if move.promotion:
            score += 900_000 + PIECE_VALUES[move.promotion]

        if board.is_capture(move):
            attacker = board.piece_type_at(move.from_square) or chess.PAWN
            if board.is_en_passant(move):
                victim = chess.PAWN
            else:
                victim = board.piece_type_at(move.to_square) or chess.PAWN
            # MVV-LVA
            score += 500_000 + PIECE_VALUES[victim] * 10 - PIECE_VALUES[attacker]
            return score

        if ply < 128:
            if move == self.killers[ply][0]:
                return 400_000
            if move == self.killers[ply][1]:
                return 350_000

        score += self.history.get((board.turn, move.from_square, move.to_square), 0)
        return score

    def _order_moves(self, board: chess.Board, moves, tt_move: chess.Move | None, ply: int):
        return sorted(moves, key=lambda m: self._score_move(board, m, tt_move, ply), reverse=True)

    def _quiescence(self, board: chess.Board, alpha: int, beta: int, ply: int) -> int:
        self.nodes += 1
        self._check_time()

        if board.is_repetition(2) or board.is_fifty_moves() or board.is_insufficient_material():
            return 0

        in_check = board.is_check()
        if not in_check:
            stand_pat = self.evaluate(board)
            if stand_pat >= beta:
                return beta
            if stand_pat > alpha:
                alpha = stand_pat
            # Nur Schlagzüge und Umwandlungen im Ruhezustand betrachten
            candidates = [
                m for m in board.legal_moves
                if board.is_capture(m) or m.promotion == chess.QUEEN
            ]
        else:
            candidates = list(board.legal_moves)
            if not candidates:
                return -MATE_SCORE + ply

        ordered = self._order_moves(board, candidates, None, ply)
        for move in ordered:
            # Delta Pruning (falls nicht im Schach)
            if not in_check and not move.promotion:
                victim = chess.PAWN if board.is_en_passant(move) else (board.piece_type_at(move.to_square) or chess.PAWN)
                if stand_pat + PIECE_VALUES[victim] + 200 < alpha:
                    continue

            board.push(move)
            score = -self._quiescence(board, -beta, -alpha, ply + 1)
            board.pop()

            if score >= beta:
                return beta
            if score > alpha:
                alpha = score

        return alpha

    def _has_non_pawn_material(self, board: chess.Board, color: bool) -> bool:
        return bool(
            board.pieces_mask(chess.KNIGHT, color)
            or board.pieces_mask(chess.BISHOP, color)
            or board.pieces_mask(chess.ROOK, color)
            or board.pieces_mask(chess.QUEEN, color)
        )

    def _negamax(self, board: chess.Board, depth: int, alpha: int, beta: int,
                 ply: int, allow_null: bool = True) -> int:
        self.nodes += 1
        self._check_time()

        if ply > 0:
            if board.is_repetition(2) or board.is_fifty_moves() or board.is_insufficient_material():
                return 0

        in_check = board.is_check()
        if in_check and ply < 64:
            depth += 1  # Check Extension

        if depth <= 0:
            return self._quiescence(board, alpha, beta, ply)

        alpha_orig = alpha
        zobrist = chess.polyglot.zobrist_hash(board)
        tt_move: chess.Move | None = None

        entry = self.tt.get(zobrist)
        if entry is not None:
            tt_depth, tt_flag, tt_score, tt_move = entry
            if tt_depth >= depth:
                # Matt-Distanzen korrigieren
                adj_score = tt_score
                if adj_score > MATE_THRESHOLD:
                    adj_score -= ply
                elif adj_score < -MATE_THRESHOLD:
                    adj_score += ply

                if tt_flag == TT_EXACT:
                    return adj_score
                elif tt_flag == TT_LOWER:
                    if adj_score > alpha:
                        alpha = adj_score
                elif tt_flag == TT_UPPER:
                    if adj_score < beta:
                        beta = adj_score
                if alpha >= beta:
                    return adj_score

        legal_moves = list(board.legal_moves)
        if not legal_moves:
            if in_check:
                return -MATE_SCORE + ply
            return 0  # Patt

        # Null-Move Pruning
        if (
            allow_null
            and not in_check
            and depth >= 3
            and ply > 0
            and self._has_non_pawn_material(board, board.turn)
        ):
            r = 3 if depth >= 6 else 2
            board.push(chess.Move.null())
            null_score = -self._negamax(board, depth - 1 - r, -beta, -beta + 1, ply + 1, allow_null=False)
            board.pop()
            if null_score >= beta:
                return beta

        ordered_moves = self._order_moves(board, legal_moves, tt_move, ply)
        best_move = ordered_moves[0]
        best_score = -INF

        for idx, move in enumerate(ordered_moves):
            is_capture = board.is_capture(move)
            board.push(move)

            # Late Move Reduction (LMR)
            if (
                idx >= 3
                and depth >= 3
                and not in_check
                and not is_capture
                and not move.promotion
                and not board.is_check()
            ):
                reduction = 2 if (idx >= 8 and depth >= 5) else 1
                score = -self._negamax(board, depth - 1 - reduction, -alpha - 1, -alpha, ply + 1)
                if score > alpha:
                    score = -self._negamax(board, depth - 1, -beta, -alpha, ply + 1)
            else:
                # Principal Variation Search (PVS)
                if idx == 0:
                    score = -self._negamax(board, depth - 1, -beta, -alpha, ply + 1)
                else:
                    score = -self._negamax(board, depth - 1, -alpha - 1, -alpha, ply + 1)
                    if alpha < score < beta:
                        score = -self._negamax(board, depth - 1, -beta, -alpha, ply + 1)

            board.pop()

            if score > best_score:
                best_score = score
                best_move = move

            if score > alpha:
                alpha = score

            if alpha >= beta:
                # Killer & History Heuristik für ruhige Züge aktualisieren
                if not is_capture and not move.promotion and ply < 128:
                    if self.killers[ply][0] != move:
                        self.killers[ply][1] = self.killers[ply][0]
                        self.killers[ply][0] = move
                    key = (board.turn, move.from_square, move.to_square)
                    self.history[key] = min(self.history.get(key, 0) + depth * depth, 200_000)
                break

        # In Transposition Table speichern
        if len(self.tt) >= MAX_TT_SIZE:
            self.tt.clear()

        if best_score <= alpha_orig:
            flag = TT_UPPER
        elif best_score >= beta:
            flag = TT_LOWER
        else:
            flag = TT_EXACT

        store_score = best_score
        if store_score > MATE_THRESHOLD:
            store_score += ply
        elif store_score < -MATE_THRESHOLD:
            store_score -= ply

        self.tt[zobrist] = (depth, flag, store_score, best_move)
        return best_score

    def find_best_move(self, board: chess.Board) -> chess.Move | None:
        """Berechnet den stärkstmöglichen Zug innerhalb des Zeitlimits."""
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return None
        if len(legal_moves) == 1:
            return legal_moves[0]

        # 1. Eröffnungsbuch prüfen
        zobrist = chess.polyglot.zobrist_hash(board)
        if zobrist in OPENING_BOOK:
            book_uci = random.choice(OPENING_BOOK[zobrist])
            book_move = chess.Move.from_uci(book_uci)
            if book_move in legal_moves:
                return book_move

        # 2. Iterative Deepening mit Aspiration Windows
        # Auf einer Kopie suchen, damit SearchTimeout das Originalbrett niemals verändert.
        search_board = board.copy()
        self.nodes = 0
        self.start_time = time.perf_counter()
        self.stop_time = self.start_time + self.time_limit
        best_move = legal_moves[0]
        prev_score = 0

        for depth in range(1, self.max_depth + 1):
            try:
                alpha = -INF
                beta = INF
                if depth >= 4 and abs(prev_score) < MATE_THRESHOLD:
                    alpha = prev_score - 50
                    beta = prev_score + 50

                score, move = self._search_root(search_board, depth, alpha, beta, best_move)

                # Bei Aspiration-Fehlschlag mit vollem Fenster neu suchen
                if score <= alpha or score >= beta:
                    score, move = self._search_root(search_board, depth, -INF, INF, best_move)

                best_move = move
                prev_score = score

                # Wenn ein erzwungenes Matt gefunden wurde, nicht unnötig weiter suchen
                if abs(score) >= MATE_THRESHOLD:
                    break
            except SearchTimeout:
                break

        return best_move

    def _search_root(self, board: chess.Board, depth: int, alpha: int, beta: int,
                     prev_best: chess.Move) -> tuple[int, chess.Move]:
        legal_moves = list(board.legal_moves)
        zobrist = chess.polyglot.zobrist_hash(board)
        entry = self.tt.get(zobrist)
        tt_move = entry[3] if entry is not None else prev_best

        ordered = self._order_moves(board, legal_moves, tt_move, 0)
        best_move = ordered[0]
        best_score = -INF

        for idx, move in enumerate(ordered):
            board.push(move)
            if idx == 0:
                score = -self._negamax(board, depth - 1, -beta, -alpha, 1)
            else:
                score = -self._negamax(board, depth - 1, -alpha - 1, -alpha, 1)
                if alpha < score < beta:
                    score = -self._negamax(board, depth - 1, -beta, -alpha, 1)
            board.pop()

            if score > best_score:
                best_score = score
                best_move = move
            if score > alpha:
                alpha = score
            if alpha >= beta:
                break

        return best_score, best_move


# Globale Instanz, damit Transposition-Table & History über Züge hinweg erhalten bleiben
_ENGINE = ChessEngine(time_limit=2.0, max_depth=12)


def berechne_zug(board: chess.Board) -> chess.Move | None:
    """Öffentliche Schnittstelle für main.py."""
    return _ENGINE.find_best_move(board)
