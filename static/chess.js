// NOTE: this example uses the chess.js library:
// https://github.com/jhlywa/chess.js

var board = null
var game = new Chess()
var elo = 1;

var ready = true;
var turn = 'w';
var move_count = -1;
var fen = game.fen()
var pgn = game.pgn()


function onDragStart (source, piece, position, orientation) {
  // do not pick up pieces if the game is over
  if (game.game_over()) return false

  // only pick up pieces for the side to move
  if ((game.turn() === 'w' && piece.search(/^b/) !== -1) ||
      (game.turn() === 'b' && piece.search(/^w/) !== -1)) {
    return false
  }

  if (!ready) return false
}

function onDrop (source, target) {
  // see if the move is legal
  var move = game.move({
    from: source,
    to: target,
    promotion: 'q' // NOTE: always promote to a queen for example simplicity
  })

  // illegal move
  if (move === null) return 'snapback'

  updateStatus()
}

// update the board position after the piece snap
// for castling, en passant, pawn promotion
function onSnapEnd () {
  board.position(game.fen())
}

function updateStatus () {
  var status = ''

  var moveColor = 'White'
  if (game.turn() === 'b') {
    moveColor = 'Black'
  }

  // checkmate?
  if (game.in_checkmate()) {
    status = 'Game over, ' + moveColor + ' is in checkmate.'
  }

  // draw?
  else if (game.in_draw()) {
    status = 'Game over, drawn position'
  }

  // game still on
  else {
    status = moveColor + ' to move'

    // check?
    if (game.in_check()) {
      status += ', ' + moveColor + ' is in check'
    }
  }

  turn = game.turn();
  move_count++;
  fen = game.fen();
  pgn = game.pgn();

  ready = false;

  fetch('http://127.0.0.1:5000/move', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({ turn, fen, pgn, elo }),
  })
  .then(response => response.json())
  .then(data => update(data))
  .catch(error => console.error('Error:', error));

}

function update(data) {
  console.log(data);

  // evaluation bar
  if (data.evaluation.type == "cp") {
    document.getElementById("progress").style.height = "" + Math.min(100, Math.max(0, (1000 - data.evaluation.value) / 20)) + "%";
    document.getElementById("score").getElementsByTagName("div")[0].innerHTML = data.evaluation.value / 100;
  } else if (data.evaluation.type == "mate") {
    if (data.evaluation.value != 0) {
      document.getElementById("progress").style.height = (data.evaluation.value < 0) * 100 + "%";
    }
    document.getElementById("score").getElementsByTagName("div")[0].innerHTML = "#" + data.evaluation.value;
  }

  // engine
  var display = "";
  for (var i = 0; i < data.stockfish.length; i++) {
    display += "<div class='branch'>"

    display += "<span class='eval'>"
    if (data.stockfish[i][0].type == "cp") display += (data.stockfish[i][0].value/100);
    else if (data.stockfish[i][0].type == "mate") display += "#" + data.stockfish[i][0].value;;
    display += "</span>"

    display += "<span class='moves'>"

    for (var j = 0; j < data.stockfish[i][1].length; j++) {
      if (j % 2 == 0) display += (Math.floor((j + move_count) / 2) + 1) + ". ";
      display += data.stockfish[i][1][j] + " ";
    }
    display += "</span>"

    display += "</div>"
  }
  document.getElementById("stockfish").innerHTML = display;

  ready = true;
}




var config = {
  draggable: true,
  position: 'start',
  onDragStart: onDragStart,
  onDrop: onDrop,
  onSnapEnd: onSnapEnd
}
board = Chessboard('myBoard', config)

updateStatus()

document.getElementById("elo-dropdown").onchange = function() {elo = document.getElementById("elo-dropdown").value;};
