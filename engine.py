import chess
import chess.engine
import kenlm

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

with open('models/vocab.txt', 'r') as file:
    vocab = file.readlines()


def suggest_top_k(model, prefix, top_k=3):
    words = prefix.strip().split()

    in_state = kenlm.State()

    # Advance state with the prefix
    for word in words:
        next_state = kenlm.State()
        model.BaseScore(in_state, word, next_state)
        in_state = next_state

    suggestions = []

    # Try every word in the vocabulary
    for word in vocab:
        if word in ("<s>", "</s>"):
            continue
        out_state = kenlm.State()
        score = model.BaseScore(in_state, word, out_state)
        suggestions.append((10**score, word))
        
    # Sort by descending score
    suggestions.sort(reverse=True)
    return suggestions[:top_k]

def continue_on_line(model, prefix, continuation):
    words = prefix.strip().split()

    in_state = kenlm.State()

    # Advance state with the prefix
    for word in words:
        next_state = kenlm.State()
        model.BaseScore(in_state, word, next_state)
        in_state = next_state
    next_state = kenlm.State()
    model.BaseScore(in_state, continuation, next_state)
    in_state = next_state

    next_moves,temp  = [continuation], []

    for i in range(7):
        for word in vocab:
            if word in ("<s>", "</s>"):
                continue
            out_state = kenlm.State()
            score = model.BaseScore(in_state, word, out_state)
            temp.append((10**score, word))
            temp.sort(reverse=True)
            next_moves.append(temp[0][1])
            model.BaseScore(in_state, temp[0][1], next_state)
            in_state = next_state
    return next_moves

def calculate_branches_lm(starting_pgn, starting_fen, elo, turn):
    model = kenlm.Model(f'models/24-7-L{elo}-Short.mmap')
    print('a')

    top3fromModel = suggest_top_k(model, starting_pgn)
    print(top3fromModel)
    result = []
    for line in top3fromModel:
        print(line[1])
        result.append(continue_on_line(model, starting_pgn, line[1]))
    print('c')

    branches = []
    for line in result:
        board.set_fen(starting_fen)
        for move in line:
            try:
                board.push(move)
            except:
                #skip the next moves for the board if there is an illegal move
                break
    
        scoringLine = engine.analyse(board, chess.engine.Limit(depth=DEPTH), multipv=1)#Analyse 1st variation
        
        score_obj = scoringLine.get("score").white()
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

        temp_board = board.copy()
        san_moves = [] if turn == 'w' else [".."]


        branches.append((score, line))