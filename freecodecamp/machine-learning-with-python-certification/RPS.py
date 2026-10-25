"""Adaptive Rock Paper Scissors player, using only observed moves."""

from collections import deque


_BEATS = {"R": "P", "P": "S", "S": "R"}
_MOVES = "RPS"


def player(prev_play, _state={}):
    """Predict the opponent with an ensemble, then counter its next move.

    An empty previous move starts a new match. Each predictor is scored
    against the opponent's actual moves over a rolling 60-round window.
    No opponent functions or game internals are accessed.
    """
    if not prev_play or not _state:
        _state.clear()
        _state.update(
            own=[],
            opponent=[],
            transitions={a + b: 0 for a in _MOVES for b in _MOVES},
            scores=[deque(maxlen=60) for _ in range(5)],
            pending=[],
            responses=deque(maxlen=120),
        )

    own = _state["own"]
    opponent = _state["opponent"]

    if prev_play in _MOVES and prev_play:
        for score, prediction in zip(_state["scores"], _state["pending"]):
            score.append(int(prediction == prev_play))
        # The observed move responded to our move from two calls ago.
        context = own[-2] if len(own) > 1 else "R"
        _state["responses"].append((context, prev_play))
        opponent.append(prev_play)

    # Model 1: a repeating five-move opponent; infer its phase from history.
    cycle = ("R", "P", "P", "S", "R")
    periodic = opponent[-5] if len(opponent) >= 5 else cycle[len(opponent) % 5]

    # Model 2: an opponent that counters our most recent move.
    previous = own[-1] if own else "R"
    reactive = _BEATS[previous]

    # Model 3: an opponent that counters our most frequent recent move.
    recent = ([""] + own)[-10:]
    frequent = max(set(recent), key=recent.count)
    frequency = _BEATS[frequent or "S"]

    # Model 4: an opponent that predicts our next move from transitions.
    counts = _state["transitions"]
    if own:
        before = own[-2] if len(own) > 1 else "R"
        counts[before + own[-1]] += 1
    predicted_own = max(_MOVES, key=lambda move: counts[previous + move])
    transition = _BEATS[predicted_own]

    # Model 5: learn the observed response to each of our previous moves.
    responses = [move for context, move in _state["responses"]
                 if context == previous]
    learned = max(_MOVES, key=responses.count) if responses else "R"

    predictions = [periodic, reactive, frequency, transition, learned]
    best = max(range(len(predictions)),
               key=lambda index: sum(_state["scores"][index]))
    move = _BEATS[predictions[best]]
    _state["pending"] = predictions
    own.append(move)
    return move
