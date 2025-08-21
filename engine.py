import chess
import chess.engine
import kenlm

DEPTH = 20
BRANCHES = 3

engine = chess.engine.SimpleEngine.popen_uci("stockfish/stockfish-ubuntu-x86-64-avx2")  # Ensure "stockfish" is in your PATH
engine.configure({"Threads": 4, "Hash": 2048})

board = chess.Board()

with open('models/vocab.txt', 'r') as file:
    vocab = set(i.strip() for i in file.readlines())

models = {i: kenlm.Model(f'models/24-7-L{i}-Short.mmap') if i == 7 else None for i in range(1, 8)}

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


def suggest_top_k(model, starting_fen, prefix, top_k=3):
    board.set_fen(starting_fen)

    words = ['<s>'] + prefix.strip().split()

    in_state = kenlm.State()

    # Advance state with the prefix
    for word in words:
        next_state = kenlm.State()
        model.BaseScore(in_state, word, next_state)
        in_state = next_state

    suggestions = []

    # Try every word in the vocabulary
    for move in board.legal_moves:
        word = board.san(move)
        if not word in vocab:
            continue
    # for word in vocab:
    #     try:
    #         board.push_san(word)
    #         board.pop()
    #     except:
    #         continue
        score = model.BaseScore(in_state, word, kenlm.State())
        suggestions.append((10**score, word))
        
    # Sort by descending score
    suggestions.sort(reverse=True)

    return in_state, suggestions[:top_k]

def continue_on_line(model, starting_fen, in_state, continuation):
    board.set_fen(starting_fen)

    next_state = kenlm.State()
    model.BaseScore(in_state, continuation, next_state)
    in_state = next_state
    
    board.push_san(continuation)

    next_moves = [continuation]

    for i in range(10):
        best = (float("-inf"), "", None)

        for move in board.legal_moves:
            word = board.san(move)
            if not word in vocab:
                continue
        # for word in vocab:
        #     try:
        #         board.push_san(word)
        #         board.pop()
        #     except:
        #         continue
            out_state = kenlm.State()
            score = model.BaseScore(in_state, word, out_state)
            if score > best[0]:
                best = (score, word, out_state)

        next_moves.append(best[1])
        board.push_san(best[1])
        in_state = best[2]

    return next_moves

def calculate_branches_lm(starting_pgn, starting_fen, elo, turn):
    model = models[elo]

    in_state, top3fromModel = suggest_top_k(model, starting_fen, starting_pgn)
    print(top3fromModel)

    result = []
    for score, continuation in top3fromModel:
        result.append(continue_on_line(model, starting_fen, in_state, continuation))

    branches = []
    for line in result:
        print(line)
        board.set_fen(starting_fen)
        board.push_san(line[0])
    
        scoringLine = engine.analyse(board, chess.engine.Limit(depth=DEPTH))
            
        score_obj = scoringLine['score'].white()
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

        # Format moves properly based on turn
        formatted_moves = [] if turn == 'w' else [".."]
        formatted_moves.extend(line)

        branches.append((score, formatted_moves))
    
    return branches
