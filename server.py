from flask import Flask, request, jsonify, render_template, send_from_directory
from stockfish import Stockfish
import chess

NUM_BRANCHES = 3
BRANCH_DEPTH = 7

stockfish = Stockfish()
board = chess.Board()

app = Flask(__name__)

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/move', methods=['POST'])
def handle_move():
    data = request.get_json()
    turn = data['turn']
    fen = data['fen']
    pgn = data['pgn']
    elo = data['elo']
    
    stockfish.set_fen_position(fen)
    evaluation = stockfish.get_evaluation()
    branches = [calculate_branch(fen, m["Move"], turn) for m in stockfish.get_top_moves(NUM_BRANCHES)]

    return jsonify({
        'stockfish': branches,
        'evaluation': evaluation,
    })

@app.route('/img/chesspieces/wikipedia/<filename>')
def serve_image(filename):
    return send_from_directory(app.static_folder, 'img/chesspieces/wikipedia/' + filename)


def calculate_branch(starting_fen, first_move, turn):
    next_moves = [] if turn == 'w' else ["..."]

    stockfish.set_fen_position(starting_fen)
    board.set_fen(starting_fen)

    next_moves.append(board.san(chess.Move.from_uci(first_move)))

    stockfish.make_moves_from_current_position([first_move])
    board.push(chess.Move.from_uci(first_move))

    
    for i in range(2 * BRANCH_DEPTH - (turn == 'b') - 1):
        move = stockfish.get_best_move()
        if move is None: break
        next_moves.append(board.san(chess.Move.from_uci(move)))

        stockfish.make_moves_from_current_position([move])
        board.push(chess.Move.from_uci(move))


    return (stockfish.get_evaluation(), next_moves)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
