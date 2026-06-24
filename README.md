# Minimax Game Engine

A move-search AI for a custom chess-like variant, played on a 12×12 board. The script reads the current game state from `input.txt`, searches for the best move using negamax (minimax with alpha-beta pruning), and writes its chosen move to `output.txt`. Built for a turn-based engine harness where each side is invoked as a separate process per move.

## The game

- **Board:** 12×12, columns labeled `a–n` (skipping `i` and `l`), rows numbered `1–12` from the bottom (Black's back rank) to the top (White's back rank), similar to chess notation.
- **Sides:** `WHITE` (uppercase letters) vs `BLACK` (lowercase letters).
- **Pieces** (letter → name → relative material value):

  | Letter | Name | Value | Movement |
  |---|---|---|---|
  | `P`/`p` | Prince (royal piece) | 100,000 | One step in any of 8 directions |
  | `X`/`x` | Princess | 900 | Up to 3 squares, straight or diagonal, blocked by friendly pieces, stops on capture |
  | `G`/`g` | Guard | 500 | Up to 2 squares orthogonally, blocked by friendly pieces, stops on capture |
  | `T`/`t` | Tutor | 450 | Up to 2 squares diagonally, blocked by friendly pieces, stops on capture |
  | `S`/`s` | Scout | 350 | 1–3 squares forward, plus diagonal drift, can't capture forward-only |
  | `Y`/`y` | Pony | 300 | One step diagonally |
  | `N`/`n` | Sibling | 250 | One step in any of 8 directions, only to squares adjacent to another friendly piece |
  | `B`/`b` | Baby (pawn-like) | 100 | 1–2 squares straight forward, captures by moving onto an enemy in its path |

  The game ends when a side's Prince is captured — losing it is an immediate loss for that side.

- The starting position is hardcoded in `START_ROWS` and used to detect opening play.

## How it works

### I/O contract
- **Input** (`input.txt`):
  - Line 1: `WHITE` or `BLACK` — which color the engine is playing
  - Line 2: `<my_time> <opponent_time>` — remaining time budgets (seconds)
  - Lines 3–14: the 12 board rows, top to bottom, using the piece letters above and `.` for empty squares
- **Output** (`output.txt`): a single line with the chosen move in `<from> <to>` coordinate notation, e.g. `f2 f3`

### Move generation
Each piece type has its own generator (`gen_baby`, `gen_prince`, `gen_princess`, `gen_pony`, `gen_guard`, `gen_tutor`, `gen_scout`, `gen_sibling`) implementing its specific movement rules, dispatched from `generate_moves`. Moves are pre-sorted to put captures of higher-value pieces first, which seeds move ordering before the search even starts.

### Search (`Searcher` class)
- **Negamax with alpha-beta pruning** (`negamax`), with:
  - **Iterative deepening** — searches depth 1, 2, 3... up to a time-budget-based cap, keeping the best move found at each completed depth
  - **Transposition table** (`self.tt`) keyed by board string + side to move + depth, to reuse prior search results
  - **Killer moves** and **history heuristic** to improve move ordering on later searches
  - **Quiescence search** (`qsearch`) at the search horizon, extending capture sequences to avoid misjudging tactical positions
- **Time management** — a process-time clock (`time_used`/`time_up`) with a small safety buffer (`TIME_BUFFER`); falls back to the first legal move if time runs out or an error occurs
- **Position classification** (`classify_position`) — labels the position as `"tactical"` (captures or threats available), `"baby"` (pawn-type moves available), or `"quiet"`, which adjusts the search depth and root move ordering
- **Opening book** — a short hardcoded list of preferred first moves for White, used only from the exact starting position
- **Evaluation** (`eval_white`) — material count (`MAT`) plus positional bonuses (`piece_square_bonus`, e.g. rewarding advanced pawns and central pieces) plus king-safety-style terms for both Princes (bonus for mobility, penalty for being attacked)
- **Root move scoring** (`root_priority`) — an additional heuristic layer applied only to root-level moves, weighting threats to the enemy Prince, defense of the own Prince, captures, and piece-specific incentives, used both to order moves before search and as a tiebreaker

### Entry point (`main`)
Parses `input.txt`, runs the search via `Searcher.choose()`, and writes the resulting move to `output.txt`. Wrapped in broad exception handling so that a crash still produces a legal fallback move rather than no output at all.

## Usage

```bash
python3 Minimax_game.py
```

Expects `input.txt` in the working directory in the format described above; produces `output.txt` with the chosen move. Designed to be invoked once per move by a surrounding game-playing harness/referee, not run interactively.

## Requirements

Pure Python standard library only (`sys`, `time`) — no external dependencies.

## Notes

- `MAX_DEPTH_CAP` hard-limits search depth to 5 regardless of how much time is available.
- Search depth scales with both remaining time and position type (tactical positions get deeper search than quiet ones).
- If time remaining drops below 0.20 seconds, the engine skips search entirely and plays the first legal move.
