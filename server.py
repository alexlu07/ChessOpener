from flask import Flask, request, jsonify, render_template, send_from_directory

app = Flask(__name__)

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/move', methods=['POST'])
def handle_move():
    data = request.get_json()
    status = data['status']
    fen = data['fen']
    pgn = data['pgn']
    
    print(status)
    print(fen)
    print(pgn)

    return jsonify({
        'status': 'success',
        'message': 'Move received',
    })

@app.route('/img/chesspieces/wikipedia/<filename>')
def serve_image(filename):
    return send_from_directory(app.static_folder, 'img/chesspieces/wikipedia/' + filename)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
