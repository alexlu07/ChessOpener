from flask import Flask, request, jsonify, render_template, send_from_directory
from engine import calculate_branches, calculate_branches_lm

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
    
    branches = calculate_branches(fen, turn) 
    evaluation = branches[0][0]
    branches_model = calculate_branches_lm(pgn, fen, elo, turn)

    return jsonify({
        'stockfish': branches,
        'model': branches_model, #same branches format
        'evaluation': evaluation,
    })

@app.route('/img/chesspieces/wikipedia/<filename>')
def serve_image(filename):
    return send_from_directory(app.static_folder, 'img/chesspieces/wikipedia/' + filename)

if __name__ == '__main__':
    app.run(debug=True, port=5000)