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
    elo = 1#data['elo']
    
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

#Implement next in new file
"""def suggest_next_words(model, prefix, top_k=3):
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

def calculate_branch_lm(elo, pgn):
    model = kenlm.Model(f'models/24-7-L{elo}-Short.mmap')
    firstMoveTop3 = suggest_next_words(model=model, prefix=pgn)
    returnArr = []
    for move in firstMoveTop3:
        returnArr.append(suggest_next_words(model=model, prefix=pgn, top_k=7))
    return returnArr"""
