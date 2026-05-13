#!/usr/bin/env python3
import sys
import time

BOARD_SIZE = 12
N = 144

COLS = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'j', 'k', 'm', 'n']
IDX_TO_COL = {i: c for i, c in enumerate(COLS)}
COL_TO_IDX = {c: i for i, c in enumerate(COLS)}

WHITE = "WHITE"
BLACK = "BLACK"

TIME_BUFFER = 0.05
MAX_DEPTH_CAP = 5
INF = 10**18

MAT = {
    'P': 100000, 'p': 100000,
    'X': 900,    'x': 900,
    'G': 500,    'g': 500,
    'T': 450,    't': 450,
    'S': 350,    's': 350,
    'Y': 300,    'y': 300,
    'N': 250,    'n': 250,
    'B': 100,    'b': 100,
}

DIR8 = [(-1, -1), (-1, 0), (-1, 1),
        (0, -1),            (0, 1),
        (1, -1),  (1, 0),   (1, 1)]
ORTH = [(-1, 0), (1, 0), (0, -1), (0, 1)]
DIAG = [(-1, -1), (-1, 1), (1, -1), (1, 1)]

R_OF = [i // 12 for i in range(N)]
C_OF = [i % 12 for i in range(N)]

START_ROWS = [
    "gytsnxpnstyg",
    "bbbbbbbbbbbb",
    "............",
    "............",
    "............",
    "............",
    "............",
    "............",
    "............",
    "............",
    "BBBBBBBBBBBB",
    "GYTSNXPNSTYG",
]

def idx_of(r, c):
    return r * 12 + c

def in_bounds(r, c):
    return 0 <= r < 12 and 0 <= c < 12

def row_to_num(r):
    return 12 - r

def other(color):
    return BLACK if color == WHITE else WHITE

def is_friend(ch, color):
    if ch == '.':
        return False
    return (color == WHITE and ch.isupper()) or (color == BLACK and ch.islower())

def is_enemy(ch, color):
    if ch == '.':
        return False
    return (color == WHITE and ch.islower()) or (color == BLACK and ch.isupper())

def move_text(src, dst):
    sr, sc = R_OF[src], C_OF[src]
    dr, dc = R_OF[dst], C_OF[dst]
    return f"{IDX_TO_COL[sc]}{row_to_num(sr)} {IDX_TO_COL[dc]}{row_to_num(dr)}"

def coord_to_idx(coord):
    col = coord[0]
    row = int(coord[1:])
    return idx_of(12 - row, COL_TO_IDX[col])

def parse_input():
    with open("input.txt", "r") as f:
        lines = [ln.rstrip("\n") for ln in f]

    color = lines[0].strip()
    my_time, opp_time = map(float, lines[1].split())
    rows = lines[2:14]

    board = ['.'] * N
    white_pieces = []
    black_pieces = []
    white_pos = {}
    black_pos = {}
    white_prince_idx = None
    black_prince_idx = None

    for r in range(12):
        row = rows[r]
        for c in range(12):
            ch = row[c]
            i = idx_of(r, c)
            board[i] = ch
            if ch == '.':
                continue
            if ch.isupper():
                white_pos[i] = len(white_pieces)
                white_pieces.append(i)
                if ch == 'P':
                    white_prince_idx = i
            else:
                black_pos[i] = len(black_pieces)
                black_pieces.append(i)
                if ch == 'p':
                    black_prince_idx = i

    state = {
        'board': board,
        'white_pieces': white_pieces,
        'black_pieces': black_pieces,
        'white_pos': white_pos,
        'black_pos': black_pos,
        'white_prince_idx': white_prince_idx,
        'black_prince_idx': black_prince_idx,
    }
    return color, my_time, opp_time, state

def is_start_position(state):
    board = state['board']
    for r in range(12):
        if ''.join(board[r * 12:(r + 1) * 12]) != START_ROWS[r]:
            return False
    return True

def remove_piece(piece_list, pos_map, idx):
    pos = pos_map[idx]
    last = piece_list[-1]
    piece_list[pos] = last
    pos_map[last] = pos
    piece_list.pop()
    del pos_map[idx]

def restore_piece(piece_list, pos_map, idx):
    pos_map[idx] = len(piece_list)
    piece_list.append(idx)

def make_move(state, src, dst):
    board = state['board']
    moved = board[src]
    captured = board[dst]

    old_white_prince = state['white_prince_idx']
    old_black_prince = state['black_prince_idx']

    board[dst] = moved
    board[src] = '.'

    if moved.isupper():
        mover_list = state['white_pieces']
        mover_map = state['white_pos']
        enemy_list = state['black_pieces']
        enemy_map = state['black_pos']

        mover_pos = mover_map[src]
        del mover_map[src]
        mover_map[dst] = mover_pos
        mover_list[mover_pos] = dst

        if moved == 'P':
            state['white_prince_idx'] = dst

        if captured != '.':
            if captured == 'p':
                state['black_prince_idx'] = None
            remove_piece(enemy_list, enemy_map, dst)
    else:
        mover_list = state['black_pieces']
        mover_map = state['black_pos']
        enemy_list = state['white_pieces']
        enemy_map = state['white_pos']

        mover_pos = mover_map[src]
        del mover_map[src]
        mover_map[dst] = mover_pos
        mover_list[mover_pos] = dst

        if moved == 'p':
            state['black_prince_idx'] = dst

        if captured != '.':
            if captured == 'P':
                state['white_prince_idx'] = None
            remove_piece(enemy_list, enemy_map, dst)

    return captured, mover_pos, moved, old_white_prince, old_black_prince

def undo_move(state, src, dst, captured, mover_pos, moved, old_white_prince, old_black_prince):
    board = state['board']
    board[src] = moved
    board[dst] = captured

    if moved.isupper():
        mover_list = state['white_pieces']
        mover_map = state['white_pos']
        enemy_list = state['black_pieces']
        enemy_map = state['black_pos']

        del mover_map[dst]
        mover_map[src] = mover_pos
        mover_list[mover_pos] = src

        if captured != '.':
            restore_piece(enemy_list, enemy_map, dst)
    else:
        mover_list = state['black_pieces']
        mover_map = state['black_pos']
        enemy_list = state['white_pieces']
        enemy_map = state['white_pos']

        del mover_map[dst]
        mover_map[src] = mover_pos
        mover_list[mover_pos] = src

        if captured != '.':
            restore_piece(enemy_list, enemy_map, dst)

    state['white_prince_idx'] = old_white_prince
    state['black_prince_idx'] = old_black_prince

def gen_baby(state, src, color):
    board = state['board']
    r, c = R_OF[src], C_OF[src]
    dr = -1 if color == WHITE else 1
    out = []
    for step in (1, 2):
        nr = r + dr * step
        if not in_bounds(nr, c):
            break
        dst = idx_of(nr, c)
        ch = board[dst]
        if ch == '.':
            out.append((src, dst))
        elif is_enemy(ch, color):
            out.append((src, dst))
            break
        else:
            break
    return out

def gen_prince(state, src, color):
    board = state['board']
    r, c = R_OF[src], C_OF[src]
    out = []
    for dr, dc in DIR8:
        nr, nc = r + dr, c + dc
        if not in_bounds(nr, nc):
            continue
        dst = idx_of(nr, nc)
        ch = board[dst]
        if is_friend(ch, color):
            continue
        out.append((src, dst))
    return out

def gen_princess(state, src, color):
    board = state['board']
    r, c = R_OF[src], C_OF[src]
    out = []
    for dr, dc in DIR8:
        for step in (1, 2, 3):
            nr, nc = r + dr * step, c + dc * step
            if not in_bounds(nr, nc):
                break
            dst = idx_of(nr, nc)
            ch = board[dst]
            if is_friend(ch, color):
                break
            out.append((src, dst))
            if ch != '.':
                break
    return out

def gen_pony(state, src, color):
    board = state['board']
    r, c = R_OF[src], C_OF[src]
    out = []
    for dr, dc in DIAG:
        nr, nc = r + dr, c + dc
        if not in_bounds(nr, nc):
            continue
        dst = idx_of(nr, nc)
        ch = board[dst]
        if is_friend(ch, color):
            continue
        out.append((src, dst))
    return out

def gen_guard(state, src, color):
    board = state['board']
    r, c = R_OF[src], C_OF[src]
    out = []
    for dr, dc in ORTH:
        for step in (1, 2):
            nr, nc = r + dr * step, c + dc * step
            if not in_bounds(nr, nc):
                break
            dst = idx_of(nr, nc)
            ch = board[dst]
            if is_friend(ch, color):
                break
            out.append((src, dst))
            if ch != '.':
                break
    return out

def gen_tutor(state, src, color):
    board = state['board']
    r, c = R_OF[src], C_OF[src]
    out = []
    for dr, dc in DIAG:
        for step in (1, 2):
            nr, nc = r + dr * step, c + dc * step
            if not in_bounds(nr, nc):
                break
            dst = idx_of(nr, nc)
            ch = board[dst]
            if is_friend(ch, color):
                break
            out.append((src, dst))
            if ch != '.':
                break
    return out

def gen_scout(state, src, color):
    board = state['board']
    r, c = R_OF[src], C_OF[src]
    dr = -1 if color == WHITE else 1
    out = []
    for step in (1, 2, 3):
        nr = r + dr * step
        if not (0 <= nr < 12):
            break
        for side in (-1, 0, 1):
            nc = c + side
            if not in_bounds(nr, nc):
                continue
            dst = idx_of(nr, nc)
            ch = board[dst]
            if is_friend(ch, color):
                continue
            out.append((src, dst))
    return out

def gen_sibling(state, src, color):
    board = state['board']
    r, c = R_OF[src], C_OF[src]
    out = []
    for dr, dc in DIR8:
        nr, nc = r + dr, c + dc
        if not in_bounds(nr, nc):
            continue
        dst = idx_of(nr, nc)
        ch = board[dst]
        if is_friend(ch, color):
            continue

        ok = False
        for adr, adc in DIR8:
            ar, ac = nr + adr, nc + adc
            if not in_bounds(ar, ac):
                continue
            adj = idx_of(ar, ac)
            if adj == src:
                continue
            if is_friend(board[adj], color):
                ok = True
                break
        if ok:
            out.append((src, dst))
    return out

def generate_moves(state, color, captures_only=False):
    board = state['board']
    pieces = state['white_pieces'] if color == WHITE else state['black_pieces']
    out = []

    for src in pieces:
        ch = board[src]
        if ch in ('B', 'b'):
            mv = gen_baby(state, src, color)
        elif ch in ('P', 'p'):
            mv = gen_prince(state, src, color)
        elif ch in ('X', 'x'):
            mv = gen_princess(state, src, color)
        elif ch in ('Y', 'y'):
            mv = gen_pony(state, src, color)
        elif ch in ('G', 'g'):
            mv = gen_guard(state, src, color)
        elif ch in ('T', 't'):
            mv = gen_tutor(state, src, color)
        elif ch in ('S', 's'):
            mv = gen_scout(state, src, color)
        elif ch in ('N', 'n'):
            mv = gen_sibling(state, src, color)
        else:
            mv = []

        if captures_only:
            for s, d in mv:
                if board[d] != '.':
                    out.append((s, d))
        else:
            out.extend(mv)

    def move_key(mv):
        s, d = mv
        attacker = board[s]
        victim = board[d]
        return (
            0 if victim != '.' else 1,
            -(MAT.get(victim, 0) if victim != '.' else 0),
            MAT.get(attacker, 0),
            s,
            d
        )

    out.sort(key=move_key)
    return out

def piece_square_bonus(ch, idx):
    r, c = R_OF[idx], C_OF[idx]
    center = 6.0 - (abs(r - 5.5) + abs(c - 5.5))

    if ch in ('B', 'b'):
        adv = (11 - r) if ch.isupper() else r
        return int(8 * adv + 2 * center)
    if ch in ('S', 's'):
        adv = (11 - r) if ch.isupper() else r
        return int(4 * adv + 2 * center)
    if ch in ('P', 'p'):
        return int(5 * center)
    if ch in ('X', 'x', 'G', 'g', 'T', 't', 'Y', 'y', 'N', 'n'):
        return int(2 * center)
    return int(1 * center)

def attackers_on_square(state, target, attacking_color):
    pieces = state['white_pieces'] if attacking_color == WHITE else state['black_pieces']
    count = 0
    for src in pieces:
        if piece_attacks_square(state, src, attacking_color, target):
            count += 1
    return count

def piece_attacks_square(state, src, color, target):
    board = state['board']
    ch = board[src]
    sr, sc = R_OF[src], C_OF[src]
    tr, tc = R_OF[target], C_OF[target]
    dr = tr - sr
    dc = tc - sc

    if ch in ('P', 'p'):
        return max(abs(dr), abs(dc)) == 1

    if ch in ('Y', 'y'):
        return abs(dr) == 1 and abs(dc) == 1

    if ch in ('B', 'b'):
        if sc != tc:
            return False
        forward = -1 if color == WHITE else 1
        return dr in (forward, 2 * forward)

    if ch in ('S', 's'):
        forward = -1 if color == WHITE else 1
        return dr in (forward, 2 * forward, 3 * forward) and dc in (-1, 0, 1)

    if ch in ('G', 'g'):
        if dr != 0 and dc != 0:
            return False
        dist = abs(dr) + abs(dc)
        if dist == 0 or dist > 2:
            return False
        step_r = 0 if dr == 0 else (1 if dr > 0 else -1)
        step_c = 0 if dc == 0 else (1 if dc > 0 else -1)
        for step in range(1, dist):
            mid = idx_of(sr + step_r * step, sc + step_c * step)
            if board[mid] != '.':
                return False
        return True

    if ch in ('T', 't'):
        if abs(dr) != abs(dc):
            return False
        dist = abs(dr)
        if dist == 0 or dist > 2:
            return False
        step_r = 1 if dr > 0 else -1
        step_c = 1 if dc > 0 else -1
        for step in range(1, dist):
            mid = idx_of(sr + step_r * step, sc + step_c * step)
            if board[mid] != '.':
                return False
        return True

    if ch in ('X', 'x'):
        if max(abs(dr), abs(dc)) > 3 or (dr == 0 and dc == 0):
            return False
        if not (dr == 0 or dc == 0 or abs(dr) == abs(dc)):
            return False
        step_r = 0 if dr == 0 else (1 if dr > 0 else -1)
        step_c = 0 if dc == 0 else (1 if dc > 0 else -1)
        dist = max(abs(dr), abs(dc))
        for step in range(1, dist):
            mid = idx_of(sr + step_r * step, sc + step_c * step)
            if board[mid] != '.':
                return False
        return True

    if ch in ('N', 'n'):
        if max(abs(dr), abs(dc)) != 1 or (dr == 0 and dc == 0):
            return False
        for adr, adc in DIR8:
            ar, ac = tr + adr, tc + adc
            if not in_bounds(ar, ac):
                continue
            adj = idx_of(ar, ac)
            if adj == src:
                continue
            if is_friend(board[adj], color):
                return True
        return False

    return False

def eval_white(state):
    board = state['board']
    score = 0

    for idx in state['white_pieces']:
        ch = board[idx]
        score += MAT.get(ch, 0)
        score += piece_square_bonus(ch, idx)

    for idx in state['black_pieces']:
        ch = board[idx]
        score -= MAT.get(ch, 0)
        score -= piece_square_bonus(ch, idx)

    if state['white_prince_idx'] is not None:
        score += 60
        score += 25 * len([
            1 for d in DIR8
            if in_bounds(R_OF[state['white_prince_idx']] + d[0], C_OF[state['white_prince_idx']] + d[1])
        ])
        score -= 180 * attackers_on_square(state, state['white_prince_idx'], BLACK)

    if state['black_prince_idx'] is not None:
        score -= 60
        score -= 180 * attackers_on_square(state, state['black_prince_idx'], WHITE)

    return score

def classify_position(state, color):
    moves = generate_moves(state, color)
    if not moves:
        return "quiet", moves

    board = state['board']
    enemy_prince = state['black_prince_idx'] if color == WHITE else state['white_prince_idx']
    has_capture = False
    has_baby = False
    threat = False

    for src, dst in moves:
        if board[dst] != '.':
            has_capture = True
        if board[src] in ('B', 'b'):
            has_baby = True
        if enemy_prince is not None and piece_attacks_square(state, src, color, enemy_prince):
            threat = True

    if has_capture or threat:
        return "tactical", moves
    if has_baby:
        return "baby", moves
    return "quiet", moves

class Searcher:
    def __init__(self, state, color, time_left):
        self.state = state
        self.color = color
        self.time_left = float(time_left)
        self.start_cpu = time.process_time()
        self.tt = {}
        self.killers = [[None, None] for _ in range(16)]
        self.history = {}
        self.best_move = None

    def time_used(self):
        return time.process_time() - self.start_cpu

    def time_up(self):
        return self.time_used() >= max(0.0, self.time_left - TIME_BUFFER)

    def eval_side(self, to_move):
        ew = eval_white(self.state)
        return ew if to_move == WHITE else -ew

    def terminal_score(self, to_move):
        if self.state['white_prince_idx'] is None:
            return -INF if to_move == WHITE else INF
        if self.state['black_prince_idx'] is None:
            return INF if to_move == WHITE else -INF
        return None

    def move_score(self, mv, to_move, phase, depth=0, preferred=None):
        src, dst = mv
        board = self.state['board']
        attacker = board[src]
        victim = board[dst]

        score = 0

        if preferred is not None and mv == preferred:
            score += 10_000_000

        if victim != '.':
            score += 1_000_000 + 20 * MAT.get(victim, 0) - MAT.get(attacker, 0)
            if victim in ('P', 'p'):
                score += 5_000_000

        if depth < len(self.killers):
            k1, k2 = self.killers[depth]
            if mv == k1:
                score += 700_000
            elif mv == k2:
                score += 650_000

        score += self.history.get((to_move, src, dst), 0)

        if attacker in ('B', 'b'):
            score += 20_000
            if phase == "baby":
                score += 15_000
        elif attacker in ('S', 's'):
            score += 8_000
        elif attacker in ('P', 'p'):
            score += 5_000
        else:
            score += 1_000

        if attacker.isupper():
            score += (11 - R_OF[dst]) * 18
        else:
            score += R_OF[dst] * 18

        score -= abs(C_OF[dst] - 5) * 3
        return score

    def order_moves(self, moves, to_move, phase, depth=0, preferred=None):
        moves.sort(key=lambda mv: self.move_score(mv, to_move, phase, depth=depth, preferred=preferred), reverse=True)

    def qsearch(self, alpha, beta, to_move):
        stand = self.eval_side(to_move)
        if stand >= beta:
            return beta
        if stand > alpha:
            alpha = stand

        if self.time_up():
            return stand

        moves = generate_moves(self.state, to_move, captures_only=True)
        if not moves:
            return stand

        self.order_moves(moves, to_move, "tactical")
        nxt = other(to_move)

        for src, dst in moves:
            if self.time_up():
                break
            captured, mover_pos, moved, wpk, bpk = make_move(self.state, src, dst)
            score = -self.qsearch(-beta, -alpha, nxt)
            undo_move(self.state, src, dst, captured, mover_pos, moved, wpk, bpk)
            if score >= beta:
                return beta
            if score > alpha:
                alpha = score
        return alpha

    def negamax(self, depth, alpha, beta, to_move, phase):
        if self.time_up():
            return self.eval_side(to_move)

        term = self.terminal_score(to_move)
        if term is not None:
            return term

        if depth == 0:
            return self.qsearch(alpha, beta, to_move)

        key = (''.join(self.state['board']), to_move, depth)
        entry = self.tt.get(key)
        preferred = None
        if entry is not None:
            _, preferred = entry

        moves = generate_moves(self.state, to_move)
        if not moves:
            return self.eval_side(to_move)

        self.order_moves(moves, to_move, phase, depth=depth, preferred=preferred)

        best = -INF
        best_move = None
        nxt = other(to_move)

        for src, dst in moves:
            if self.time_up():
                break
            captured, mover_pos, moved, wpk, bpk = make_move(self.state, src, dst)
            score = -self.negamax(depth - 1, -beta, -alpha, nxt, phase)
            undo_move(self.state, src, dst, captured, mover_pos, moved, wpk, bpk)

            if score > best:
                best = score
                best_move = (src, dst)
            if score > alpha:
                alpha = score
            if alpha >= beta:
                if depth < len(self.killers):
                    if self.killers[depth][0] != (src, dst):
                        self.killers[depth][1] = self.killers[depth][0]
                        self.killers[depth][0] = (src, dst)
                self.history[(to_move, src, dst)] = self.history.get((to_move, src, dst), 0) + depth * depth
                break

        if best_move is not None and not self.time_up():
            self.tt[key] = (best, best_move)

        return best

    def opening_move(self, legal):
        if self.color != WHITE:
            return None
        if not is_start_position(self.state):
            return None

        preferred_coords = [
            ("f2", "f3"),
            ("g2", "g3"),
            ("e2", "e3"),
            ("h2", "h3"),
            ("d2", "d3"),
            ("j2", "j3"),
        ]

        legal_set = {(src, dst) for src, dst in legal}
        for a, b in preferred_coords:
            src = coord_to_idx(a)
            dst = coord_to_idx(b)
            if (src, dst) in legal_set:
                return (src, dst)
        return None

    def root_priority(self, mv, phase):
        src, dst = mv
        board = self.state['board']
        attacker = board[src]
        victim = board[dst]

        captured, mover_pos, moved, wpk, bpk = make_move(self.state, src, dst)

        enemy_prince = self.state['black_prince_idx'] if self.color == WHITE else self.state['white_prince_idx']
        own_prince = self.state['white_prince_idx'] if self.color == WHITE else self.state['black_prince_idx']

        score = 0

        if enemy_prince is None:
            score += 10_000_000
        else:
            enemy_attackers = attackers_on_square(self.state, enemy_prince, self.color)
            score += 80_000 * enemy_attackers
            if enemy_attackers >= 2:
                score += 150_000

        if own_prince is not None:
            own_attackers = attackers_on_square(self.state, own_prince, other(self.color))
            score -= 120_000 * own_attackers

        if victim != '.':
            score += 1_000_000 + 20 * MAT.get(victim, 0) - MAT.get(attacker, 0)
            if victim in ('P', 'p'):
                score += 8_000_000

        if attacker in ('B', 'b'):
            score += 25_000
            if phase == "baby":
                score += 15_000
        elif attacker in ('S', 's'):
            score += 8_000
        elif attacker in ('P', 'p'):
            score += 5_000
        else:
            score += 2_000

        if attacker.isupper():
            score += (11 - R_OF[dst]) * 18
        else:
            score += R_OF[dst] * 18
        score -= abs(C_OF[dst] - 5) * 3

        if own_prince is not None:
            score += 20 * adjacent_friends(self.state, own_prince, self.color)

        undo_move(self.state, src, dst, captured, mover_pos, moved, wpk, bpk)
        return score

    def choose(self):
        phase, legal = classify_position(self.state, self.color)
        if not legal:
            return None

        fallback = legal[0]
        self.best_move = fallback

        book = self.opening_move(legal)
        if book is not None:
            return book

        enemy_prince = self.state['black_prince_idx'] if self.color == WHITE else self.state['white_prince_idx']
        if enemy_prince is not None:
            for src, dst in legal:
                if dst == enemy_prince and piece_attacks_square(self.state, src, self.color, enemy_prince):
                    return (src, dst)

        if self.time_left < 0.20:
            return fallback

        if phase == "tactical":
            max_depth = 5 if self.time_left > 45 else 4 if self.time_left > 18 else 3
        elif phase == "baby":
            max_depth = 4 if self.time_left > 60 else 3
        else:
            max_depth = 3 if self.time_left > 80 else 2

        max_depth = min(max_depth, MAX_DEPTH_CAP)

        try:
            root_moves = generate_moves(self.state, self.color)
            self.order_moves(root_moves, self.color, phase, depth=max_depth, preferred=self.best_move)
            root_moves.sort(key=lambda mv: self.root_priority(mv, phase), reverse=True)

            for depth in range(1, max_depth + 1):
                if self.time_up():
                    break

                alpha = -INF
                beta = INF
                best_score = -INF
                best_move = self.best_move
                nxt = other(self.color)

                for src, dst in root_moves:
                    if self.time_up():
                        break
                    captured, mover_pos, moved, wpk, bpk = make_move(self.state, src, dst)
                    score = -self.negamax(depth - 1, -beta, -alpha, nxt, phase)

                    own_prince = self.state['white_prince_idx'] if self.color == WHITE else self.state['black_prince_idx']
                    if own_prince is not None and attackers_on_square(self.state, own_prince, other(self.color)) > 0:
                        score -= 1500

                    enemy_prince = self.state['black_prince_idx'] if self.color == WHITE else self.state['white_prince_idx']
                    if enemy_prince is not None:
                        attacks = attackers_on_square(self.state, enemy_prince, self.color)
                        if attacks >= 2:
                            score += 900
                        elif attacks == 1:
                            score += 250

                    undo_move(self.state, src, dst, captured, mover_pos, moved, wpk, bpk)

                    if score > best_score:
                        best_score = score
                        best_move = (src, dst)
                    if score > alpha:
                        alpha = score

                if best_move is not None:
                    self.best_move = best_move

        except Exception as e:
            print(f"search error: {e}", file=sys.stderr)
            self.best_move = fallback

        return self.best_move if self.best_move is not None else fallback

def adjacent_friends(state, idx, color):
    board = state['board']
    r, c = R_OF[idx], C_OF[idx]
    cnt = 0
    for dr, dc in DIR8:
        nr, nc = r + dr, c + dc
        if not in_bounds(nr, nc):
            continue
        if is_friend(board[idx_of(nr, nc)], color):
            cnt += 1
    return cnt

def main():
    fallback = None
    try:
        color, my_time, opp_time, state = parse_input()
        legal = generate_moves(state, color)
        if legal:
            fallback = legal[0]

        searcher = Searcher(state, color, my_time)
        mv = searcher.choose()
        if mv is None:
            mv = fallback

        if mv is None:
            raise RuntimeError("No legal move available")

        with open("output.txt", "w") as f:
            f.write(move_text(mv[0], mv[1]) + "\n")

    except Exception as e:
        print(f"fatal error: {e}", file=sys.stderr)
        if fallback is not None:
            try:
                with open("output.txt", "w") as f:
                    f.write(move_text(fallback[0], fallback[1]) + "\n")
                return
            except Exception:
                pass
        try:
            with open("output.txt", "w") as f:
                f.write("")
        except Exception:
            pass

if __name__ == "__main__":
    main()