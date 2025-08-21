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

var redoStack = [];
var lock = false;

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
  redoStack = []; // clear redo stack after a new move
}

function renderHistory() {
  const historyDiv = document.getElementById("history");
  const history = game.history({ verbose: true });
  let html = "";
  let moveNumber = 1;
  for (let i = 0; i < history.length; i++) {
    if (i % 2 === 0) html += `<span>${moveNumber++}. </span>`;
    html += `<span class="history-move" data-move-index="${i}">${history[i].san}</span> `;
  }
  historyDiv.innerHTML = html;

  // Add click listeners to each move
  document.querySelectorAll('.history-move').forEach(function(elem) {
    elem.onclick = function() {
      if (lock) return;
      lock = true;
      const idx = parseInt(this.getAttribute('data-move-index'));
      // Undo moves until we reach the desired move
      let movesToUndo = game.history().length - (idx + 1);
      for (let j = 0; j < movesToUndo; j++) {
        const undone = game.undo();
        if (undone) {
          redoStack.push(undone.san);
        }
      }
      board.position(game.fen());
      updateStatus();
    };
  });
}

function undoMove() {
  if (lock) return; // Prevent multiple undo clicks
  lock = true;
  const move = game.undo();
  if (move) {
    redoStack.push(move.san);
    board.position(game.fen());
    move_count = move_count - 2;
    updateStatus();
  } else {
    console.log("No moves to undo");
    lock = false;
  }
}

function redoMove() {
  if (lock) return; // Prevent multiple redo clicks
  lock = true;
  if (redoStack.length > 0) {
    var move = redoStack.pop();
    game.move(move);
    board.position(game.fen());
    updateStatus();
  } else {
    console.log("No moves to redo");
    lock = false;
  }
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

  // Helper to render moves as clickable spans
  function renderMoves(line, branchType, branchIdx) {
    let html = "";
    for (let j = 0; j < line.length; j++) {
      if (j % 2 == 0) html += (Math.floor((j + move_count) / 2) + 1) + ". ";
      html += `<span class="move-clickable" data-branch="${branchType}" data-branch-idx="${branchIdx}" data-move-idx="${j}">${line[j]}</span> `;
    }
    return html;
  }

  // engine
  let display = "";
  for (let i = 0; i < data.stockfish.length; i++) {
    display += "<div class='branch'>"
    display += "<span class='eval " + ((data.stockfish[i][0].value > 0) ? "white" : "black") + "'>"
    if (data.stockfish[i][0].type == "cp") display += ((data.stockfish[i][0].value > 0) ? "+" : "") + (data.stockfish[i][0].value/100);
    else if (data.stockfish[i][0].type == "mate") display += "#" + data.stockfish[i][0].value;
    display += "</span>"
    display += "<span class='moves'>" + renderMoves(data.stockfish[i][1], "stockfish", i) + "</span>"
    display += "</div>"
  }
  document.getElementById("stockfish").innerHTML = display;

  // model
  display = "";
  for (let i = 0; i < data.model.length; i++) {
    display += "<div class='branch'>"
    display += "<span class='eval " + ((data.model[i][0].value > 0) ? "white" : "black") + "'>"
    if (data.model[i][0].type == "cp") display += ((data.model[i][0].value > 0) ? "+" : "") + (data.model[i][0].value/100);
    else if (data.model[i][0].type == "mate") display += "#" + data.model[i][0].value;
    display += "</span>"
    display += "<span class='moves'>" + renderMoves(data.model[i][1], "model", i) + "</span>"
    display += "</div>"
  }
  document.getElementById("model").innerHTML = display;

  ready = true;

  // Add click event listeners to all move spans
  document.querySelectorAll('.move-clickable').forEach(function(elem) {
    elem.onclick = function() {
      if (lock) return; // Prevent multiple clicks
      lock = true; // Lock to prevent further clicks until the move is processed
      let branchType = this.getAttribute('data-branch');
      let branchIdx = parseInt(this.getAttribute('data-branch-idx'));
      let moveIdx = parseInt(this.getAttribute('data-move-idx'));
      let line = (branchType === "stockfish" ? data.stockfish : data.model)[branchIdx][1];

      // If ".." is present as the first move, skip it (for black to move lines)
      let startIdx = (line[0] === "..") ? 1 : 0;
      for (let k = startIdx; k <= moveIdx; k++) {
        try {
          game.move(line[k]);
        } catch (e) {
          // Ignore illegal moves (shouldn't happen)
        }
      }
      board.position(game.fen());
      updateStatus();
    }
  });

  renderHistory();

  lock = false;
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
document.getElementById("undo-btn").onclick = undoMove;
document.getElementById("redo-btn").onclick = redoMove;