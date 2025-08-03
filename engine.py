import chess
import chess.engine

DEPTH = 20
BRANCHES = 3

engine = chess.engine.SimpleEngine.popen_uci("stockfish/stockfish-windows-x86-64-avx2.exe")  # Ensure "stockfish" is in your PATH
engine.configure({"Threads": 4, "Hash": 2048})

board = chess.Board()

def calculate_branches(starting_fen, turn):
    board.set_fen(starting_fen)
    
    result = engine.analyse(
        board,
        chess.engine.Limit(depth=DEPTH),
        multipv=BRANCHES  # Retrieve 3 principal variations
    )

    branches = []
    for line in result:
        score_obj = line.get("score").white()
        if score_obj.score():
            score = {
                'type': 'cp',
                'value': score_obj.score()
            }
        else:
            score = {
                'type': 'mate',
                'value': score_obj.mate()
            }

        pv = line.get("pv", [])
        temp_board = board.copy()
        san_moves = [] if turn == 'w' else [".."]

        for move in pv:
            san_moves.append(temp_board.san(move))
            temp_board.push(move)

        branches.append((score, san_moves))
    
    return branches